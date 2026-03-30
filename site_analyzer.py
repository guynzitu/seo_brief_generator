"""
Analyze the target site to extract tone, style, and context
for adapting the SEO brief.
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
}


def analyze_site(url: str) -> dict:
    """
    Analyze a target website to extract context for brief adaptation.

    Returns dict with:
        - name: site name
        - tone: detected editorial tone
        - description: site description
        - sample_headings: sample H1/H2 from the site
        - domain: domain name
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        response.raise_for_status()

        if response.encoding and response.encoding.lower() != "utf-8":
            response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract site name
        name = ""
        og_site = soup.find("meta", property="og:site_name")
        if og_site:
            name = og_site.get("content", "").strip()
        elif soup.find("title"):
            # Often "Page Title - Site Name" or "Site Name | Page Title"
            title_text = soup.find("title").get_text(strip=True)
            for sep in [" | ", " - ", " — ", " – ", " : "]:
                if sep in title_text:
                    parts = title_text.split(sep)
                    name = parts[-1].strip()
                    break
            if not name:
                name = title_text

        # Extract description
        description = ""
        meta_desc = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta_desc:
            description = meta_desc.get("content", "").strip()

        # Extract domain
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        # Sample headings to detect style
        sample_headings = []
        for h in soup.find_all(re.compile(r"^h[1-3]$")):
            text = h.get_text(strip=True)
            if text and len(text) > 3:
                sample_headings.append({"level": h.name.upper(), "text": text})
            if len(sample_headings) >= 10:
                break

        # Detect tone from body text
        body = soup.find("main") or soup.find("article") or soup.find("body")
        body_text = ""
        if body:
            for tag in body(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            body_text = body.get_text(separator=" ", strip=True)[:2000]

        tone = detect_tone(body_text)

        return {
            "name": name,
            "tone": tone,
            "description": description,
            "sample_headings": sample_headings,
            "domain": domain,
            "url": url,
        }

    except Exception as e:
        return {
            "name": "",
            "tone": "professionnel",
            "description": "",
            "sample_headings": [],
            "domain": "",
            "url": url,
            "error": str(e),
        }


def detect_tone(text: str) -> str:
    """
    Simple heuristic to detect editorial tone from text sample.
    """
    if not text:
        return "professionnel"

    text_lower = text.lower()

    # Casual / informal indicators
    casual_indicators = ["tu ", " toi ", "t'", "sympa", "cool", "super",
                         "génial", "top", "!", "😊", "🎉", "👍"]
    casual_score = sum(1 for w in casual_indicators if w in text_lower)

    # Formal indicators
    formal_indicators = ["nous vous", "vous pouvez", "il convient",
                         "en effet", "par conséquent", "néanmoins",
                         "toutefois", "conformément"]
    formal_score = sum(1 for w in formal_indicators if w in text_lower)

    # Expert/technical indicators
    expert_indicators = ["méthodologie", "analyse", "stratégie",
                         "optimisation", "performance", "données"]
    expert_score = sum(1 for w in expert_indicators if w in text_lower)

    if casual_score > formal_score and casual_score > expert_score:
        return "décontracté et accessible"
    elif expert_score > formal_score:
        return "expert et technique"
    elif formal_score > 2:
        return "formel et institutionnel"
    else:
        return "professionnel"
