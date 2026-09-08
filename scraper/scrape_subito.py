"""
Scraper de Subito.it (annunci in affitto).

Subito.it es una single-page-app basada en Next.js: además del HTML
"visible" suele incluir un bloque <script id="__NEXT_DATA__"> con los
resultados de la búsqueda en JSON, que es mucho más estable que
parsear las clases CSS de las tarjetas (esas cambian seguido).
Este scraper intenta primero esa vía, y si no la encuentra, cae a un
parseo de HTML "best effort" con BeautifulSoup.

NOTA DE MANTENIMIENTO: si esto deja de traer resultados, lo primero
es abrir la URL de búsqueda en el navegador, ver el HTML fuente
(Ctrl+U) y revisar si sigue existiendo <script id="__NEXT_DATA__">,
o ajustar los selectores de fallback más abajo.
"""

import json
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from common import HEADERS

BASE_URL = "https://www.subito.it/annunci-italia/affitto/appartamenti/"


def build_search_url(citta):
    # Subito acepta un parámetro de texto libre "q"; filtramos ciudad ahí,
    # y luego filtramos precio/mq/locali nosotros mismos sobre los resultados.
    return f"{BASE_URL}?q={quote(citta)}"


def _parse_next_data(soup):
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag or not tag.string:
        return []

    try:
        data = json.loads(tag.string)
    except json.JSONDecodeError:
        return []

    # La ruta exacta dentro del JSON puede variar; buscamos recursivamente
    # cualquier lista de objetos que "parezca" un anuncio (tenga urn/subject/price).
    results = []

    def walk(node):
        if isinstance(node, dict):
            if "subject" in node and ("urn" in node or "item_id" in node):
                results.append(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return results


def _extract_from_next_item(item):
    titolo = item.get("subject") or item.get("title")
    url = item.get("urn") or item.get("url") or item.get("item_id", "")
    if url and not url.startswith("http"):
        url = f"https://www.subito.it{url}" if url.startswith("/") else ""

    prezzo = None
    mq = None
    locali = None

    # Subito suele guardar features en una lista de {label, value} o similar.
    features = item.get("features") or []
    for f in features:
        label = (f.get("label") or f.get("key") or "").lower()
        value = f.get("value") or f.get("values")
        if "prezzo" in label or "price" in label:
            prezzo = _to_number(value)
        elif "mq" in label or "superficie" in label:
            mq = _to_number(value)
        elif "local" in label:
            locali = _to_number(value)

    if prezzo is None:
        prezzo = _to_number(item.get("price"))

    return {
        "id": str(item.get("item_id") or item.get("urn") or url),
        "titolo": titolo or "Annuncio senza titolo",
        "url": url,
        "prezzo": prezzo,
        "mq": mq,
        "locali": locali,
    }


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


def _fallback_html_parse(soup):
    """Parseo best-effort si no aparece __NEXT_DATA__. Selectores a ajustar
    inspeccionando la página real si esta función devuelve poco o nada."""
    results = []
    cards = soup.select("div[class*='item-card'], article, li[class*='items__item']")
    for card in cards:
        link = card.find("a", href=True)
        if not link:
            continue
        url = link["href"]
        titolo = link.get_text(strip=True) or "Annuncio senza titolo"
        prezzo_tag = card.find(string=re.compile(r"€"))
        prezzo = _to_number(prezzo_tag) if prezzo_tag else None
        mq_tag = card.find(string=re.compile(r"\d+\s*mq"))
        mq = _to_number(mq_tag) if mq_tag else None
        locali_tag = card.find(string=re.compile(r"\d+\s*local", re.I))
        locali = _to_number(locali_tag) if locali_tag else None

        results.append({
            "id": url,
            "titolo": titolo,
            "url": url if url.startswith("http") else f"https://www.subito.it{url}",
            "prezzo": prezzo,
            "mq": mq,
            "locali": locali,
        })
    return results


def scrape(citta):
    url = build_search_url(citta)
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    next_items = _parse_next_data(soup)
    if next_items:
        return [_extract_from_next_item(i) for i in next_items]

    return _fallback_html_parse(soup)


if __name__ == "__main__":
    # Prueba rápida manual: python scrape_subito.py
    import sys
    citta = sys.argv[1] if len(sys.argv) > 1 else "Milano"
    for r in scrape(citta):
        print(r)
