"""
Orquestador: corre los scrapers habilitados en criteria.json, filtra
resultados según los criterios, y notifica por ntfy solo los anuncios
nuevos (que no estén ya en seen.json).

Uso: python main.py
(Lo ejecuta el workflow de GitHub Actions en scraper.yml)
"""

import sys
import traceback

from common import load_criteria, load_seen, save_seen, matches_criteria, notify_ntfy

import scrape_immobiliare
import scrape_idealista
import scrape_subito

SCRAPERS = {
    "immobiliare": scrape_immobiliare,
    "idealista": scrape_idealista,
    "subito": scrape_subito,
}


def run():
    criteria = load_criteria()
    seen = load_seen()
    citta = criteria.get("citta", "")

    nuovi_totali = 0

    for fonte, modulo in SCRAPERS.items():
        if not criteria.get("siti_attivi", {}).get(fonte, True):
            continue

        print(f"[{fonte}] cercando annunci a {citta}...")
        try:
            annunci = modulo.scrape(citta)
        except Exception as e:
            print(f"[{fonte}] ERRORE durante lo scraping: {e}")
            traceback.print_exc()
            continue

        print(f"[{fonte}] trovati {len(annunci)} annunci totali")

        seen_ids = set(seen.get(fonte, []))
        nuovi = 0

        for annuncio in annunci:
            aid = annuncio.get("id")
            if not aid or aid in seen_ids:
                continue

            seen_ids.add(aid)

            if matches_criteria(annuncio, criteria):
                ok = notify_ntfy(annuncio, fonte)
                if ok:
                    nuovi += 1
                    nuovi_totali += 1
                    print(f"[{fonte}] notificato: {annuncio.get('titolo')}")

        seen[fonte] = list(seen_ids)
        print(f"[{fonte}] {nuovi} nuovi annunci che rispettano i criteri")

    save_seen(seen)
    print(f"Fatto. {nuovi_totali} notifiche inviate in totale.")


if __name__ == "__main__":
    run()
    sys.exit(0)
