import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

SOURCE_URL = "https://www.eduscho.at/c/jede-woche-neue-inspirationen"
OUTPUT_FILE = "feed_eduscho.xml"

SKIP = {"Neu", "Nur Online", "endet bald", "Alle Artikel stark reduziert", "Exklusiv vorab kaufen!"}

def fetch_articles():
    response = requests.get(SOURCE_URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    articles = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/themeworlds/" not in href or href in seen:
            continue

        link_text = a.get_text(strip=True)
        if not link_text:
            continue

        seen.add(href)
        full_url = "https://www.eduscho.at" + href if href.startswith("/") else href
        subtitle = link_text

        title = ""
        prev_sib = a.previous_sibling
        while prev_sib:
            if hasattr(prev_sib, 'get_text'):
                text = prev_sib.get_text(strip=True)
            else:
                text = str(prev_sib).strip()
            if text and text not in SKIP:
                title = text
                break
            prev_sib = prev_sib.previous_sibling

        full_title = f"{title} – {subtitle}" if title else subtitle
        articles.append((full_title, full_url))

    print(f"Found {len(articles)} articles")
    return articles

def build_feed(articles):
    rss = ET.Element("rss")
    rss.set("version", "2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Eduscho Themenwelten"
    ET.SubElement(channel, "link").text = SOURCE_URL
    ET.SubElement(channel, "description").text = "Jede Woche neue Inspirationen von Eduscho/Tchibo"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    for title, link in articles:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid").text = link

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    tree.write(OUTPUT_FILE, encoding="unicode", xml_declaration=True)
    print(f"Feed written with {len(articles)} articles.")

if __name__ == "__main__":
    articles = fetch_articles()
    build_feed(articles)
