/* ================================================================
   rh_assistant — script.js
   Modules :
     1. Chargement des composants HTML (navbar, footer)
     2. Gestion de la sidebar (toggle mobile)
     3. Navigation (boutons actifs + contexte)
     4. Chat — envoi & réception de messages
     5. API IA — à brancher ici
     6. Utilitaires
   ================================================================ */


/* ----------------------------------------------------------------
   1. Chargement des composants HTML
   ---------------------------------------------------------------- */

/**
 * Charge un fichier HTML partiel et l'injecte dans un élément cible.
 * @param {string} placeholderId - ID de l'élément cible
 * @param {string} filePath      - Chemin vers le composant HTML
 * @param {Function} [callback]  - Appelé après injection
 */
async function loadComponent(placeholderId, filePath, callback) {
  try {
    const res  = await fetch(filePath);
    if (!res.ok) throw new Error(`Erreur chargement : ${filePath} (${res.status})`);
    const html = await res.text();
    const el   = document.getElementById(placeholderId);
    if (!el) return;
    el.outerHTML = html;                 // remplace le placeholder par le vrai markup
    if (typeof callback === 'function') callback();
  } catch (err) {
    console.error('[rh_assistant]', err);
  }
}

/** Initialise tous les composants puis démarre l'application */

/* ----------------------------------------------------------------
   2. Sidebar toggle (mobile)
   ---------------------------------------------------------------- */

function initSidebarToggle() {
  const toggleBtn = document.getElementById('sidebarToggle');
  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', () => {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) sidebar.classList.toggle('open');
  });

  // Fermer en cliquant en dehors (mobile)
  document.addEventListener('click', (e) => {
    const sidebar = document.querySelector('.sidebar');
    const toggle  = document.getElementById('sidebarToggle');
    if (
      sidebar &&
      sidebar.classList.contains('open') &&
      !sidebar.contains(e.target) &&
      toggle && !toggle.contains(e.target)
    ) {
      sidebar.classList.remove('open');
    }
  });
}


/* ----------------------------------------------------------------
   3. Navigation — boutons actifs + contexte chat
   ---------------------------------------------------------------- */

/** Labels affichés dans le chat selon l'action choisie */
const ACTION_LABELS = {
  'analyser-cv':       'Analyser un CV',
  'analyser-offre':    'Analyser une offre',
  'matching':          'Matching CV / Offre',
  'grille-entretien':  "Grille d'entretien",
  'mail-rh':           'Rédiger un mail RH',
  'rapport':           'Rapport de recrutement',
  'preferences':       'Préférences',
  'deconnexion':       'Déconnexion',
};

/** Message d'invite contextuel selon l'action */
const ACTION_PROMPTS = {
  'analyser-cv':      'Envoyez ou collez le texte du CV à analyser.',
  'analyser-offre':   "Envoyez ou collez le texte de l'offre d'emploi.",
  'matching':         'Fournissez le CV puis l\'offre pour le matching.',
  'grille-entretien': 'Précisez le poste pour générer la grille.',
  'mail-rh':          'Décrivez le contexte du mail à rédiger.',
  'rapport':          'Indiquez la période ou le poste concerné.',
};

function initNavbar() {
  const btns = document.querySelectorAll('.nav-btn');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      // Activer le bouton
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const action = btn.dataset.action;

      // Fermer sidebar sur mobile
      const sidebar = document.querySelector('.sidebar');
      if (sidebar) sidebar.classList.remove('open');

      // Afficher un message contextuel dans le chat
      if (ACTION_PROMPTS[action]) {
        appendBotMessage(ACTION_PROMPTS[action]);
      }
    });
  });

  initSidebarToggle();
}


/* ----------------------------------------------------------------
   4. Chat — envoi & réception de messages
   ---------------------------------------------------------------- */

const chatMessages = document.getElementById('chatMessages');

/** Crée et ajoute un message utilisateur */
function appendUserMessage(text) {
  const wrapper = document.createElement('div');
  wrapper.className = 'msg msg-user';
  wrapper.innerHTML = `
    <div class="msg-avatar avatar-user">Moi</div>
    <div class="msg-content">
      <div class="msg-bubble">${escapeHtml(text)}</div>
    </div>
  `;
  chatMessages.appendChild(wrapper);
  scrollToBottom();
}

/** Crée et ajoute un message bot */
function appendBotMessage(text) {
  const wrapper = document.createElement('div');
  wrapper.className = 'msg msg-bot';
  wrapper.innerHTML = `
    <div class="msg-avatar avatar-bot">AI</div>
    <div class="msg-content">
      <div class="msg-bubble">${escapeHtml(text)}</div>
    </div>
  `;
  chatMessages.appendChild(wrapper);
  scrollToBottom();
}

/** Affiche l'indicateur de frappe */
function showTyping() {
  const el = document.createElement('div');
  el.className = 'msg msg-bot';
  el.id = 'typingIndicator';
  el.innerHTML = `
    <div class="msg-avatar avatar-bot">AI</div>
    <div class="typing-indicator">
      <span></span><span></span><span></span>
    </div>
  `;
  chatMessages.appendChild(el);
  scrollToBottom();
}

/** Supprime l'indicateur de frappe */
function hideTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

/** Gère l'envoi d'un message */
async function handleSend() {
  const input = document.getElementById('msgInput');
  const text  = input.value.trim();
  if (!text) return;

  input.value = '';
  appendUserMessage(text);
  showTyping();

  // ----------------------------------------------------------------
  // 5. APPEL API — à remplacer par votre backend ou Claude API
  // ----------------------------------------------------------------
  const reply = await fetchAIResponse(text);
  hideTyping();
  appendBotMessage(reply);
}

/** Liaison des événements du chat */
function initChat() {
  const sendBtn  = document.getElementById('sendBtn');
  const msgInput = document.getElementById('msgInput');

  if (sendBtn)  sendBtn.addEventListener('click', handleSend);
  if (msgInput) {
    msgInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });
  }
}


/* ----------------------------------------------------------------
   5. API IA — connectez ici votre backend
   ---------------------------------------------------------------- */

/**
 * Envoie un message à votre API et retourne la réponse.
 * Remplacez cette fonction par votre vrai appel (Anthropic, OpenAI, etc.)
 *
 * @param {string} userMessage
 * @returns {Promise<string>}
 */
async function fetchAIResponse(userMessage) {
  /* --- Exemple de stub à remplacer --- */
  // const res  = await fetch('/api/chat', {
  //   method:  'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body:    JSON.stringify({ message: userMessage }),
  // });
  // const data = await res.json();
  // return data.reply;

  // Réponse simulée (à supprimer en production)
  await delay(1200);
  return `[API non connectée] Votre message : "${userMessage}" — Branchez votre backend dans fetchAIResponse().`;
}


/* ----------------------------------------------------------------
   6. Utilitaires
   ---------------------------------------------------------------- */

function scrollToBottom() {
  if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(str) {
  return str
    .replace(/&/g,  '&amp;')
    .replace(/</g,  '&lt;')
    .replace(/>/g,  '&gt;')
    .replace(/"/g,  '&quot;')
    .replace(/'/g,  '&#39;');
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


/* ----------------------------------------------------------------
   Démarrage
   ---------------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', async () => {
  //await initComponents();   // charge navbar + footer
  initChat();               // lie les événements du chat
});
