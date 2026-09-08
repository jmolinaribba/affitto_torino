"""
Scraper de Idealista.it (affitto).

Mismo aviso que en scrape_immobiliare.py: Idealista tiene protección
anti-bot fuerte (a veces Cloudflare / rate limiting agresivo). Si
`requests` empieza a fallar con 403, migrar `fetch_html` a Playwright.

La URL de búsqueda de Idealista tiene el formato:
  https://www.idealista.it/affitto-case/<citta>-<provincia>/
Como no siempre sabemos la provincia, probamos primero solo con la
ciudad (Idealista suele redirigir/autocompletar igual).
"""

import json
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from common import HEADERS

BASE_URL = "https://www.idealista.it/affitto-case/"


def build_search_url(citta):
    slug = quote(citta.lower().strip())
    return f"{BASE_URL}{slug}/"


def fetch_html(url):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def _to_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    match = re.search(r"[\d.]+", str(value).replace(".", "").replace(",", "."))
    try:
        return float(match.group()) if match else None
    except (ValueError, AttributeError):
        return None


def _parse_ld_json(soup):
    results = []
    for tag in soup.find_all("script", type="application/ld+json"):
        if not tag.string:
            continue
        try:
            data = json.loads(tag.string)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            if "RealEstateListing" not in str(item.get("@type", "")) and "Product" not in str(item.get("@type", "")):
                continue
            offers = item.get("offers", {}) or {}
            results.append({
                "id": item.get("url", item.get("name", "")),
                "titolo": item.get("name", "Annuncio senza titolo"),
                "url": item.get("url", ""),
                "prezzo": _to_number(offers.get("price")),
                "mq": None,
                "locali": None,
            })
    return results


def _fallback_html_parse(soup):
    """Parseo best-effort. Ajustar selectores si Idealista cambia el HTML."""
    results = []
    cards = soup.select("article[class*='item'], div[class*='item-info-container']")
    for card in cards:
        link = card.find("a", href=True)
        if not link:
            continue
        url = link["href"]
        titolo = link.get_text(strip=True) or "Annuncio senza titolo"
        prezzo_tag = card.find(string=re.compile(r"€"))
        prezzo = _to_number(prezzo_tag) if prezzo_tag else None
        mq_tag = card.find(string=re.compile(r"\d+\s*m²|\d+\s*mq", re.I))
        mq = _to_number(mq_tag) if mq_tag else None
        locali_tag = card.find(string=re.compile(r"\d+\s*local", re.I))
        locali = _to_number(locali_tag) if locali_tag else None

        results.append({
            "id": url,
            "titolo": titolo,
            "url": url if url.startswith("http") else f"https://www.idealista.it{url}",
            "prezzo": prezzo,
            "mq": mq,
            "locali": locali,
        })
    return results


def scrape(citta):
    url = build_search_url(citta)
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    ld_items = _parse_ld_json(soup)
    if ld_items:
        return ld_items

    return _fallback_html_parse(soup)


if __name__ == "__main__":
    import sys
    citta = sys.argv[1] if len(sys.argv) > 1 else "Milano"
    for r in scrape(citta):
        print(r)
