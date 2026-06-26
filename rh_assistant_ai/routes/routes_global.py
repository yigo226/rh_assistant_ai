from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    flash,
    redirect,
    url_for
)

import os
from config.database import db

# Blueprint pour les routes liées aux CV
from flask import Blueprint
from flask_login import current_user, login_required
from config.decorateurs import role_required
from models.cv import CV

from services.cv_service import save_cv


global_bp = Blueprint(
    "global",
    __name__,
    url_prefix="/global"
)

from flask import request, render_template, redirect, url_for, session, flash, jsonify
from flask_login import login_required, current_user
from config.database import db
from models.cv import CV
from models.offre import Offre


@global_bp.route("/matching", methods=["GET", "POST"])
@login_required
def matching():
    # ============================================================
    # COMPORTEMENT SÉCURISÉ — MÉTHODE POST (Lancement du Matching)
    # ============================================================
    if request.method == "POST":
        # 1. Récupérer le CV unique de l'utilisateur
        existing_cv = CV.query.filter_by(user_id=current_user.id, est_actif=True).first()
        if not existing_cv or not existing_cv.analyse:
            flash("Action impossible : Votre CV n'est pas chargé ou analysé dans le système.", "danger")
            return redirect(url_for('global_bp.matching'))

        # 2. Récupérer l'offre active sélectionnée dans la session de l'utilisateur
        current_offre_id = session.get('current_offre_id')
        existing_offre = None
        
        if current_offre_id:
            existing_offre = Offre.query.get(current_offre_id)

        # Sécurité : Si aucune offre en session ou pas d'analyse rattachée
        if not existing_offre or not existing_offre.analyse:
            flash("Action impossible : Aucune offre d'emploi n'est sélectionnée ou analysée.", "danger")
            return redirect(url_for('global_bp.matching'))

        # 3. Récupération des données extraites (JSON) pour l'algorithme de comparaison
        donnees_cv = existing_cv.analyse       # Contient skills, diplomas, experiences du CV
        donnees_offre = existing_offre.analyse # Contient skills, diplomas, experiences de l'offre

        # ------------------------------------------------------------
        # Simulation de score (votre logique d'algorithme / IA prend le relais ici)
        # ICI : Insérez l'appel à votre algorithme ou IA de Matching
        # Exemple basique pour le rendu final :
        # score_matching = votre_fonction_matching(donnees_cv, donnees_offre)
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

    # 1. Récupérer le CV de référence unique de l'utilisateur
    existing_cv = CV.query.filter_by(user_id=current_user.id, est_actif=True).first()

    # 2. Récupérer l'offre active via la session (Plan A - Historique)
    existing_offre = None
    current_offre_id = session.get('current_offre_id')
    
    if current_offre_id:
        existing_offre = Offre.query.get(current_offre_id)
    
    # Sécurité Plan A : Si la session s'est vidée mais que l'utilisateur a un historique, 
    # on sélectionne automatiquement la toute dernière offre qu'il a analysée.
    if not existing_offre:
        existing_offre = Offre.query.filter_by(user_id=current_user.id).order_by(Offre.id.desc()).first()
        if existing_offre:
            session['current_offre_id'] = existing_offre.id

    # Rendu final du formulaire de comparaison
    return render_template(
        "upload.html",  # Remplacez par le nom exact de votre template global de matching
        existing_cv=existing_cv, 
        existing_offre=existing_offre
    )




