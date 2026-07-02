from flask import Blueprint, request, jsonify, render_template, session, flash, redirect, url_for
from flask_login import login_required, current_user
from models import CV, Offre, MatchResult, CVAnalyser, OffreAnalyser
from models.utilisateur import Candidat
from services.matching_service import calculer_matching, enregistrer_match_result
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from flask_login import login_required, current_user
from config.database import db

# Importations unifiées de vos modèles et services francisés
from models import CV, Offre, MatchResult, CVAnalyser, OffreAnalyser
from services.matching_service import calculer_matching, enregistrer_match_result

matching_bp = Blueprint(
    "matching",
    __name__,
    url_prefix="/matching"
)

# ============================================================
# 🟢 ROUTE UNIFIÉE : AFFICHAGE (GET) ET CALCUL SYNCHRONE (POST)
# ============================================================
@matching_bp.route("/start_match", methods=["GET", "POST"])
@login_required
def start_match():
    
    # --------------------------------------------------------
    # COMPORTEMENT TRAITEMENT : MÉTHODE POST (Lancement du Match)
    # --------------------------------------------------------
    if request.method == "POST":
        # 1. Récupération des IDs envoyés par le formulaire traditionnel
        cv_id_form = request.form.get("cv_id")
        offre_id_form = request.form.get("offre_id")

        if not cv_id_form or not offre_id_form:
            flash("Action impossible : Les identifiants du CV et de l'offre sont requis.", "danger")
            return redirect(url_for("matching.start_match"))

        # 2. Récupération des objets physiques et de leurs analyses IA
        cv_physique = CV.query.get_or_404(int(cv_id_form))
        offre_physique = Offre.query.get_or_404(int(offre_id_form))

        analyse_cv = cv_physique.analyse
        analyse_offre = offre_physique.analyse

        if not analyse_cv or not analyse_offre:
            flash("Action impossible : Les analyses structurelles IA sont introuvables.", "danger")
            return redirect(url_for("matching.start_match"))

        # 3. Vérification de l'historique : si le match existe déjà, on ne réveille pas l'IA
        match_permanent = MatchResult.query.filter_by(
            cv_analyser_id=analyse_cv.id, 
            offre_analyser_id=analyse_offre.id
        ).first()

        # 4. Si non testé, calcul algorithmique et persistance en base de données
        if not match_permanent:
            try:
                metriques = calculer_matching(analyse_cv, analyse_offre)
                match_permanent = enregistrer_match_result(
                    analyse_cv=analyse_cv, 
                    analyse_offre=analyse_offre, 
                    metriques=metriques
                )
            except Exception as e:
                flash(f"Erreur lors de l'exécution de l'analyse comparative : {str(e)}", "danger")
                return redirect(url_for("matching.start_match"))

        # 5. Redirection immédiate vers l'URL fixe et propre du rapport
        return redirect(url_for("matching.rapport", match_id=match_permanent.id))

    # --------------------------------------------------------
    # COMPORTEMENT ENTRÉE : MÉTHODE GET (Affichage de l'interface)
    # --------------------------------------------------------
    # Interception d'une sélection rapide issue du catalogue candidat
    url_offre_id = request.args.get('select_offre_id')
    if url_offre_id:
        offre_selectionnee = Offre.query.get(url_offre_id)
        if offre_selectionnee:
            session['current_offre_id'] = offre_selectionnee.id
            flash(f"Offre « {offre_selectionnee.titre} » chargée pour la comparaison.", "success")

    # Recherche du CV unique ACTIF lié au Candidat connecté
    existing_cv = CV.query.filter_by(candidat_id=current_user.id, est_actif=True).first()

    # Récupération de l'offre d'emploi active enregistrée en session
    existing_offre = None
    current_offre_id = session.get('current_offre_id')
    
    if current_offre_id:
        existing_offre = Offre.query.get(current_offre_id)
    
    # Sécurité Plan A : Si la session s'est vidée, sélection de la toute dernière offre publique
    if not existing_offre:
        existing_offre = Offre.query.order_by(Offre.date_creation.desc()).first()
        if existing_offre:
            session['current_offre_id'] = existing_offre.id

    offres_publiees = Offre.query.all()

    # Rendu du formulaire (Votre fichier upload.html renommé ou configuré)
    return render_template(
        "upload.html", 
        existing_cv=existing_cv,
        existing_offre=existing_offre,
        offres_publiees=offres_publiees
    )


# ============================================================
# 3. COMPTE-RENDU VISUEL FIXE (Rapport d'adéquation global)
# ============================================================
@matching_bp.route("/rapport/<int:match_id>", methods=["GET"])
@login_required
def rapport(match_id):
    resultat = MatchResult.query.get_or_404(match_id)
    
    # Sécurité d'accès : Remonte la chaîne pour valider la propriété du dossier
    if resultat.cv_analyser.cv.candidat_id != current_user.id:
        abort(403)

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

