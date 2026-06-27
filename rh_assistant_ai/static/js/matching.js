

// ============================================================
// AUTO-SOUMISSION EN FORMAT JSON PUR (Évite l'erreur 415)
// ============================================================
if (window.location.pathname.includes('matching') && window.location.search.includes('autorun=true')) {
    
    // On attend que la page soit bien chargée
    window.addEventListener('load', async () => {
        const form = document.getElementById('matchingForm');
        
        if (form) {
            // 1. Récupération des valeurs des inputs hidden générés par Jinja2
            const cvId = document.getElementById('hiddenCvId')?.value;
            const offreId = document.getElementById('hiddenOffreId')?.value;

            // Sécurité : On vérifie que les deux IDs sont bien présents avant de lancer l'appel
            if (!cvId || !offreId) {
                console.error("Impossible de lancer l'auto-run : IDs manquants dans le HTML.");
                return;
            }

            try {
                // 2. Envoi de la requête en arrière-plan au format APPLICATION/JSON
                const response = await fetch('/matching/run', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json' // 🧠 Indispensable pour request.get_json()
                    },
                    body: JSON.stringify({
                        cv_id: parseInt(cvId),
                        offre_id: parseInt(offreId)
                    })
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    // 3. Succès : Redirection vers votre page de rapport finale avec l'ID du match obtenu
                    // Ajustez l'URL ci-dessous selon la route de votre rapport final
                    window.location.href = `/matching/rapport/${result.data.id}`;
                } else {
                    alert(result.message || "Une erreur est survenue lors du calcul IA.");
                }

            } catch (error) {
                console.error("Erreur réseau lors du matching automatique :", error);
                alert("Le serveur n'a pas répondu à la demande d'analyse.");
            }
        }
    });
}



// ============================================================
// ACTION 1 : Comparer à mon CV (Solution A - Attributs de Données)
// ============================================================
document.querySelectorAll('.btn-analyser-offre').forEach(button => {
    button.addEventListener('click', function() {
        const offreId = this.getAttribute('data-offre-id');
        
        // Récupération de l'URL calculée proprement par le serveur Flask (/global/matching)
        const matchingBaseUrl = this.getAttribute('data-matching-url');
        
        // Effet visuel immédiat sur le bouton
        this.disabled = true;
        this.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Lancement IA...`;

        // Redirection propre sans accolades textuelles
        window.location.href = `${matchingBaseUrl}?select_offre_id=${offreId}&autorun=true`;
    });
});

// Déclencheur automatique d'analyse une fois arrivé sur la page de destination
if (window.location.pathname.includes('/global/matching') && window.location.search.includes('autorun=true')) {
    const form = document.getElementById('matchingForm'); 
    if (form) {
        setTimeout(() => {
            form.submit(); // Soumet automatiquement le formulaire en POST
        }, 300);
    }
}
