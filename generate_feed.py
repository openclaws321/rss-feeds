import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os

SOURCE_URL = "https://www.derstandard.at/immobilien/bauenwohnen/wohngespraech"
OUTPUT_FILE = "feed.xml"

def fetch_articles():
    cookie_str = os.environ.get("DS_COOKIES", "")
    cookies = {}
    for item in cookie_str.split("; "):
        if "=" in item:
            k, v = item.split("=", 1)
            v = v.encode("latin-1", errors="ignore").decode("latin-1")
            cookies[k.strip()] = v

    response = requests.get(SOURCE_URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }, cookies=cookies)
    response.raise_for_status()

    print("=== RESPONSE URL ===", response.url)
    print("=== HTML PREVIEW ===")
    print(response.text[:2000])

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/story/"):
            full_url = "https://www.derstandard.at" + href
            # extract title from URL slug, e.g. "/story/300000.../this-is-the-title"
            slug = href.split("/")[-1]
            title = slug.replace("-", " ").title()
            if full_url not in seen:
                seen.add(full_url)
                articles.append((title, full_url))
                print(f"FOUND: {title} | {full_url}")

    print(f"Total unique articles: {len(articles)}")
    return articles

def build_feed(articles):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "DerStandard Wohngespräch"
    ET.SubElement(channel, "link").text = SOURCE_URL
    ET.SubElement(channel, "description").text = "Wohngespräch articles from DerStandard"
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
