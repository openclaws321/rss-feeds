import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

SOURCE_URL = "https://www.derstandard.at/rss/immobilien"
OUTPUT_FILE = "feed.xml"
FEED_TITLE = "DerStandard Wohngespräch"
FEED_LINK = "https://www.derstandard.at"
FEED_DESC = "Filtered Wohngespräch articles from DerStandard"

def fetch_articles():
    response = requests.get(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    root = ET.fromstring(response.content)
    articles = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        desc = item.findtext("description", "")
        pubdate = item.findtext("pubDate", "")
        if "wohngesp" in link.lower() or "wohngesp" in title.lower():
            articles.append((title, link, desc, pubdate))
    return articles

def build_feed(articles):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = FEED_LINK
    ET.SubElement(channel, "description").text = FEED_DESC
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    for title, link, desc, pubdate in articles:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "description").text = desc
        ET.SubElement(item, "pubDate").text = pubdate
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    tree.write(OUTPUT_FILE, encoding="unicode", xml_declaration=True)
    print(f"Feed written with {len(articles)} articles.")

if __name__ == "__main__":
    articles = fetch_articles()
    build_feed(articles)
