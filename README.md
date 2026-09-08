# Affitto Scraper + Notifiche

Busca alquileres en Immobiliare.it, Idealista.it y Subito.it cada 30
minutos, y te avisa por notificación push (ntfy) cuando aparece un
anuncio nuevo que cumple tus criterios.

## Cómo funciona

- `scraper/main.py` corre en **GitHub Actions** (server, no en tu
  celular), cada 30 min, lee `criteria.json`, busca en los 3 sitios,
  compara contra `seen.json` (para no repetir avisos) y notifica por
  ntfy los anuncios nuevos que cumplen los criterios.
- La **PWA** (`index.html` + `app.js` + `criteria.js`) te deja ver el
  alquiler actual (pestaña "Dettagli", igual que antes) y editar los
  criterios de búsqueda (pestaña "Criteri"), que se guardan
  directamente en `criteria.json` del repo de GitHub.

## Puesta en marcha (una sola vez)

1. **Creá un repositorio en GitHub** y subí todos estos archivos.
2. **Instalá la app ntfy** en tu celular (Android/iOS, gratis) y
   suscribite al topic `affitto_canale_segreto_123` (o cambialo por
   uno tuyo, ver abajo — cuanto más raro el nombre, mejor, porque
   cualquiera que lo sepa puede recibir tus notificaciones).
3. **Configurá el secret de GitHub Actions**:
   - Repo → Settings → Secrets and variables → Actions → New repository secret
   - Nombre: `NTFY_TOPIC`, valor: tu topic (ej. `affitto_canale_segreto_123`)
4. **Activá el workflow**: Repo → Actions → habilitar workflows si
   pregunta. El cron corre solo cada 30 min; también podés
   dispararlo a mano desde la pestaña Actions ("Run workflow").
5. **Publicá la PWA** (opcional pero recomendado): Repo → Settings →
   Pages → activar GitHub Pages sobre la rama principal. Así podés
   abrir la app desde el celular y agregarla a la pantalla de inicio.
6. **Generá un Personal Access Token de GitHub** para poder editar
   los criterios desde la PWA:
   - GitHub → Settings → Developer settings → Personal access tokens
     → Fine-grained tokens → Generate new token
   - Repository access: solo este repositorio
   - Permisos: **Contents: Read and write**
   - Copiá el token y pegalo en la pestaña "Criteri" de la app junto
     con tu usuario y el nombre del repo (se guarda solo en tu
     celular, en el almacenamiento local del navegador).

## Ajustar los criterios

Desde la pestaña "Criteri" de la app, o editando `criteria.json`
directamente en GitHub:

```json
{
  "citta": "Milano",
  "prezzo_massimo": 900,
  "mq_minimi": 40,
  "locali_minimi": 2,
  "siti_attivi": { "immobiliare": true, "idealista": true, "subito": true }
}
```

## Limitaciones a tener en cuenta

- **Immobiliare.it e Idealista.it** tienen protecciones anti-bot más
  fuertes que Subito.it. Si el workflow empieza a fallar con errores
  403 en esos scrapers, hay que reemplazar el `requests.get` de
  `scrape_immobiliare.py` / `scrape_idealista.py` por un navegador
  headless (Playwright), que también puede correr en GitHub Actions.
- **Los selectores HTML de fallback pueden romperse** si esos sitios
  cambian su diseño (pasa cada tanto). El código prioriza leer datos
  estructurados (JSON embebido) porque es más estable, pero conviene
  revisar los logs del workflow de vez en cuando.
- No hagas el cron mucho más frecuente que cada 15-30 min: aumenta el
  riesgo de que tu IP (la de GitHub Actions) sea bloqueada.
