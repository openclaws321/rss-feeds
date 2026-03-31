import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os

SOURCE_URL = "https://www.derstandard.at/immobilien/bauenwohnen/wohngespraech"
OUTPUT_FILE = "feed.xml"

def get_cookies():
    cookie_str = os.environ.get("DS_COOKIES", "")
    cookies = {}
    for item in cookie_str.split("; "):
        if "=" in item:
            k, v = item.split("=", 1)
            v = v.encode("latin-1", errors="ignore").decode("latin-1")
            cookies[k.strip()] = v
    return cookies

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
        seen.add(href)
        full_url = "https://www.eduscho.at" + href if href.startswith("/") else href

        # Title is in the next sibling <a> tag's text, or in surrounding text nodes
        # Try: the subtitle link (next <a> with same href) has the description
        # The heading text sits between the image <a> and the subtitle <a>
        title = ""
        subtitle = ""
        next_sib = a.next_sibling
        while next_sib:
            if hasattr(next_sib, 'get_text'):
                text = next_sib.get_text(strip=True)
                if text and text not in ("Neu", "Nur Online", "endet bald", "Alle Artikel stark reduziert", "Exklusiv vorab kaufen!"):
                    if not title:
                        title = text
                    elif not subtitle:
                        subtitle = text
                        break
            elif str(next_sib).strip():
                text = str(next_sib).strip()
                if text and text not in ("Neu", "Nur Online", "endet bald", "Alle Artikel stark reduziert", "Exklusiv vorab kaufen!"):
                    if not title:
                        title = text
            next_sib = next_sib.next_sibling

        if not title:
            title = href  # fallback

        full_title = f"{title} – {subtitle}" if subtitle else title
        articles.append((full_title, full_url))

    print(f"Found {len(articles)} articles")
    return articles

def fetch_content(url, cookies):
    try:
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }, cookies=cookies, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else None
        for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        body = soup.find("article") or soup.find(class_="article-body") or soup.find("main")
        html = str(body) if body else "<p>No content found.</p>"
        print(f"Fetched: {url}")
        return title, html
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None, ""

def build_feed(articles, cookies):
    rss = ET.Element("rss")
    rss.set("version", "2.0")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "DerStandard Wohngespräch"
    ET.SubElement(channel, "link").text = SOURCE_URL
    ET.SubElement(channel, "description").text = "Wohngespräch articles from DerStandard"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    for title, link in articles:
        real_title, html = fetch_content(link, cookies)
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = real_title or title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid").text = link
        ET.SubElement(item, "content:encoded").text = html
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    tree.write(OUTPUT_FILE, encoding="unicode", xml_declaration=True)
    print(f"Feed written with {len(articles)} articles.")

if __name__ == "__main__":
    cookies = get_cookies()
    articles = fetch_articles(cookies)
    build_feed(articles, cookies)
