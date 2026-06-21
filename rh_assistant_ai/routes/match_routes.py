from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.cv_analyser import CVAnalyser
from models.offre_analyser import OffreAnalyser
from services.matching_service import calculer_matching, enregistrer_match_result
from flask import render_template, session
from models.cv import CV
from models.offre import Offre


matching_bp = Blueprint(
    "matching",
    __name__,
    url_prefix="/matching"
)


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


# @matching_bp.route("/run", methods=["POST"])
# @login_required
# def run_matching():

#     data = request.get_json()

#     cv_id = data.get("cv_id")
#     offre_id = data.get("offre_id")

#     if not cv_id or not offre_id:
#         return jsonify({
#             "success": False,
#             "message": "cv_id et offre_id sont obligatoires."
#         }), 400

#     try:

#         result = calculer_matching(
#             cv_id=cv_id,
#             offre_id=offre_id,
#             user_id=current_user.id
#         )

#         return jsonify({
#             "success": True,
#             "data": result
#         }), 200

#     except Exception as e:

#         return jsonify({
#             "success": False,
#             "message": str(e)
#         }), 500
    
# Note: Le résultat retourné par calculer_matching est déjà un dict prêt à être JSONifié,
