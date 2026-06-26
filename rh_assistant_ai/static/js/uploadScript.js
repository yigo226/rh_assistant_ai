
document.addEventListener("DOMContentLoaded", () => {

    // INITIALISATION DES STATUTS INITIALS (Basé sur vos badges Jinja existants)
    ['cv', 'offre'].forEach(type => {
        const badge = document.getElementById(`${type}StatusBadge`);
        if (badge) {
            // Si le badge a déjà la classe verte de Jinja, on le marque loaded, sinon empty
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
                    // L'utilisateur change le fichier -> le statut devient non-synchronisé (dirty)
                    badge.setAttribute('data-status', 'dirty');
                }
            });
        }

        // Bouton Modifier / Charger un autre
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
    // 2. LOGIQUE D'UPLOAD AJAX UNIQUE (FACTORISÉE)
    // ============================================================
    document.querySelectorAll('.btn-upload-ajax').forEach(button => {
        button.addEventListener("click", async function() {
            const targetType = this.getAttribute('data-target'); // 'cv' ou 'offre'
            const fileInput = document.getElementById(`${targetType}FileInput`);
            const badge = document.getElementById(`${targetType}StatusBadge`);

            if (!fileInput || !fileInput.files.length) {
                alert(`Veuillez sélectionner un fichier pour : ${targetType.toUpperCase()}.`);
                return;
            }

            const file = fileInput.files[0];
            const formData = new FormData();
            
            // Sécurité Clé Backend : "cv" pour le CV, "file" pour l'offre (comme vu dans votre route offre_route)
            const formKey = (targetType === 'cv') ? 'cv' : 'file';
            formData.append(formKey, file);

            try {
                this.disabled = true;
                this.innerHTML = '<i class="ti ti-loader"></i> Analyse...';

                // URL dynamique : /cv/upload ou /offre/upload
                const response = await fetch(`/${targetType}/upload`, {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (!data.success) {
                    alert(data.message);
                    return;
                }

                // Passage du badge au Vert
                badge.classList.remove("match-status-badge--warn");
                badge.classList.add("match-status-badge--ok");
                badge.innerHTML = '<i class="ti ti-circle-check"></i> Chargé';
                badge.setAttribute('data-status', 'loaded'); // Sécurise la soumission finale

                // Sauvegarde de l'ID de l'analyse dans le dataset
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
            const targetType = this.getAttribute('data-type'); // 'cv' ou 'offre'

            if (!analysisId) {
                alert("Aucune analyse disponible pour le moment.");
                return;
            }

            // Redirige vers /cv/result/ID ou /offre/result/ID selon le bloc
            window.location.href = `/${targetType}/result/${analysisId}`;
        });
    });

    // ============================================================
    // 4. SÉCURITÉ DE SOUMISSION DU FORMULAIRE GLOBAL
    // ============================================================
    const matchingForm = document.getElementById('matchingForm');
    if (matchingForm) {
        matchingForm.addEventListener('submit', function (event) {
            const cvStatus = document.getElementById('cvStatusBadge').getAttribute('data-status');
            const offreStatus = document.getElementById('offreStatusBadge').getAttribute('data-status');
            let errors = [];

            if (cvStatus === 'empty') errors.push("Votre CV est requis.");
            if (cvStatus === 'dirty') errors.push("Un nouveau CV est sélectionné. Cliquez sur 'Uploader' avant de comparer.");

            if (offreStatus === 'empty') errors.push("L'offre d'emploi est requise.");
            if (offreStatus === 'dirty') errors.push("Une nouvelle offre est sélectionnée. Cliquez sur 'Uploader' avant de comparer.");

            if (errors.length > 0) {
                event.preventDefault(); // Bloque la comparaison globale si un fichier n'est pas envoyé
                alert("Action impossible :\n\n" + errors.join("\n"));
            }
        });
    }
});

/* ----------------------------------------------------------------
  Chargement de l'offre ( PDF)
   ---------------------------------------------------------------- */

document.addEventListener("DOMContentLoaded", function () {


    const boutons = document.querySelectorAll(".btn-voir-pdf");
    console.log(boutons.length);

    const modalElement = document.getElementById("modalApercuOffre");

    const modal = new bootstrap.Modal(modalElement);

    const iframe = document.getElementById("iframePdfViewer");

    const titre = document.getElementById("modalOffreTitre");

    document.querySelectorAll(".btn-voir-pdf")
        .forEach(btn => {

            btn.addEventListener("click", function () {

                const pdfUrl = this.dataset.pdfUrl;

                const offreTitre = this.dataset.offreTitre;

                titre.textContent = offreTitre;

                iframe.src = pdfUrl;

                modal.show();

            });

        });
    
    document.querySelectorAll(".btn-voir-pdf").forEach(btn => {


    });
    modalElement.addEventListener("hidden.bs.modal", function () {

        iframe.src = "";

    });

});