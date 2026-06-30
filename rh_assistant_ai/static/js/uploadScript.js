document.addEventListener("DOMContentLoaded", () => {

    // ============================================================
    // INITIALISATION DES STATUTS INITIALS (Badges Jinja)
    // ============================================================
    ['cv', 'offre'].forEach(type => {
        const badge = document.getElementById(`${type}StatusBadge`);
        if (badge) {
            // vue du badge ( succès)

            //const isLoaded = badge.classList.contains('match-status-badge--ok');
            //badge.setAttribute('data-status', isLoaded ? 'loaded' : 'empty');
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
        // Boutons "Modifier / Charger un autre"
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

            // Respect strict des clés attendues par vos services Flask respectifs
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
    // 5. GESTION DES FENÊTRES POP-UPS & APERÇU PDF
    // ============================================================
    const htmlApercu = document.getElementById("modalApercuOffre");
    const htmlAnalyse = document.getElementById("modalDetailsAnalyse");
    const iframeViewer = document.getElementById("iframePdfViewer");
    const modalTitre = document.getElementById("modalOffreTitre");
    const modalAnalyseContenu = document.getElementById("modalAnalyseContenu");

    let modalApercu = null;
    let modalAnalyse = null;
    let isNativeMode = false;

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
    // ============================================================
    // 🟢 AJOUTÉ : LOGIQUE POUR LE BOUTON DÉTAILS (RAPPORT IA 🤖)
    // ============================================================
    document.querySelectorAll('.btn-details-analyse').forEach(button => {
        button.addEventListener('click', async function() {
            const offreId = this.getAttribute('data-offre-id');
            
            if (!modalAnalyseContenu) return;

            // 1. Affichage du loader d'attente animé natif Bootstrap
            modalAnalyseContenu.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-success" role="status"></div>
                    <p class="text-muted mt-2">Récupération des métriques auprès de l'assistant IA...</p>
                </div>`;
            
            // 2. Ouverture de la modale d'analyse (S'adapte au mode Bootstrap ou Natif)
            if (isNativeMode && htmlAnalyse) {
                htmlAnalyse.style.display = 'block';
                htmlAnalyse.classList.add('show');
                htmlAnalyse.style.background = 'rgba(0,0,0,0.5)';
            } else if (modalAnalyse) {
                modalAnalyse.show();
            }

            try {
                // 3. Appel AJAX vers votre route backend Flask
                const response = await fetch(`/matching/recuperer-details-json/${offreId}`);
                const data = await response.json();
                
                if (response.ok && data.success) {
                    // 4. Construction et injection dynamique du rapport au format HTML
                    modalAnalyseContenu.innerHTML = `
                        <div class="row align-items-center mb-4">
                            <div class="col-sm-4 text-center">
                                <div class="d-inline-flex align-items-center justify-content-center rounded-circle border border-4 border-success" style="width: 100px; height: 100px;">
                                    <span class="h2 font-weight-bold mb-0 text-dark">${Math.floor(data.score)}%</span>
                                </div>
                                <span class="d-block text-muted small mt-2">Score d'adéquation</span>
                            </div>
                            <div class="col-sm-8 border-start">
                                <h6 class="font-weight-bold text-uppercase small text-secondary"><i class="ti ti-message-chatbot"></i> Synthèse de l'assistant</h6>
                                <p class="text-dark small mb-0" style="line-height: 1.5;">${data.recommendation}</p>
                            </div>
                        </div>

                        <div class="d-flex flex-column gap-3">
                            <div>
                                <h6 class="text-success font-weight-bold small text-uppercase mb-2"><i class="ti ti-circle-check"></i> Compétences Validées (${data.matching_skills.length})</h6>
                                <div class="d-flex flex-wrap gap-1">
                                    ${data.matching_skills.map(s => `<span class="badge px-2 py-1 small rounded text-success" style="background-color: #f0fdf4; border: 1px solid #bbf7d0;">${s}</span>`).join('') || '<span class="text-muted small italic">Aucune correspondance.</span>'}
                                </div>
                            </div>
                            <div>
                                <h6 class="text-danger font-weight-bold small text-uppercase mb-2"><i class="ti ti-circle-x"></i> Compétences Manquantes (${data.missing_skills.length})</h6>
                                <div class="d-flex flex-wrap gap-1">
                                    ${data.missing_skills.map(s => `<span class="badge px-2 py-1 small rounded text-danger" style="background-color: #fef2f2; border: 1px solid #fecaca;">${s}</span>`).join('') || '<span class="text-success small fw-bold">Parfait ! Rien ne manque.</span>'}
                                </div>
                            </div>
                            <div>
                                <h6 class="text-primary font-weight-bold small text-uppercase mb-2"><i class="ti ti-plus"></i> Compétences Extra (${data.extra_skills.length})</h6>
                                <div class="d-flex flex-wrap gap-1">
                                    ${data.extra_skills.map(s => `<span class="badge px-2 py-1 small rounded text-primary" style="background-color: #eff6ff; border: 1px solid #bfdbfe;">${s}</span>`).join('') || '<span class="text-muted small italic">Aucun bonus.</span>'}
                                </div>
                            </div>
                        </div>`;
                } else {
                    modalAnalyseContenu.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                }
            } catch (error) {
                console.error(error);
                modalAnalyseContenu.innerHTML = `<div class="alert alert-danger">Erreur réseau lors de la récupération des données.</div>`;
            }
        });
    });

    // ============================================================
    // 6. GESTION UNIFIÉE DE LA FERMETURE (Croix et Boutons fermer)
    // ============================================================
    const fermerToutesLesModales = () => {
        if (htmlApercu) htmlApercu.style.display = 'none';
        if (htmlAnalyse) htmlAnalyse.style.display = 'none';
        if (iframeViewer) iframeViewer.src = ""; // Coupe instantanément le PDF
        
        if (!isNativeMode) {
            if (modalApercu) modalApercu.hide();
            if (modalAnalyse) modalAnalyse.hide();
        }
    };

    // Écoute le clic sur toutes les croix "X" ou boutons fermer du projet
    document.querySelectorAll('[data-bs-dismiss="modal"], .btn-close').forEach(btn => {
        btn.addEventListener('click', fermerToutesLesModales);
    });

    // Nettoyage classique si Bootstrap standard s'active un jour pour l'iframe
    if (htmlApercu && iframeViewer) {
        htmlApercu.addEventListener('hidden.bs.modal', () => {
            iframeViewer.src = "";
        });
    }


   // ============================================================
    // 5. G BOUTON GLOBAL AJAX — APPEL DE LA ROUTE `/run`
    // ============================================================
    const matchSubmitBtn = document.getElementById('matchSubmitBtn');

    if (matchSubmitBtn) {
        matchSubmitBtn.addEventListener('click', async function () {
            
            const cvBtn = document.querySelector('.btnVoirAnalyse[data-type="cv"]');
            const offreBtn = document.querySelector('.btnVoirAnalyse[data-type="offre"]');
            
            const cvId = cvBtn ? cvBtn.dataset.analysisId : null;
            const offreId = offreBtn ? offreBtn.dataset.analysisId : null;

            const cvStatus = document.getElementById('cvStatusBadge').getAttribute('data-status');
            const offreStatus = document.getElementById('offreStatusBadge').getAttribute('data-status');

            // Vérifications de sécurité basées sur le statut réel
            if (cvStatus !== 'loaded' || !cvId || cvId === "") {
                alert("Action impossible : Votre CV doit être chargé et analysé.");
                return;
            }
            if (offreStatus !== 'loaded' || !offreId || offreId === "") {
                alert("Action impossible : L'offre d'emploi doit être chargée et analysée.");
                return;
            }

            // Animation du bouton de chargement
            this.disabled = true;
            const originalContent = this.innerHTML;
            this.innerHTML = '<i class="ti ti-loader text-spin"></i> Calcul de compatibilité...';

            try {
                const response = await fetch('/matching/run', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        cv_id: parseInt(cvId),
                        offre_id: parseInt(offreId)
                    })
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    // Redirection directe vers la page du rapport global généré
                    window.location.href = `/matching/rapport/${result.data.id}`;
                } else {
                    alert("Erreur de calcul : " + (result.message || "Impossible de matcher les profils."));
                    this.disabled = false;
                    this.innerHTML = originalContent;
                }

            } catch (error) {
                console.error("Erreur Matching Global:", error);
                alert("Erreur réseau ou serveur lors de la confrontation des profils.");
                this.disabled = false;
                this.innerHTML = originalContent;
            }
        });
    }
});

