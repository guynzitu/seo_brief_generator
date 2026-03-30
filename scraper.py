"""
Web scraper for competitor page analysis.
Extracts heading structure, word count, title, meta description.
"""
import requests
from bs4 import BeautifulSoup
import re


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def scrape_url(url: str, timeout: int = 15) -> dict | None:
    """
    Scrape a URL and return structured data.

    Returns dict with keys:
        - title: page <title>
        - meta_description: meta description content
        - headings: list of {level: 'h1'|'h2'|..., text: str}
        - body_text: cleaned body text
        - html: raw HTML (for further processing)
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        # Handle encoding
        if response.encoding and response.encoding.lower() != "utf-8":
            response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                         "noscript", "iframe", "form"]):
            tag.decompose()

        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Extract meta description
        meta_description = ""
        meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta_tag:
            meta_description = meta_tag.get("content", "").strip()

        # Extract headings
        headings = []
        for level in range(1, 7):
            for h in soup.find_all(f"h{level}"):
                text = h.get_text(strip=True)
                if text:
                    headings.append({"level": f"H{level}", "text": text})

        # Re-order headings by their position in the document
        all_heading_tags = soup.find_all(re.compile(r"^h[1-6]$"))
        headings_ordered = []
        for h in all_heading_tags:
            text = h.get_text(strip=True)
            if text:
                headings_ordered.append({
                    "level": f"H{h.name[1]}",
                    "text": text
                })

        # Extract body text
        body_text = ""
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", {"class": re.compile(r"content|article|post|entry", re.I)})
            or soup.find("body")
        )
        if main_content:
            body_text = main_content.get_text(separator=" ", strip=True)
        else:
            body_text = soup.get_text(separator=" ", strip=True)

        # Clean up body text
        body_text = re.sub(r"\s+", " ", body_text).strip()

        return {
            "title": title,
            "meta_description": meta_description,
            "headings": headings_ordered,
            "body_text": body_text,
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def extract_structure(page_data: dict) -> list:
    """
    Extract the heading structure from scraped page data.

    Returns list of {level, text} dicts.
    """
    if not page_data:
        return []
    return page_data.get("headings", [])


def count_words(page_data: dict) -> int:
    """Count words in the body text."""
    if not page_data:
        return 0
    text = page_data.get("body_text", "")
    words = re.findall(r"\b\w+\b", text)
    return len(words)
