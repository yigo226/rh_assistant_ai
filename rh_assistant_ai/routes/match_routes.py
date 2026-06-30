from flask import Blueprint, request, jsonify, render_template, session, flash, redirect, url_for
from flask_login import login_required, current_user
from models import CV, Offre, MatchResult, CVAnalyser, OffreAnalyser
from models.utilisateur import Candidat
from services.matching_service import calculer_matching, enregistrer_match_result

matching_bp = Blueprint(
    "matching",
    __name__,
    url_prefix="/matching"
)

# ============================================================
# 1. ÉCRAN D'ACCUEIL DU MATCHING (Sélection Catalogue & Dépôt)
# ============================================================
@matching_bp.route("/start_match", methods=["GET"])
@login_required
def start_match():
    # 🟢 SYNC : Recherche du CV unique ACTIF lié au Candidat connecté
    existing_cv = (
        CV.query
        .filter_by(candidat_id=current_user.id, est_actif=True)
        .first()
    )

    # Récupération de l'offre d'emploi active enregistrée en session
    existing_offre = None
    current_offre_id = session.get('current_offre_id')
    
    if current_offre_id:
        existing_offre = Offre.query.get(current_offre_id)
    
    # Sécurité Plan A : Si la session s'est vidée, on sélectionne la toute dernière offre publique
    if not existing_offre:
        existing_offre = (
            Offre.query
            .order_by(Offre.date_creation.desc())
            .first()
        )
        if existing_offre:
            session['current_offre_id'] = existing_offre.id

    # Chargement de la liste de toutes les offres pour alimenter votre sélecteur de catalogue
    offres_publiees = Offre.query.all()

    return render_template(
        "match/start_match.html", 
        existing_cv=existing_cv,
        existing_offre=existing_offre,
        offres_publiees=offres_publiees
    )


# ============================================================
# 2. EXECUTION DU MATCHING (Requête Asynchrone JSON)
# ============================================================
@matching_bp.route("/run", methods=["POST"])
@login_required
def run_matching():
    print("Run exécuté")
    data = request.get_json()

    cv_analyser_id = data.get("cv_id")  
    offre_analyser_id = data.get("offre_id")  

    if not cv_analyser_id or not offre_analyser_id:
        return jsonify({
            "success": False,
            "message": "Les identifiants du CV et de l'offre sont obligatoires."
        }), 400

    try:
        analyse_cv = CVAnalyser.query.get_or_404(cv_analyser_id)
        analyse_offre = OffreAnalyser.query.get_or_404(offre_analyser_id)

        # Calcul algorithmique
        metriques = calculer_matching(analyse_cv, analyse_offre)

        # Enregistrement dans la table match_results
        match_permanent = enregistrer_match_result(
            analyse_cv=analyse_cv, 
            analyse_offre=analyse_offre, 
            metriques=metriques, 
        )

        return jsonify({
            "success": True,
            "data": {
                "id": match_permanent.id,
                "score": match_permanent.score
            }
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Une erreur est survenue lors du calcul du matching : {str(e)}"
        }), 500


# ============================================================
# 3. COMPTE-RENDU VISUEL RAPPORT (Rapport d'adéquation global)
# ============================================================
@matching_bp.route("/rapport/<int:match_id>", methods=["GET"])
@login_required
def rapport(match_id):
    resultat = MatchResult.query.get_or_404(match_id)
    
    # 🟢 SÉCURITÉ : Remonte la chaîne pour vérifier si le rapport appartient bien au candidat connecté
    if resultat.cv_analyser.cv.candidat_id != current_user.id:
        flash("Vous n'êtes pas autorisé à consulter ce rapport.", "danger")
        return redirect(url_for('matching.start_match'))

    analyse_cv = resultat.cv_analyser
    analyse_offre = resultat.offre_analyser
    
    cv_brut = analyse_cv.cv if analyse_cv else None
    offre_brut = analyse_offre.offre if analyse_offre else None

    return render_template(
        "match/rapport.html",
        resultat=resultat,
        cv=cv_brut,
        offre=offre_brut
    )


# ============================================================
# 4. API UTILS : Récupérer l'ID du match pour une offre
# ============================================================
@matching_bp.route("/recuperer-id-resultat/<int:offre_id>", methods=["GET"])
@login_required
def obtenir_id_matching(offre_id):
    # 🟢 REQUÊTE SYNC : Filtre à travers l'arborescence de jointure pour cibler le candidat
    resultat = MatchResult.query\
        .join(CVAnalyser, MatchResult.cv_analyser_id == CVAnalyser.id)\
        .join(CV, CVAnalyser.cv_id == CV.id)\
        .filter(CV.candidat_id == current_user.id, MatchResult.offre_analyser_id == Offre.analyse)\
        .order_by(MatchResult.created_at.desc())\
        .first()
    
    if not resultat:
        return jsonify({"success": False, "message": "Aucun rapport trouvé pour cette offre d'emploi."}), 404
        
    return jsonify({
        "success": True,
        "match_result_id": resultat.id
    }), 200


# ============================================================
# 5. API UTILS : Extraire les métriques JSON (Pour le pop-up de détails)
# ============================================================
@matching_bp.route("/recuperer-details-json/<int:offre_id>", methods=["GET"])
@login_required
def obtenir_details_matching_json(offre_id):
    # 🟢 REQUÊTE SYNC : Liaison dynamique à l'aide des tables d'analyses de votre SIRH
    resultat = MatchResult.query\
        .join(CVAnalyser, MatchResult.cv_analyser_id == CVAnalyser.id)\
        .join(CV, CVAnalyser.cv_id == CV.id)\
        .join(OffreAnalyser, MatchResult.offre_analyser_id == OffreAnalyser.id)\
        .filter(CV.candidat_id == current_user.id, OffreAnalyser.offre_id == offre_id)\
        .order_by(MatchResult.created_at.desc())\
        .first()
    
    if not resultat:
        return jsonify({"success": False, "message": "Aucun rapport d'adéquation trouvé en base de données."}), 404
        
    return jsonify({
        "success": True,
        "score": resultat.score,
        "matching_skills": resultat.matching_skills or [],
        "missing_skills": resultat.missing_skills or [],
        "extra_skills": resultat.extra_skills or [],
        "recommendation": resultat.recommendation or "Aucune synthèse disponible pour le moment."
    }), 200