# matching_bp = Blueprint(
#     "matching",
#     __name__,
#     url_prefix="/matching"
# )

# # ============================================================
# # 1. ÉCRAN D'ACCUEIL DU MATCHING (Sélection Catalogue & Dépôt)
# # ============================================================
# @matching_bp.route("/start_match", methods=["GET"])
# @login_required
# def start_match():
#     # 🟢 SYNC : Recherche du CV unique ACTIF lié au Candidat connecté
#     existing_cv = (
#         CV.query
#         .filter_by(candidat_id=current_user.id, est_actif=True)
#         .first()
#     )

#     # Récupération de l'offre d'emploi active enregistrée en session
#     existing_offre = None
#     current_offre_id = session.get('current_offre_id')
    
#     if current_offre_id:
#         existing_offre = Offre.query.get(current_offre_id)
    
#     # Sécurité Plan A : Si la session s'est vidée, on sélectionne la toute dernière offre publique
#     if not existing_offre:
#         existing_offre = (
#             Offre.query
#             .order_by(Offre.date_creation.desc())
#             .first()
#         )
#         if existing_offre:
#             session['current_offre_id'] = existing_offre.id

#     # Chargement de la liste de toutes les offres pour alimenter votre sélecteur de catalogue
#     offres_publiees = Offre.query.all()

#     return render_template(
#         "match/start_match.html", 
#         existing_cv=existing_cv,
#         existing_offre=existing_offre,
#         offres_publiees=offres_publiees
#     )


# # ============================================================
# # 2. EXECUTION DU MATCHING (Requête Asynchrone JSON)
# # ============================================================
# @matching_bp.route("/run", methods=["POST"])
# @login_required
# def run_matching():
#     print("Run exécuté")
#     data = request.get_json()

#     cv_analyser_id = data.get("cv_id")  
#     offre_analyser_id = data.get("offre_id")  

#     if not cv_analyser_id or not offre_analyser_id:
#         return jsonify({
#             "success": False,
#             "message": "Les identifiants du CV et de l'offre sont obligatoires."
#         }), 400

#     try:
#         analyse_cv = CVAnalyser.query.get_or_404(cv_analyser_id)
#         analyse_offre = OffreAnalyser.query.get_or_404(offre_analyser_id)

#         # Calcul algorithmique
#         metriques = calculer_matching(analyse_cv, analyse_offre)

#         # Enregistrement dans la table match_results
#         match_permanent = enregistrer_match_result(
#             analyse_cv=analyse_cv, 
#             analyse_offre=analyse_offre, 
#             metriques=metriques, 
#         )

#         return jsonify({
#             "success": True,
#             "data": {
#                 "id": match_permanent.id,
#                 "score": match_permanent.score
#             }
#         }), 200

#     except Exception as e:
#         return jsonify({
#             "success": False,
#             "message": f"Une erreur est survenue lors du calcul du matching : {str(e)}"
#         }), 500


# # ============================================================
# # 3. COMPTE-RENDU VISUEL RAPPORT (Rapport d'adéquation global)
# # ============================================================
# @matching_bp.route("/rapport/<int:match_id>", methods=["GET"])
# @login_required
# def rapport(match_id):
#     resultat = MatchResult.query.get_or_404(match_id)
    
#     # 🟢 SÉCURITÉ : Remonte la chaîne pour vérifier si le rapport appartient bien au candidat connecté
#     if resultat.cv_analyser.cv.candidat_id != current_user.id:
#         flash("Vous n'êtes pas autorisé à consulter ce rapport.", "danger")
#         return redirect(url_for('matching.start_match'))

#     analyse_cv = resultat.cv_analyser
#     analyse_offre = resultat.offre_analyser
    
#     cv_brut = analyse_cv.cv if analyse_cv else None
#     offre_brut = analyse_offre.offre if analyse_offre else None

#     return render_template(
#         "match/rapport.html",
#         resultat=resultat,
#         cv=cv_brut,
#         offre=offre_brut
#     )


