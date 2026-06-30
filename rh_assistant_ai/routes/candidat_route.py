import os
from datetime import datetime, timezone
from flask import Blueprint, request, render_template, flash, redirect, url_for, session, jsonify
from flask_login import current_user, login_required
from config.decorateurs import role_required
from config.database import db

# Importations des modèles mis à jour
from models import CV, Offre, Candidature, MatchResult, CVAnalyser, OffreAnalyser


candidat_bp = Blueprint(
    "candidat",
    __name__,
    url_prefix="/candidat"
)

# ============================================================
# 1. ESPACE CANDIDAT (Dashboard / Catalogue des Offres public)
# ============================================================
@candidat_bp.route("/dashboard", methods=["GET"])
@login_required
@role_required("candidat")
def espace_candidat():
    # 🟢 CORRECTION : Filtrage sur candidat_id au lieu de user_id
    cv_existant = CV.query.filter_by(candidat_id=current_user.id, est_actif=True).first()
    # 1. Récupération du filtre de recherche textuelle
    recherche = request.args.get('search', '').strip()
    
    # 2. Requête de filtrage sur le catalogue d'offres
    requete_offres = Offre.query
    if recherche:
        requete_offres = requete_offres.filter(
            Offre.titre.ilike(f"%{recherche}%") | 
            Offre.entreprise.ilike(f"%{recherche}%")
        )
    
    # Tri des annonces de la plus récente à la plus ancienne
    offres = requete_offres.order_by(Offre.date_creation.desc()).all()

    # 3. Récupération optimisée des scores via la chaîne relationnelle de la BDD
    # On remonte du MatchResult -> CVAnalyser -> CV pour cibler l'id du candidat connecté
    scores_deja_calcules = {}
    if cv_existant and cv_existant.analyse:
        matchings_utilisateur = MatchResult.query.filter_by(cv_analyser_id=cv_existant.analyse.id).all()
        
        # Création du dictionnaire {offre_id: score} lue instantanément par les cartes HTML
        for m in matchings_utilisateur:
            if m.offre_analyser:
                scores_deja_calcules[m.offre_analyser.offre_id] = m.score

    return render_template(
        "offre/ListeOffre.html",
        offres=offres,
        scores_deja_calcules=scores_deja_calcules,
        recherche=recherche,
        cv_existant=cv_existant # Variable renommée existant_cv pour s'aligner sur votre vue HTML
    )


# ============================================================
# 2. POSTULATION À UNE OFFRE (Workflow Intelligent avec Auto-Match)
# ============================================================
@candidat_bp.route("/postuler/<int:offre_id>", methods=["GET", "POST"])
@login_required
@role_required("candidat") # Sécurisé pour interdire aux recruteurs de postuler
def postuler_offre(offre_id):
    # 1. Vérifications de base (Offre existante et présence d'un CV Actif)
    offre = Offre.query.get_or_404(offre_id)
    cv_actif = CV.query.filter_by(candidat_id=current_user.id, est_actif=True).first()
    
    if not cv_actif:
        flash("Vous devez charger un CV actif dans votre espace avant de postuler.", "danger")
        return redirect(url_for("candidat.espace_candidat"))

    # 2. Récupération automatique des synthèses de l'extracteur IA
    analyse_cv = cv_actif.analyse
    analyse_offre = offre.analyse

    if not analyse_cv or not analyse_offre:
        flash("Action impossible : Les analyses structurelles du CV ou de l'offre sont introuvables.", "danger")
        return redirect(url_for("candidat.espace_candidat"))

    # Vérification de l'existence d'un calcul de score historique dans match_results
    from services.matching_service import calculer_matching, enregistrer_match_result
    match_existant = MatchResult.query.filter_by(
        cv_analyser_id=analyse_cv.id, 
        offre_analyser_id=analyse_offre.id
    ).first()
    
    # 🧠 INTÉGRATION IA : Si non testé, exécution transparente du matching à la volée avant envoi
    if not match_existant:
        try:
            metriques = calculer_matching(analyse_cv, analyse_offre)
            match_existant = enregistrer_match_result(
                analyse_cv=analyse_cv,  
                analyse_offre=analyse_offre, 
                metriques=metriques, 
            )
        except Exception as e:
            flash(f"L'assistant IA n'a pas pu évaluer votre profil pour ce poste : {str(e)}", "danger")
            return redirect(url_for("candidat.espace_candidat"))

    # 3. ENREGISTREMENT SÉCURISÉ DE LA CANDIDATURE CONFORME À LA RÉALITÉ MÉTIER
    # On utilise la liaison directe (candidat_id + offre_id + cv_id) que nous avons programmée
    deja_postule = Candidature.query.filter_by(
        candidat_id=current_user.id, 
        offre_id=offre.id
    ).first()
    
    if deja_postule:
        flash("Vous avez déjà déposé votre candidature pour ce poste.", "warning")
        return redirect(url_for("candidat.espace_candidat"))

    # Écriture définitive de la postulation en base de données
    nouvelle_candidature = Candidature(
        candidat_id=current_user.id, 
        offre_id=offre.id, 
        cv_id=cv_actif.id, 
        statut="a_letude"
    )
    db.session.add(nouvelle_candidature)
    db.session.commit()

    flash(f"Votre candidature pour « {offre.titre} » a été transmise avec succès après analyse de conformité !", "success")
    return redirect(url_for("candidat.espace_candidat"))
