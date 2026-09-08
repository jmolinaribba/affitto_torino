const NTFY_TOPIC = "affitto_canale_segreto_123";

// Registrazione Service Worker per PWA
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js')
    .then(() => console.log('Service Worker registrato'))
    .catch(err => console.error('Errore SW:', err));
}

// Caricamento dati da data.json
fetch('data.json')
  .then(res => res.json())
  .then(data => {
    const total = data.importo_canone + data.importo_spese;
    document.getElementById('content').innerHTML = `
      <div class="detail"><span class="label">Inquilino:</span> ${data.inquilino}</div>
      <div class="detail"><span class="label">Immobile:</span> ${data.immobile}</div>
      <div class="detail"><span class="label">Canone:</span> ${data.importo_canone} €</div>
      <div class="detail"><span class="label">Spese:</span> ${data.importo_spese} €</div>
      <div class="detail"><span class="label">Totale Mensile:</span> <strong>${total} €</strong></div>
      <div class="detail"><span class="label">Scadenza:</span> Giorno ${data.giorno_scadenza} del mese</div>
      <div class="detail"><span class="label">Stato:</span> ${data.stato_pagamento}</div>
    `;
  })
  .catch(err => {
    document.getElementById('content').innerText = "Errore nel caricamento dei dati.";
  });

// Pulsante per inviare notifica immediata di test
document.getElementById('test-btn').addEventListener('click', () => {
  fetch(`https://ntfy.sh/${NTFY_TOPIC}`, {
    method: 'POST',
    headers: {
      'Title': 'Test Notifica Affitto',
      'Priority': 'default',
      'Tags': 'test,house'
    },
    body: 'Questo è un messaggio di test inviato direttamente dalla tua PWA!'
  })
  .then(res => {
    if (res.ok) alert('Notifica inviata con successo!');
    else alert('Errore invio notifica.');
  })
  .catch(err => alert('Errore di connessione: ' + err));
});