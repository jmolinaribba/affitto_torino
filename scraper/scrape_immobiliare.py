"""
Scraper de Immobiliare.it (affitto).

AVISO: Immobiliare.it (como Idealista) suele tener protección anti-bot
más agresiva que Subito. Este scraper con `requests` puede funcionar,
pero si empieza a devolver 403 / captchas, la solución es reemplazar
el fetch de este archivo por Playwright (navegador headless), que sí
corre bien dentro de GitHub Actions. Dejamos la función `fetch_html`
separada justamente para poder cambiar solo esa parte sin tocar el
resto del parseo.

Estrategia de parseo: buscamos bloques <script type="application/ld+json">
con datos estructurados (schema.org), que suelen incluir precio,
superficie y habitaciones de forma más estable que el HTML visual.
Si no aparecen, caemos a un parseo HTML best-effort.
"""

import json
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from common import HEADERS

BASE_URL = "https://www.immobiliare.it/affitto-case/"


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
            if "RealEstateListing" not in str(item.get("@type", "")):
                continue
            offers = item.get("offers", {}) or {}
            results.append({
                "id": item.get("url", item.get("name", "")),
                "titolo": item.get("name", "Annuncio senza titolo"),
                "url": item.get("url", ""),
                "prezzo": _to_number(offers.get("price")),
                "mq": _to_number(item.get("floorSize", {}).get("value")) if isinstance(item.get("floorSize"), dict) else None,
                "locali": _to_number(item.get("numberOfRooms")),
            })
    return results


def _fallback_html_parse(soup):
    """Parseo best-effort. Ajustar selectores si Immobiliare cambia el HTML."""
    results = []
    cards = soup.select("li[class*='nd-list__item'], div[class*='in-card'], article")
    for card in cards:
        link = card.find("a", href=True)
        if not link:
            continue
        url = link["href"]
        titolo = card.get_text(strip=True)[:80] or "Annuncio senza titolo"
        prezzo_tag = card.find(string=re.compile(r"€"))
        prezzo = _to_number(prezzo_tag) if prezzo_tag else None
        mq_tag = card.find(string=re.compile(r"\d+\s*m", re.I))
        mq = _to_number(mq_tag) if mq_tag else None
        locali_tag = card.find(string=re.compile(r"\d+\s*local", re.I))
        locali = _to_number(locali_tag) if locali_tag else None

        results.append({
            "id": url,
            "titolo": titolo,
            "url": url if url.startswith("http") else f"https://www.immobiliare.it{url}",
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
