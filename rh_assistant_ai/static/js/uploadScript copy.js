document.addEventListener("DOMContentLoaded", () => {

    // ============================================================
    // INITIALISATION DES STATUTS INITIALS (Basé sur vos badges Jinja)
    // ============================================================
    ['cv', 'offre'].forEach(type => {
        const badge = document.getElementById(`${type}StatusBadge`);
        if (badge) {
            const hasFile = badge.classList.contains('match-status-badge--ok');
            badge.setAttribute('data-status', hasFile ? 'loaded' : 'empty');
        }
    });

    // ============================================================
    // 1. GESTION DU NOM DES FICHIERS ET CHANGEMENT DE STATUT
    // ============================================================
    ['cv', 'offre'].forEach(type => {
        const fileInput = document.getElementById(`${type}FileInput`);
        const fileLabel = document.getElementById(`${type}FileLabel`);
        const badge = document.getElementById(`${type}StatusBadge`);

        if (fileInput) {
            fileInput.addEventListener("change", () => {
                if (fileInput.files.length > 0) {
                    fileLabel.textContent = fileInput.files[0].name;
                    badge.setAttribute('data-status', 'dirty');
                }
            });
        }

        const editBtn = document.getElementById(`${type}EditBtn`);
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                const loadedView = document.getElementById(`${type}LoadedView`);
                const inputWrap = document.getElementById(`${type}InputWrap`);
                if (loadedView) loadedView.style.display = 'none';
                if (inputWrap) inputWrap.style.display = 'block';
                if (badge) badge.setAttribute('data-status', 'dirty');
            });
        }
    });

    // ============================================================
    // 2. LOGIQUE D'UPLOAD AJAX UNIQUE (FACTORISÉE)
    // ============================================================
    document.querySelectorAll('.btn-upload-ajax').forEach(button => {
        button.addEventListener("click", async function() {
            const targetType = this.getAttribute('data-target');
            const fileInput = document.getElementById(`${targetType}FileInput`);
            const badge = document.getElementById(`${targetType}StatusBadge`);

            if (!fileInput || !fileInput.files.length) {
                alert(`Veuillez sélectionner un fichier pour : ${targetType.toUpperCase()}.`);
                return;
            }

            const file = fileInput.files[0];
            const formData = new FormData();
            const formKey = (targetType === 'cv') ? 'cv' : 'file';
            formData.append(formKey, file);

            try {
                this.disabled = true;
                this.innerHTML = '<i class="ti ti-loader"></i> Analyse...';

                const response = await fetch(`/${targetType}/upload`, {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (!data.success) {
                    alert(data.message);
                    return;
                }

                if (badge) {
                    badge.classList.remove("match-status-badge--warn");
                    badge.classList.add("match-status-badge--ok");
                    badge.innerHTML = '<i class="ti ti-circle-check"></i> Chargé';
                    badge.setAttribute('data-status', 'loaded');
                }

                document.querySelectorAll(`.btnVoirAnalyse[data-type="${targetType}"]`)
                    .forEach(btn => {
                        btn.dataset.analysisId = data.analysis_id;
                    });

                alert(`${targetType === 'cv' ? 'CV' : "L'offre"} analysé(e) avec succès.`);

            } catch (error) {
                console.error(error);
                alert("Erreur serveur.");
            } finally {
                this.disabled = false;
                this.innerHTML = '<i class="ti ti-upload"></i> Uploader';
            }
        });
    });

    // ============================================================
    // 3. LOGIQUE UNIQUE POUR LES BOUTONS "VOIR" (FACTORISÉE)
    // ============================================================
    document.querySelectorAll(".btnVoirAnalyse").forEach(btn => {
        btn.addEventListener("click", function() {
            const analysisId = this.dataset.analysisId;
            const targetType = this.getAttribute('data-type');

            if (!analysisId) {
                alert("Aucune analyse disponible pour le moment.");
                return;
            }

            window.location.href = `/${targetType}/result/${analysisId}`;
        });
    });

    // ============================================================
    // 4. SÉCURITÉ DE SOUMISSION DU FORMULAIRE GLOBAL
    // ============================================================
    const matchingForm = document.getElementById('matchingForm');
    if (matchingForm) {
        matchingForm.addEventListener('submit', function (event) {
            const cvBadge = document.getElementById('cvStatusBadge');
            const offreBadge = document.getElementById('offreStatusBadge');
            
            const cvStatus = cvBadge ? cvBadge.getAttribute('data-status') : 'empty';
            const offreStatus = offreBadge ? offreBadge.getAttribute('data-status') : 'empty';
            let errors = [];

            if (cvStatus === 'empty') errors.push("Votre CV est requis.");
            if (cvStatus === 'dirty') errors.push("Un nouveau CV est sélectionné. Cliquez sur 'Uploader' avant de comparer.");

            if (offreStatus === 'empty') errors.push("L'offre d'emploi est requise.");
            if (offreStatus === 'dirty') errors.push("Une nouvelle offre est sélectionnée. Cliquez sur 'Uploader' avant de comparer.");

            if (errors.length > 0) {
                event.preventDefault();
                alert("Action impossible :\n\n" + errors.join("\n"));
            }
        });
    }

    // ============================================================
    // 5. GESTION DES FENÊTRES POP-UPS (Nouveau Bloc Intégré et Sécurisé)
    // ============================================================
    const htmlApercu = document.getElementById("modalApercuOffre");
    const htmlAnalyse = document.getElementById("modalDetailsAnalyse");
    const iframeViewer = document.getElementById("iframePdfViewer");
    const modalTitre = document.getElementById("modalOffreTitre");

    let modalApercu = null;
    let modalAnalyse = null;
    let isNativeMode = false;

    // Initialisation sécurisée
    try {
        if (htmlApercu && typeof bootstrap !== 'undefined') modalApercu = new bootstrap.Modal(htmlApercu);
        if (htmlAnalyse && typeof bootstrap !== 'undefined') modalAnalyse = new bootstrap.Modal(htmlAnalyse);
    } catch (e) {
        console.warn("Rétrocompatibilité : Passage en mode d'ouverture natif HTML.");
        isNativeMode = true;
    }

    // Écouteur pour le bouton de l'œil (Aperçu PDF)
    document.querySelectorAll(".btn-voir-pdf").forEach(btn => {
        btn.addEventListener("click", function () {
            const pdfUrl = this.getAttribute('data-pdf-url') || this.dataset.pdfUrl;
            const offreTitre = this.getAttribute('data-offre-titre') || this.dataset.offreTitre;

            if (iframeViewer && modalTitre) {
                modalTitre.textContent = offreTitre || "Fiche de poste";
                iframeViewer.src = pdfUrl;

                // FIX LIGNE 187 : Ouverture selon le mode détecté (Natif ou Bootstrap)
                if (isNativeMode && htmlApercu) {
                    htmlApercu.style.display = 'block';
                    htmlApercu.classList.add('show');
                    htmlApercu.style.background = 'rgba(0,0,0,0.5)';
                } else if (modalApercu) {
                    modalApercu.show();
                }
            }
        });
    });

    // Nettoyage de l'iframe à la fermeture
    if (htmlApercu && iframeViewer) {
        htmlApercu.addEventListener("hidden.bs.modal", function () {
            iframeViewer.src = "";
        });
    }

    // Gestion manuelle de la fermeture si le mode natif s'active
    document.querySelectorAll('[data-bs-dismiss="modal"], .btn-close').forEach(closeBtn => {
        closeBtn.addEventListener('click', () => {
            if (htmlApercu) htmlApercu.style.display = 'none';
            if (htmlAnalyse) htmlAnalyse.style.display = 'none';
            if (iframeViewer) iframeViewer.src = "";
        });
    });
});