# ============================================================
# 4. API UTILS : Récupérer l'ID du match pour une offre
# ============================================================
@matching_bp.route("/recuperer-id-resultat/<int:offre_id>", methods=["GET"])
@login_required
def obtenir_id_matching(offre_id):
    resultat = MatchResult.query\
        .join(CVAnalyser, MatchResult.cv_analyser_id == CVAnalyser.id)\
        .join(CV, CVAnalyser.cv_id == CV.id)\
        .filter(CV.candidat_id == current_user.id, MatchResult.offre_analyser_id == Offre.analyse)\
        .order_by(MatchResult.date_creation.desc())\
        .first() # 🟢 CORRECTION : date_creation au lieu de created_at
    
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
    resultat = MatchResult.query\
        .join(CVAnalyser, MatchResult.cv_analyser_id == CVAnalyser.id)\
        .join(CV, CVAnalyser.cv_id == CV.id)\
        .join(OffreAnalyser, MatchResult.offre_analyser_id == OffreAnalyser.id)\
        .filter(CV.candidat_id == current_user.id, OffreAnalyser.offre_id == offre_id)\
        .order_by(MatchResult.date_creation.desc())\
        .first() # 🟢 CORRECTION : date_creation au lieu de created_at
    
    if not resultat:
        return jsonify({"success": False, "message": "Aucun rapport d'adéquation trouvé en base de données."}), 404
    return jsonify({
        "success": True,
        "score": resultat.score,
        "recommendation": resultat.recommandation or "Aucune synthèse disponible.",
        
        # 1. Le bloc Compétences
        "matching_skills": resultat.competences_validees or [],
        "missing_skills": resultat.competences_manquantes or [],
        "extra_skills": resultat.competences_bonus or [],
        
        # 2. Le bloc Études & Diplômes (🟢 Ajouté à l'export API)
        "diplomes_valides": resultat.diplomes_valides or [],
        "diplomes_manquants": resultat.diplomes_manquants or [],
        
        # 3. Le bloc Expériences (🟢 Ajouté à l'export API)
        "experiences_validees": resultat.experiences_validees or [],
        "experiences_manquantes": resultat.experiences_manquantes or []
    }), 200

    # return jsonify({
    #     "success": True,
    #     "score": resultat.score,
    #     "matching_skills": resultat.competences_validees or [], # 🟢 Raccordement aux noms FR
    #     "missing_skills": resultat.competences_manquantes or [], # 🟢 Raccordement aux noms FR
    #     "extra_skills": resultat.competences_bonus or [],       # 🟢 Raccordement aux noms FR
    #     "recommendation": resultat.recommandation or "Aucune synthèse disponible." # 🟢 Raccordement aux noms FR
    # }), 200





# ============================================================
# 4. API UTILS : Récupérer l'ID du match pour une offre
# ============================================================
# @matching_bp.route("/recuperer-id-resultat/<int:offre_id>", methods=["GET"])
# @login_required
# def obtenir_id_matching(offre_id):
#     # 🟢 REQUÊTE SYNC : Filtre à travers l'arborescence de jointure pour cibler le candidat
#     resultat = MatchResult.query\
#         .join(CVAnalyser, MatchResult.cv_analyser_id == CVAnalyser.id)\
#         .join(CV, CVAnalyser.cv_id == CV.id)\
#         .filter(CV.candidat_id == current_user.id, MatchResult.offre_analyser_id == Offre.analyse)\
#         .order_by(MatchResult.created_at.desc())\
#         .first()
    
#     if not resultat:
#         return jsonify({"success": False, "message": "Aucun rapport trouvé pour cette offre d'emploi."}), 404
        
#     return jsonify({
#         "success": True,
#         "match_result_id": resultat.id
#     }), 200


# # ============================================================
# # 5. API UTILS : Extraire les métriques JSON (Pour le pop-up de détails)
# # ============================================================
# @matching_bp.route("/recuperer-details-json/<int:offre_id>", methods=["GET"])
# @login_required
# def obtenir_details_matching_json(offre_id):
#     # 🟢 REQUÊTE SYNC : Liaison dynamique à l'aide des tables d'analyses de votre SIRH
#     resultat = MatchResult.query\
#         .join(CVAnalyser, MatchResult.cv_analyser_id == CVAnalyser.id)\
#         .join(CV, CVAnalyser.cv_id == CV.id)\
#         .join(OffreAnalyser, MatchResult.offre_analyser_id == OffreAnalyser.id)\
#         .filter(CV.candidat_id == current_user.id, OffreAnalyser.offre_id == offre_id)\
#         .order_by(MatchResult.created_at.desc())\
#         .first()
    
#     if not resultat:
#         return jsonify({"success": False, "message": "Aucun rapport d'adéquation trouvé en base de données."}), 404
        
#     return jsonify({
#         "success": True,
#         "score": resultat.score,
#         "matching_skills": resultat.matching_skills or [],
#         "missing_skills": resultat.missing_skills or [],
#         "extra_skills": resultat.extra_skills or [],
#         "recommendation": resultat.recommendation or "Aucune synthèse disponible pour le moment."
#     }), 200
