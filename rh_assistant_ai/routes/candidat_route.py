
import os
from config.database import db

# Blueprint pour les routes liées aux CV
from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import current_user, login_required
from config.decorateurs import role_required
from models.offre import Offre
from models.cv import CV
from models.candidature import Candidature, LesRecrutEntreprise
from models.offre_analyser import OffreAnalyser
from services.cv_service import save_cv
from models.match_result import MatchResult
from services.matching_service import calculer_matching, enregistrer_match_result
from datetime import datetime, timezone

candidat_bp = Blueprint(
    "candidat",
    __name__,
    url_prefix="/candidat"
)

@candidat_bp.route("/dashboard")
@login_required
@role_required("candidat")
def espace_candidat():

    cv_existant = CV.query.filter_by(user_id=current_user.id, est_actif=True).first()

    # 1. Récupération du filtre de recherche (si l'utilisateur tape un mot-clé)
    recherche = request.args.get('search', '').strip()
    
    # 2. Requête de base pour récupérer les offres
    requete_offres = Offre.query
    if recherche:
        requete_offres = requete_offres.filter(Offre.titre.ilike(f"%{recherche}%") | Offre.entreprise.ilike(f"%{recherche}%"))
    
    # Récupérer les offres triées par la plus récente
    offres = requete_offres.order_by(Offre.date_creation.desc()).all()

    # 3. Récupérer les matchings passés du candidat pour afficher les scores sur les cartes
    matchings_utilisateur = MatchResult.query.filter_by(user_id=current_user.id).all()
    
    # Créer un dictionnaire {offre_id: score} pour une recherche ultra-rapide dans le template Jinja
    scores_deja_calcules = {m.offre_analyser.offre_id: m.score for m in matchings_utilisateur if m.offre_analyser}

    return render_template(
        "offre/ListeOffre.html",
        offres=offres,
        scores_deja_calcules=scores_deja_calcules,
        recherche=recherche,
        cv_existant=cv_existant
    )

@candidat_bp.route("/postuler/<int:offre_id>", methods=["GET", "POST"])
@login_required
def postuler_offre(offre_id):
    # 1. Vérifications de base (Offre et CV Actif)
    offre = Offre.query.get_or_404(offre_id)
    cv_actif = CV.query.filter_by(user_id=current_user.id, est_actif=True).first()
    
    if not cv_actif:
        flash("Vous devez charger un CV actif dans votre espace avant de postuler.", "danger")
        return redirect(url_for("candidat.espace_candidat"))

    # 2. 🧠 INTEGRATION DU MATCHING AUTOMATIQUE TRANSPARENT (CORRIGÉ)
    # Récupération des analyses structurales (skills, diplomas, etc.) rattachées aux objets
    analyse_cv = cv_actif.analyse
    analyse_offre = offre.analyse

    if not analyse_cv or not analyse_offre:
        flash("Action impossible : Les analyses IA du CV ou de l'offre sont introuvables.", "danger")
        return redirect(url_for("candidat.espace_candidat"))

    # Requête corrigée sur les vrais noms de colonnes SQL de la table match_results
    match_existant = MatchResult.query.filter_by(
        cv_analyser_id=analyse_cv.id,
        offre_analyser_id=analyse_offre.id
    ).first()
    
    # Si aucun enregistrement n'existe, l'IA exécute le matching à la volée
    if not match_existant:
        try:
            # Appel direct de vos deux fonctions de calcul mathématique et d'écriture en BDD
            metriques = calculer_matching(analyse_cv, analyse_offre)
            match_existant = enregistrer_match_result(
                analyse_cv=analyse_cv, 
                analyse_offre=analyse_offre, 
                metriques=metriques, 
                user=current_user
            )
        except Exception as e:
            flash(f"L'assistant IA n'a pas pu évaluer votre profil pour ce poste : {str(e)}", "danger")
            return redirect(url_for("candidat.espace_candidat"))

    # 3. TRAITEMENT DE LA CANDIDATURE
    # Vérification si le candidat n'a pas déjà postulé à cette offre
    deja_postule = Candidature.query.filter_by(user_id=current_user.id, offre_id=offre.id).first()
    if deja_postule:
        flash("Vous avez déjà déposé votre candidature pour ce poste.", "warning")
        return redirect(url_for("candidat.espace_candidat"))

    # Enregistrement final de la candidature liée au MatchResult ID stable
    nouvelle_candidature = Candidature(
        user_id=current_user.id,
        offre_id=offre.id,
        match_result_id=match_existant.id, # Injecté de manière transparente !
    )
    
    db.session.add(nouvelle_candidature)
    db.session.commit()

    flash(f"Votre candidature pour « {offre.titre} » a été transmise avec succès après analyse de conformité !", "success")
    return redirect(url_for("candidat.espace_candidat"))

