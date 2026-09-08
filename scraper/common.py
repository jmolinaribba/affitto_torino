"""
Funciones compartidas por todos los scrapers:
- cargar/guardar criterios y anuncios ya vistos
- enviar notificaciones por ntfy
- headers "humanos" para reducir el riesgo de bloqueo

IMPORTANTE: los sitios de anuncios cambian su HTML con frecuencia.
Si un scraper deja de encontrar resultados, lo primero que hay que
revisar es si los selectores (funciones extract_* de cada scraper)
siguen coincidiendo con la página actual.
"""

import json
import os
import requests

# Se completa vía variable de entorno en GitHub Actions (Settings > Secrets)
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "affitto_canale_segreto_123")
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRITERIA_PATH = os.path.join(BASE_DIR, "criteria.json")
SEEN_PATH = os.path.join(BASE_DIR, "seen.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9",
}


def load_criteria():
    with open(CRITERIA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_seen():
    if not os.path.exists(SEEN_PATH):
        return {"immobiliare": [], "idealista": [], "subito": []}
    with open(SEEN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_seen(seen):
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)


def matches_criteria(listing, criteria):
    """listing: dict con claves prezzo, mq, locali (algunas pueden faltar -> se ignoran)."""
    prezzo = listing.get("prezzo")
    mq = listing.get("mq")
    locali = listing.get("locali")

    if prezzo is not None and criteria.get("prezzo_massimo") is not None:
        if prezzo > criteria["prezzo_massimo"]:
            return False
    if mq is not None and criteria.get("mq_minimi") is not None:
        if mq < criteria["mq_minimi"]:
            return False
    if locali is not None and criteria.get("locali_minimi") is not None:
        if locali < criteria["locali_minimi"]:
            return False
    return True


def notify_ntfy(listing, fonte):
    titolo = f"Nuovo affitto ({fonte})"
    dettagli = []
    if listing.get("prezzo") is not None:
        dettagli.append(f"{listing['prezzo']} €")
    if listing.get("mq") is not None:
        dettagli.append(f"{listing['mq']} mq")
    if listing.get("locali") is not None:
        dettagli.append(f"{listing['locali']} locali")

    corpo = f"{listing.get('titolo', 'Annuncio')}\n" + " · ".join(dettagli)

    try:
        resp = requests.post(
            NTFY_URL,
            data=corpo.encode("utf-8"),
            headers={
                "Title": titolo.encode("utf-8"),
                "Priority": "high",
                "Tags": "house,moneybag",
                "Click": listing.get("url", ""),
            },
            timeout=15,
        )
        return resp.ok
    except requests.RequestException as e:
        print(f"[ntfy] errore invio notifica: {e}")
        return False
