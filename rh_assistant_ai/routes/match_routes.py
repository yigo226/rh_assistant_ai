from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.cv_analyser import CVAnalyser
from models.offre_analyser import OffreAnalyser
from services.matching_service import calculer_matching, enregistrer_match_result
from flask import render_template, session
from models.cv import CV
from models.offre import Offre
from models.match_result import MatchResult

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    flash,
    redirect,
    url_for
)


matching_bp = Blueprint(
    "matching",
    __name__,
    url_prefix="/matching"
)

# faire une comparaison d'un offre avec mon cv


@matching_bp.route("/start_match", methods=["GET"])
@login_required
def start_match():
    # 1. Récupération du tout dernier CV de l'utilisateur (votre logique d'origine)
    existing_cv = (
        CV.query
        .filter_by(user_id=current_user.id)
        .order_by(CV.id.desc())
        .first()
    )
    print(" le cv dans start_match : ", existing_cv)

    # 2. Récupération de l'offre active via la session (Plan A — Historique)
    existing_offre = None
    current_offre_id = session.get('current_offre_id')
    
    if current_offre_id:
        existing_offre = Offre.query.get(current_offre_id)
    
    # Sécurité Plan A : Si la session est vide, on prend la dernière offre de son historique
    if not existing_offre:
        existing_offre = (
            Offre.query
            .filter_by(user_id=current_user.id)
            .order_by(Offre.id.desc())
            .first()
        )
        if existing_offre:
            session['current_offre_id'] = existing_offre.id

    # 3. Chargement unique du template avec les deux variables attendues par votre HTML propre
    return render_template(
        "match/start_match.html", # Assurez-vous que le nom correspond à votre fichier de template
        existing_cv=existing_cv,
        existing_offre=existing_offre
    )



# Exécution de la comparaison 
@matching_bp.route("/run", methods=["POST"])
@login_required
def run_matching():
    print("Run exécétuer")
    # 1. Récupération des données JSON envoyées par le script AJAX
    data = request.get_json()

    cv_analyser_id = data.get("cv_id")  
    print("La valeur de cv_analyser_id est ,", cv_analyser_id)    # ID reçu depuis le front-end
    offre_analyser_id = data.get("offre_id")  # ID reçu depuis le front-end

    # Validation de la présence des IDs requis
    if not cv_analyser_id or not offre_analyser_id:
        return jsonify({
            "success": False,
            "message": "Les identifiants du CV et de l'offre sont obligatoires."
        }), 400

    try:
        # 2. Chargement des objets d'analyse depuis la base de données
        # Utilise les noms de modèles exacts de votre projet
        analyse_cv = CVAnalyser.query.get_or_404(cv_analyser_id)
        analyse_offre = OffreAnalyser.query.get_or_404(offre_analyser_id)

        # 3. Calcul algorithmique pur des compétences (Logique mathématique)
        metriques = calculer_matching(analyse_cv, analyse_offre)

        # 4. Enregistrement complet en BDD (inclut le user_id et les extra_skills)
        match_permanent = enregistrer_match_result(
            analyse_cv=analyse_cv, 
            analyse_offre=analyse_offre, 
            metriques=metriques, 
            user=current_user
        )

        # 5. Réponse JSON de succès lue par le script JavaScript pour la redirection
        return jsonify({
            "success": True,
            "data": {
                "id": match_permanent.id,
                "score": match_permanent.score
            }
        }), 200

    except Exception as e:
        # Capture toutes les erreurs inattendues (ex: problème d'écriture BDD)
        return jsonify({
            "success": False,
            "message": f"Une erreur est survenue lors du calcul du matching : {str(e)}"
        }), 500


# Afficher le resultat de la comparaison
@matching_bp.route("/rapport/<int:match_id>", methods=["GET"])
@login_required
def rapport(match_id):
    # Récupérer le résultat du matching ou renvoyer une erreur 404
    resultat = MatchResult.query.get_or_404(match_id)
    
    # Sécurité : S'assurer que le rapport appartient bien à l'utilisateur connecté
    if resultat.user_id != current_user.id:
        flash("Vous n'êtes pas autorisé à consulter ce rapport.", "danger")
        return redirect(url_for('global_bp.matching'))

    # Extraction des documents d'origine via les relations de clé étrangère
    analyse_cv = resultat.cv_analyser
    analyse_offre = resultat.offre_analyser
    
    # Accès aux objets parents (CV et Offre) pour récupérer les métadonnées (titres, fichiers)
    cv_brut = analyse_cv.cv if analyse_cv else None
    offre_brut = analyse_offre.offre if analyse_offre else None

    return render_template(
        "match/rapport.html",
        resultat=resultat,
        cv=cv_brut,
        offre=offre_brut
    )


@matching_bp.route("/recuperer-id-resultat/<int:offre_id>", methods=["GET"])
@login_required
def obtenir_id_matching(offre_id):
    """
    Route utilitaire permettant au catalogue de retrouver l'identifiant du rapport
    de matching associé à l'utilisateur connecté pour une offre donnée.
    """
    # Recherche du dernier résultat de matching pour ce couple utilisateur/offre
    resultat = MatchResult.query.join(MatchResult.offre_analyser)\
                                .filter(MatchResult.user_id == current_user.id, OffreAnalyser.offre_id == offre_id)\
                                .order_by(MatchResult.created_at.desc())\
                                .first()
    
    if not resultat:
        return jsonify({"success": False, "message": "Aucun rapport trouvé pour cette offre d'emploi."}), 404
        
    return jsonify({
        "success": True,
        "match_result_id": resultat.id
    }), 200

@matching_bp.route("/recuperer-details-json/<int:offre_id>", methods=["GET"])
@login_required
def obtenir_details_matching_json(offre_id):
    """
    Retourne les scores et listes de compétences au format JSON 
    pour affichage direct dans la fenêtre modale du candidat.
    """
    resultat = MatchResult.query.join(MatchResult.offre_analyser)\
                                .filter(MatchResult.user_id == current_user.id, OffreAnalyser.offre_id == offre_id)\
                                .order_by(MatchResult.created_at.desc())\
                                .first()
    
    if not resultat:
        return jsonify({"success": False, "message": "Aucun rapport trouvé."}), 404
        
    return jsonify({
        "success": True,
        "score": resultat.score,
        "matching_skills": resultat.matching_skills or [],
        "missing_skills": resultat.missing_skills or [],
        "extra_skills": resultat.extra_skills or [],
        "recommendation": resultat.recommendation or "Aucune synthèse disponible."
    }), 200