@candidat_bp.route("/candidatListe/<int:offre_id>", methods=["GET"])
@login_required
@role_required("recruteur")
def candidat_liste(offre_id):
    # 1. Récupération de l'offre en s'assurant qu'elle appartient à la même entreprise
    offre = Offre.query.get_or_404(offre_id)
    if offre.user.entreprise_id != current_user.entreprise_id:
        flash("Accès refusé : Cette offre ne dépend pas de votre établissement.", "danger")
        return redirect(url_for("recruteur.dashboard"))

    # 2. Récupération des candidatures triées par score de matching décroissant (le meilleur en premier)
    # On fait une jointure avec MatchResult pour obtenir le score et trier directement [3]
    candidatures = Candidature.query.filter_by(offre_id=offre.id)\
        .join(MatchResult, Candidature.match_result_id == MatchResult.id)\
        .order_by(MatchResult.score.desc()).all()

    return render_template(
        "candidat_liste.html", 
        offre=offre, 
        candidatures=candidatures
    )

@candidat_bp.route("/update-statut/<int:candidature_id>", methods=["POST"])
@login_required
@role_required("recruteur")
def update_statut(candidature_id):
    candidature = Candidature.query.get_or_404(candidature_id)
    
    # Sécurité d'accès
    if candidature.offre.user.entreprise_id != current_user.entreprise_id:
        flash("Action non autorisée.", "danger")
        return redirect(url_for("recruteur.dashboard"))

    # Récupération de la nouvelle valeur soumise par le select HTML
    nouveau_statut = request.form.get("nouveau_statut")
    valeurs_autorisees = ['a_letude', 'entretien', 'retenu', 'refuse']
    
    if nouveau_statut in valeurs_autorisees:
        candidature.statut = nouveau_statut
        db.session.commit()
        flash(f"Le statut de {candidature.candidat.nom} a été mis à jour !", "success")
    else:
        flash("Statut soumis invalide.", "danger")

    return redirect(url_for("recruteur.candidat_liste", offre_id=candidature.offre_id))


@candidat_bp.route("/avancer-statut/<int:candidature_id>", methods=["POST"])
@login_required
@role_required("recruteur")
def avancer_statut(candidature_id):
    candidature = Candidature.query.get_or_404(candidature_id)
    
    # Sécurité d'accès entreprise
    if candidature.offre.user.entreprise_id != current_user.entreprise_id:
        flash("Action non autorisée.", "danger")
        return redirect(url_for("recruteur.dashboard"))

    # CAS 1 : Passage du dossier en Entretien
    if candidature.statut == "a_letude":
        candidature.statut = "entretien"
        db.session.commit()
        flash(f"Un entretien a été planifié avec {candidature.candidat.nom}.", "success")
        
    # CAS 2 : Validation Finale avec collecte des détails du contrat
    elif candidature.statut == "entretien":
        candidature.statut = "retenu"
        
        # Récupération des données du formulaire de la modale
        type_contrat = request.form.get("type_contrat")
        salaire_raw = request.form.get("salaire_propose")
        date_debut_raw = request.form.get("date_debut")
        
        # Conversions sécurisées
        salaire = float(salaire_raw) if salaire_raw else None
        date_debut = datetime.strptime(date_debut_raw, "%Y-%m-%d").date() if date_debut_raw else datetime.now(timezone.utc).date()

        # Insertion complète dans le registre
        nouveau_recrutement = LesRecrutEntreprise(
            entreprise_id=current_user.entreprise_id,
            offre_id=candidature.offre_id,
            candidat_id=candidature.user_id,
            match_result_id=candidature.match_result_id,
            type_contrat=type_contrat,
            salaire_propose=salaire,
            date_debut=date_debut
        )
        db.session.add(nouveau_recrutement)
        db.session.commit()
        
        flash(f"Félicitations ! {candidature.candidat.nom} a été recruté(e) sous contrat {type_contrat}.", "success")

    return redirect(url_for("recruteur.candidat_liste", offre_id=candidature.offre_id))

@candidat_bp.route("/refuser-candidature/<int:candidature_id>", methods=["POST"])
@login_required
@role_required("recruteur")
def refuser_candidature(candidature_id):
    candidature = Candidature.query.get_or_404(candidature_id)
    if candidature.offre.user.entreprise_id != current_user.entreprise_id:
        return redirect(url_for("recruteur.dashboard"))
        
    candidature.statut = "refuse"
    db.session.commit()
    flash(f"La candidature de {candidature.candidat.nom} a été écartée.", "info")
    return redirect(url_for("recruteur.candidat_liste", offre_id=candidature.offre_id))

def obtenir_classement_recrutement(id_de_loffre):
    """
    Retourne la liste de tous les candidats ayant postulé à une offre,
    classés par ordre décroissant de score de matching (IA).
    """
    return Candidature.query.join(Candidature.offre_analyse)\
                            .filter(OffreAnalyser.offre_id == id_de_loffre)\
                            .order_by(Candidature.score.desc())\
                            .all()