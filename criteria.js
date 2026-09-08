// Maneja la pestaña "Criteri": carga/guarda criteria.json directamente
// en el repositorio de GitHub usando la Contents API, para que el
// workflow de GitHub Actions lea siempre la versión más reciente.

const GH_CONFIG_KEY = "affitto_gh_config";

function getGhConfig() {
  try {
    return JSON.parse(localStorage.getItem(GH_CONFIG_KEY) || "{}");
  } catch {
    return {};
  }
}

function saveGhConfig(config) {
  localStorage.setItem(GH_CONFIG_KEY, JSON.stringify(config));
}

function setStatus(msg, isError = false) {
  const el = document.getElementById("criteria-status");
  el.textContent = msg;
  el.style.color = isError ? "#c53030" : "#2f855a";
}

// --- Tabs ---
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`tab-${tab.dataset.tab}`).classList.add("active");
  });
});

// --- Config GitHub ---
window.addEventListener("DOMContentLoaded", () => {
  const config = getGhConfig();
  if (config.owner) document.getElementById("gh-owner").value = config.owner;
  if (config.repo) document.getElementById("gh-repo").value = config.repo;
  if (config.token) document.getElementById("gh-token").value = config.token;

  if (config.owner && config.repo && config.token) {
    loadCriteria();
  }
});

document.getElementById("save-config-btn").addEventListener("click", () => {
  const config = {
    owner: document.getElementById("gh-owner").value.trim(),
    repo: document.getElementById("gh-repo").value.trim(),
    token: document.getElementById("gh-token").value.trim(),
  };
  if (!config.owner || !config.repo || !config.token) {
    setStatus("Compila utente, repository e token prima di salvare.", true);
    return;
  }
  saveGhConfig(config);
  setStatus("Configurazione salvata. Carico i criteri attuali...");
  loadCriteria();
});

// --- Carga/guarda criteria.json vía GitHub Contents API ---
function ghContentsUrl(config) {
  return `https://api.github.com/repos/${config.owner}/${config.repo}/contents/criteria.json`;
}

async function loadCriteria() {
  const config = getGhConfig();
  if (!config.owner || !config.repo || !config.token) return;

  try {
    const res = await fetch(ghContentsUrl(config), {
      headers: { Authorization: `Bearer ${config.token}` },
    });
    if (!res.ok) {
      setStatus(`Errore nel caricare criteria.json (HTTP ${res.status})`, true);
      return;
    }
    const data = await res.json();
    const criteria = JSON.parse(decodeURIComponent(escape(atob(data.content))));

    document.getElementById("citta").value = criteria.citta || "";
    document.getElementById("prezzo_massimo").value = criteria.prezzo_massimo ?? "";
    document.getElementById("mq_minimi").value = criteria.mq_minimi ?? "";
    document.getElementById("locali_minimi").value = criteria.locali_minimi ?? "";
    document.getElementById("site-immobiliare").checked = !!criteria.siti_attivi?.immobiliare;
    document.getElementById("site-idealista").checked = !!criteria.siti_attivi?.idealista;
    document.getElementById("site-subito").checked = !!criteria.siti_attivi?.subito;

    setStatus("Criteri caricati.");
  } catch (err) {
    setStatus("Errore di connessione a GitHub: " + err, true);
  }
}

document.getElementById("criteria-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const config = getGhConfig();
  if (!config.owner || !config.repo || !config.token) {
    setStatus("Configura prima utente, repository e token GitHub.", true);
    return;
  }

  const criteria = {
    citta: document.getElementById("citta").value.trim(),
    prezzo_massimo: Number(document.getElementById("prezzo_massimo").value) || null,
    mq_minimi: Number(document.getElementById("mq_minimi").value) || null,
    locali_minimi: Number(document.getElementById("locali_minimi").value) || null,
    siti_attivi: {
      immobiliare: document.getElementById("site-immobiliare").checked,
      idealista: document.getElementById("site-idealista").checked,
      subito: document.getElementById("site-subito").checked,
    },
  };

  setStatus("Salvo su GitHub...");

  try {
    // Necesitamos el SHA del archivo actual para poder sobreescribirlo.
    const getRes = await fetch(ghContentsUrl(config), {
      headers: { Authorization: `Bearer ${config.token}` },
    });
    if (!getRes.ok) {
      setStatus(`Errore nel leggere il file attuale (HTTP ${getRes.status})`, true);
      return;
    }
    const current = await getRes.json();

    const contentB64 = btoa(unescape(encodeURIComponent(JSON.stringify(criteria, null, 2))));

    const putRes = await fetch(ghContentsUrl(config), {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${config.token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: "Aggiorna criteria.json dalla PWA",
        content: contentB64,
        sha: current.sha,
      }),
    });

    if (putRes.ok) {
      setStatus("Criteri salvati con successo!");
    } else {
      const errBody = await putRes.json().catch(() => ({}));
      setStatus(`Errore nel salvare (HTTP ${putRes.status}): ${errBody.message || ""}`, true);
    }
  } catch (err) {
    setStatus("Errore di connessione a GitHub: " + err, true);
  }
});
