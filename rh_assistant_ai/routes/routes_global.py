import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import login_required, current_user
from config.database import db

# Importations des modèles mis à jour
from models import CV, Offre

global_bp = Blueprint(
    "global",
    __name__,
    url_prefix="/global"
)

@global_bp.route("/matching", methods=["GET", "POST"])
@login_required
def matching():
    print("Call matching route")
    
    # ============================================================
    # COMPORTEMENT SÉCURISÉ — MÉTHODE POST (Lancement du Matching)
    # ============================================================
    if request.method == "POST":
        # 1. Récupérer le CV unique de l'utilisateur connecté
        # 🟢 CORRECTION : Utilisation de la colonne candidat_id
        existing_cv = CV.query.filter_by(candidat_id=current_user.id, est_actif=True).first()
        if not existing_cv or not existing_cv.analyse:
            flash("Action impossible : Votre CV n'est pas chargé ou analysé dans le système.", "danger")
            return redirect(url_for('global.matching'))

        # 2. Récupérer l'offre active sélectionnée dans la session de l'utilisateur
        current_offre_id = session.get('current_offre_id')
        existing_offre = None
        
        if current_offre_id:
            existing_offre = Offre.query.get(current_offre_id)

        # Sécurité : Si aucune offre en session ou pas d'analyse rattachée
        if not existing_offre or not existing_offre.analyse:
            flash("Action impossible : Aucune offre d'emploi n'est sélectionnée ou analysée.", "danger")
            return redirect(url_for('global.matching'))

        # 3. Récupération des données extraites (JSON) pour l'algorithme de comparaison
        donnees_cv = existing_cv.analyse       # Contient skills, diplomas, experiences du CV
        donnees_offre = existing_offre.analyse # Contient skills, diplomas, experiences de l'offre

        # ------------------------------------------------------------
        # Simulation de score (votre logique d'algorithme / IA prend le relais ici)
        # ------------------------------------------------------------
        score_matching = 85 # Score de simulation pour l'exemple

        # Redirection vers la page de rapport global finale
        return render_template(
            "matching/rapport.html", 
            cv=existing_cv, 
            offre=existing_offre,
            score=score_matching
        )

    # ============================================================
    # COMPORTEMENT ENTRÉE — MÉTHODE GET (Affichage de l'interface)
    # ============================================================

    # 1. INTERCEPTION DE L'OFFRE SÉLECTIONNÉE DEPUIS L'ESPACE CANDIDAT
    url_offre_id = request.args.get('select_offre_id')
    if url_offre_id:
        # On vérifie que l'offre existe bien dans le catalogue public
        offre_selectionnee = Offre.query.get(url_offre_id)
        if offre_selectionnee:
            # On écrase l'offre en session pour faire de celle-ci l'offre active
            session['current_offre_id'] = offre_selectionnee.id
            flash(f"Offre « {offre_selectionnee.titre} » chargée avec succès pour la comparaison.", "success")

    # 2. Récupérer le CV de référence unique de l'utilisateur
    # 🟢 CORRECTION : Utilisation de la colonne candidat_id
    existing_cv = CV.query.filter_by(candidat_id=current_user.id, est_actif=True).first()

    # 3. Récupérer l'offre active via la session (Plan A - Historique)
    existing_offre = None
    current_offre_id = session.get('current_offre_id')
    
    if current_offre_id:
        existing_offre = Offre.query.get(current_offre_id)
    
    # 🟢 SÉCURITÉ PLAN A CORRIGÉE : Si la session est vide, 
    # on charge simplement la toute dernière offre générale du catalogue public
    if not existing_offre:
        existing_offre = Offre.query.order_by(Offre.date_creation.desc()).first()
        if existing_offre:
            session['current_offre_id'] = existing_offre.id

    # 4. Rendu final du formulaire de comparaison avec le catalogue complet des offres publiées
    offres_publiees = Offre.query.all()
    return render_template(
        "upload.html",  
        existing_cv=existing_cv, 
        existing_offre=existing_offre,
        offres_publiees=offres_publiees
    )
