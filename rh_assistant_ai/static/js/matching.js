/* ================================================================
   rh_assistant — matching.js
   Page : Comparer mon CV à une offre (matching.html)
   Modules :
     1. Bascule "Modifier le CV" (affiche/cache l'input file)
     2. Mise à jour du label de fichier sélectionné
     3. Validation du formulaire (active le bouton submit)
   ================================================================ */

document.addEventListener('DOMContentLoaded', () => {
  initCvEditToggle();
  initFileLabel('cvFileInput', 'cvFileLabel');
  initFileLabel('offreFileInput', 'offreFileLabel', 'offreStatusBadge');
  checkFormValidity();
});


/* ================================================================
   1. Bascule "Modifier le CV"
   ================================================================ */

function initCvEditToggle() {
  const editBtn   = document.getElementById('cvEditBtn');
  const loadedView = document.getElementById('cvLoadedView');
  const inputWrap  = document.getElementById('cvInputWrap');

  if (!editBtn || !inputWrap) return;

  editBtn.addEventListener('click', () => {
    const isOpen = inputWrap.style.display !== 'none';

    if (isOpen) {
      /* Annuler la modification : revenir à l'aperçu */
      inputWrap.style.display = 'none';
      editBtn.classList.remove('active');
      editBtn.innerHTML = '<i class="ti ti-edit"></i> Modifier';

      /* Réinitialiser le champ fichier */
      const fileInput = document.getElementById('cvFileInput');
      if (fileInput) fileInput.value = '';
      const label = document.getElementById('cvFileLabel');
      if (label) {
        label.textContent = "Aucun nouveau fichier sélectionné — le CV actuel sera utilisé";
        label.classList.remove('has-file', 'has-error');
      }
    } else {
      /* Ouvrir le champ pour choisir un nouveau CV */
      inputWrap.style.display = 'flex';
      editBtn.classList.add('active');
      editBtn.innerHTML = '<i class="ti ti-x"></i> Annuler';
    }

    checkFormValidity();
  });
}


/* ================================================================
   2. Mise à jour du label de fichier sélectionné
   ================================================================ */

/**
 * Lie un <input type="file"> à un texte d'aide qui affiche
 * le nom + la taille du fichier sélectionné.
 *
 * @param {string} inputId    - ID de l'input file
 * @param {string} labelId    - ID du <p> affichant le statut
 * @param {string} [badgeId]  - ID optionnel d'un badge de statut à mettre à jour
 */
function initFileLabel(inputId, labelId, badgeId) {
  const input = document.getElementById(inputId);
  const label = document.getElementById(labelId);
  if (!input || !label) return;

  input.addEventListener('change', () => {
    const file = input.files?.[0];

    if (!file) {
      label.textContent = "Aucun fichier n'a été sélectionné";
      label.classList.remove('has-file', 'has-error');
      updateBadge(badgeId, false);
      checkFormValidity();
      return;
    }

    /* Validation simple : extension PDF */
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'pdf') {
      label.textContent = 'Format non supporté — seul le PDF est accepté';
      label.classList.add('has-error');
      label.classList.remove('has-file');
      input.value = '';
      updateBadge(badgeId, false);
      checkFormValidity();
      return;
    }

    label.textContent = `${file.name} · ${formatBytes(file.size)}`;
    label.classList.add('has-file');
    label.classList.remove('has-error');

    updateBadge(badgeId, true);
    checkFormValidity();
  });
}

/** Met à jour le badge "Requis" → "Chargé" une fois un fichier sélectionné */
function updateBadge(badgeId, loaded) {
  if (!badgeId) return;
  const badge = document.getElementById(badgeId);
  if (!badge) return;

  if (loaded) {
    badge.className = 'match-status-badge match-status-badge--ok';
    badge.innerHTML = '<i class="ti ti-circle-check"></i> Chargé';
  } else {
    badge.className = 'match-status-badge match-status-badge--warn';
    badge.innerHTML = '<i class="ti ti-alert-circle"></i> Requis';
  }
}


/* ================================================================
   3. Validation du formulaire
   ================================================================ */

/**
 * Active le bouton "Comparer" uniquement si :
 *  - un CV est disponible (déjà en session OU nouveau fichier choisi)
 *  - une offre (PDF) est sélectionnée
 */
function checkFormValidity() {
  const submitBtn = document.getElementById('matchSubmitBtn');
  if (!submitBtn) return;

  const offreInput = document.getElementById('offreFileInput');
  const hasOffre   = !!offreInput?.files?.length;

  const cvLoadedView = document.getElementById('cvLoadedView');
  const cvInputWrap  = document.getElementById('cvInputWrap');
  const cvFileInput  = document.getElementById('cvFileInput');

  let hasCv;
  if (cvLoadedView) {
    /* Un CV existe déjà en session :
       valide si le champ de remplacement est fermé,
       ou si un nouveau fichier a été choisi */
    const isEditing = cvInputWrap && cvInputWrap.style.display !== 'none';
    hasCv = !isEditing || !!cvFileInput?.files?.length;
  } else {
    /* Aucun CV en session : un fichier doit être choisi */
    hasCv = !!cvFileInput?.files?.length;
  }

  submitBtn.disabled = !(hasCv && hasOffre);
}


/* ================================================================
   Utilitaires
   ================================================================ */

function formatBytes(bytes) {
  if (bytes < 1024)        return bytes + ' o';
  if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + ' Ko';
  return (bytes / (1024 * 1024)).toFixed(1) + ' Mo';
}
