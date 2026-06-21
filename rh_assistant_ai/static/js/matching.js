document.addEventListener("DOMContentLoaded", () => {

    // ============================================================
    // 1. INITIALISATION SYNCHRONE DU STATUT (Jinja -> JavaScript)
    // ============================================================
    ['cv', 'offre'].forEach(type => {
        const badge = document.getElementById(`${type}StatusBadge`);
        if (badge) {
            // Si le badge contient la classe de succès (--ok), le système sait que c'est chargé
            const isLoaded = badge.classList.contains('match-status-badge--ok');
            badge.setAttribute('data-status', isLoaded ? 'loaded' : 'empty');
        }
    });

    // ============================================================
    // 2. GESTION DU NOM DES FICHIERS ET BASCULEMENT DE VUE
    // ============================================================
    ['cv', 'offre'].forEach(type => {
        const fileInput = document.getElementById(`${type}FileInput`);
        const fileLabel = document.getElementById(`${type}FileLabel`);
        const badge = document.getElementById(`${type}StatusBadge`);

        if (fileInput) {
            fileInput.addEventListener("change", () => {
                if (fileInput.files.length > 0) {
                    fileLabel.textContent = fileInput.files[0].name;
                    // L'utilisateur change le fichier localement -> non synchronisé
                    badge.setAttribute('data-status', 'dirty');
                }
            });
        }

        // Boutons "Modifier / Charger un autre"
        const editBtn = document.getElementById(`${type}EditBtn`);
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                document.getElementById(`${type}LoadedView`).style.display = 'none';
                document.getElementById(`${type}InputWrap`).style.display = 'block';
                badge.setAttribute('data-status', 'dirty');
            });
        }
    });

    // ============================================================
    // 3. LOGIQUE D'UPLOAD AJAX FACTORISÉE
    // ============================================================
    document.querySelectorAll('.btn-upload-ajax').forEach(button => {
        button.addEventListener("click", async function() {
            const targetType = this.getAttribute('data-target'); // 'cv' ou 'offre'
            const fileInput = document.getElementById(`${targetType}FileInput`);
            const badge = document.getElementById(`${targetType}StatusBadge`);

            if (!fileInput || !fileInput.files.length) {
                alert(`Veuillez sélectionner un fichier PDF pour le bloc ${targetType.toUpperCase()}.`);
                return;
            }

            const file = fileInput.files[0];
            const formData = new FormData();
            
            // Respect strict des clés attendues par vos services Flask respectifs
            const formKey = (targetType === 'cv') ? 'cv' : 'file';
            formData.append(formKey, file);

            try {
                this.disabled = true;
                this.innerHTML = '<i class="ti ti-loader text-spin"></i> Analyse...';

                const response = await fetch(`/${targetType}/upload`, {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (!data.success) {
                    alert(data.message);
                    return;
                }

                // Passage du badge au Vert (Succès)
                badge.className = 'match-status-badge match-status-badge--ok';
                badge.innerHTML = '<i class="ti ti-circle-check"></i> Chargé';
                badge.setAttribute('data-status', 'loaded'); // Validation pour le bouton final

                // Sauvegarde immédiate de l'ID d'analyse renvoyé par la route d'upload
                document.querySelectorAll(`.btnVoirAnalyse[data-type="${targetType}"]`)
                    .forEach(btn => {
                        btn.dataset.analysisId = data.analysis_id;
                    });

                alert(`${targetType === 'cv' ? 'Votre CV' : "L'offre d'emploi"} a été traité(e) avec succès.`);

            } catch (error) {
                console.error(error);
                alert("Une erreur est survenue lors de la communication avec le serveur.");
            } finally {
                this.disabled = false;
                this.innerHTML = '<i class="ti ti-upload"></i> Uploader';
            }
        });
    });

    // ============================================================
    // 4. LOGIQUE UNIQUE POUR LES BOUTONS "VOIR" INDIVIDUELS
    // ============================================================
    document.querySelectorAll(".btnVoirAnalyse").forEach(btn => {
        btn.addEventListener("click", function() {
            const analysisId = this.dataset.analysisId;
            const targetType = this.getAttribute('data-type');

            if (!analysisId) {
                alert("Aucune analyse n'est disponible pour ce document pour le moment.");
                return;
            }

            window.location.href = `/${targetType}/result/${analysisId}`;
        });
    });

    // ============================================================
    // 5. BOUTON GLOBAL AJAX — APPEL DE LA ROUTE `/run`
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
                const response = await fetch('/run', {
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




// ============================================================
// LOGIQUE DU BOUTON DE MATCHING GLOBAL (AJAX) — VERSION FINALE
// // ============================================================
// const matchSubmitBtn = document.getElementById('matchSubmitBtn');

// if (matchSubmitBtn) {
//     matchSubmitBtn.addEventListener('click', async function () {
        
//         // 1. Récupération dynamique via le dataset (plus propre et standard avec votre code d'upload)
//         const cvBtn = document.querySelector('.btnVoirAnalyse[data-type="cv"]');
//         const offreBtn = document.querySelector('.btnVoirAnalyse[data-type="offre"]');
        
//         // .dataset.analysisId cible directement l'attribut data-analysis-id du HTML
//         const cvId = cvBtn ? cvBtn.dataset.analysisId : null;
//         const offreId = offreBtn ? offreBtn.dataset.analysisId : null;

//         // 2. Double sécurité côté client avant l'envoi
//         const cvStatusBadge = document.getElementById('cvStatusBadge');
//         const offreStatusBadge = document.getElementById('offreStatusBadge');
        
//         const cvStatus = cvStatusBadge ? cvStatusBadge.getAttribute('data-status') : 'empty';
//         const offreStatus = offreStatusBadge ? offreStatusBadge.getAttribute('data-status') : 'empty';

//         if (cvStatus !== 'loaded' || !cvId) {
//             alert("Action impossible : Veuillez d'abord uploader et analyser votre CV.");
//             return;
//         }
//         if (offreStatus !== 'loaded' || !offreId) {
//             alert("Action impossible : Veuillez d'abord uploader et analyser l'offre d'emploi.");
//             return;
//         }

//         // 3. Préparation de l'état visuel de chargement
//         this.disabled = true;
//         const originalContent = this.innerHTML;
//         this.innerHTML = '<i class="ti ti-loader text-spin"></i> Confrontation des profils en cours...';

//         try {
//             // 4. Envoi de la requête JSON à votre route backend
//             const response = await fetch('/run', {
//                 method: 'POST',
//                 headers: {
//                     'Content-Type': 'application/json'
//                     // Ajoutez le token CSRF ici si Flask-WTF / CSRFProtect est activé sur votre projet
//                 },
//                 body: JSON.stringify({
//                     cv_id: parseInt(cvId),
//                     offre_id: parseInt(offreId)
//                 })
//             });

//             const result = await response.json();

//             if (response.ok && result.success) {
//                 // 5. Redirection vers la page du rapport global
//                 const matchResultId = result.data.id; 
//                 window.location.href = `/matching/rapport/${matchResultId}`;
//             } else {
//                 alert("Échec du matching : " + (result.message || "Erreur inconnue"));
//                 this.disabled = false;
//                 this.innerHTML = originalContent;
//             }

//         } catch (error) {
//             console.error("Erreur lors du matching global:", error);
//             alert("Une erreur réseau ou serveur est survenue lors de l'analyse comparative.");
//             this.disabled = false;
//             this.innerHTML = originalContent;
//         }
//     });
// }
