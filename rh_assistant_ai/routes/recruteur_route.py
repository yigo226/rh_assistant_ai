import os
from datetime import datetime, timezone
from config.database import db

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import login_required, current_user
from config.decorateurs import role_required

# Modèles typés et révisés
from models import Offre, Departement,  Candidature, LesRecrutEntreprise, MatchResult, CV, CVAnalyser
from models.entreprise_model  import Entreprise
from models.utilisateur import Recruteur,Candidat

recruteur_bp = Blueprint(
    "recruteur",
    __name__,
    url_prefix="/recruteur")

# ============================================================
# TABLEAU DE BORD (Vue Collaborative de l'Entreprise)
# ============================================================
@recruteur_bp.route("/dashboard")
@login_required
@role_required("recruteur")
def dashboard():
    # 🟢 SYNC : Charge TOUTES les offres de l'entreprise (visibles par tous les collègues RH)
    offres = (
        Offre.query
        .join(Recruteur)
        .filter(Recruteur.entreprise_id == current_user.entreprise_id)
        .order_by(Offre.date_creation.desc())
        .all()
    )

    departements = (
        Departement.query
        .filter_by(entreprise_id=current_user.entreprise_id)
        .all()
    )

    equipe = (
        Recruteur.query
        .filter_by(entreprise_id=current_user.entreprise_id)
        .all()
    )

    total_matchings = (
        Candidature.query
        .join(Offre)
        .join(Recruteur)
        .filter(Recruteur.entreprise_id == current_user.entreprise_id)
        .count()
    )

    total_employes = (
        LesRecrutEntreprise.query
        .join(Candidature)
        .join(Offre)
        .join(Departement)
        .filter(Departement.entreprise_id == current_user.entreprise_id)
        .count()
    )

    return render_template(
        "dashboardRecruteur.html",
        offres=offres,
        departements=departements,
        equipe=equipe,
        total_matchings=total_matchings,
        total_employes=total_employes
    )

# ============================================================
# SUIVI DES CANDIDATS (Trié par Score d'Adéquation)
# ============================================================
@recruteur_bp.route("/candidatListe/<int:offre_id>", methods=["GET"])
@login_required
@role_required("recruteur")
def candidat_liste(offre_id):
    offre = Offre.query.get_or_404(offre_id)
    
    # Sécurité collaborative : n'importe quel recruteur de la même boîte peut y accéder
    if offre.recruteur.entreprise_id != current_user.entreprise_id:
        flash("Accès refusé : Cette offre ne dépend pas de votre établissement.", "danger")
        return redirect(url_for("recruteur.dashboard"))

    # Récupération des candidatures liées à cette offre précise
    candidatures = Candidature.query.filter_by(offre_id=offre.id).all()

    # Tri manuel côté Python si votre propriété dynamique details_matching est appelée
    # (Ou via une jointure si vous préférez le SQL brut)
    try:
        candidatures.sort(key=lambda c: c.details_matching.score if c.details_matching else 0, reverse=True)
    except Exception:
        pass

    return render_template(
        "recruteur/candidat_liste.html", 
        offre=offre, 
        candidatures=candidatures
    )

# ============================================================
# TRAITEMENT DES STATUTS ET ARCHIVAGE SIRH (CDI/CDD/SALAIRE)
# ============================================================
@recruteur_bp.route("/update-statut/<int:candidature_id>", methods=["POST"])
@login_required
@role_required("recruteur")
def update_statut(candidature_id):
    candidature = Candidature.query.get_or_404(candidature_id)
    
    # Sécurité d'accès collaborative
    if candidature.offre.recruteur.entreprise_id != current_user.entreprise_id:
        flash("Action non autorisée.", "danger")
        return redirect(url_for("recruteur.dashboard"))

    nouveau_statut = request.form.get("nouveau_statut")
    valeurs_autorisees = ['a_letude', 'entretien', 'retenu', 'refuse']
    
    if nouveau_statut in valeurs_autorisees:
        candidature.statut = nouveau_statut
        
        # ============================================================
        # CAS A : PLANIFICATION D'UNE SESSION D'ENTRETIEN INDÉPENDANTE
        # ============================================================
        # ============================================================
        # CAS A : PLANIFICATION D'UNE SESSION D'ENTRETIEN INDÉPENDANTE
        # ============================================================
        if nouveau_statut == 'entretien':
            date_raw = request.form.get("date_entretien")
            heure_raw = request.form.get("heure_entretien")
            lieu = request.form.get("lieu_entretien", "À distance / En ligne")
            notes = request.form.get("notes_entretien", "Entretien de sélection")
            
            # 🟢 SÉCURITÉ ANTI-CRASH : On vérifie que les données du formulaire ne sont pas vides
            if not date_raw or not heure_raw:
                flash("Erreur : La date et l'heure de rendez-vous reçues sont vides. Vérifiez les champs HTML.", "danger")
                return redirect(url_for("recruteur.candidat_liste", offre_id=candidature.offre_id))
            
            from models import Entretien
            
            nouvelle_session = Entretien(
                candidature_id=candidature.id,
                date_rendezvous=datetime.strptime(date_raw, "%Y-%m-%d").date(),
                heure_rendezvous=datetime.strptime(heure_raw, "%H:%M").time(),
                lieu=lieu,
                notes=notes
            )
            db.session.add(nouvelle_session)
            flash(f"Une session d'entretien a été planifiée avec succès pour {candidature.candidat.nom}.", "success")

        # ============================================================
        # CAS B : VALIDATION FINALE D'EMBAUCHE (LesRecrutEntreprise)
        # ============================================================
        elif nouveau_statut == 'retenu':
            type_contrat = request.form.get("type_contrat", "CDI")
            salaire_raw = request.form.get("salaire_propose")
            date_debut_raw = request.form.get("date_debut")
            
            salaire = float(salaire_raw) if salaire_raw else None
            date_debut = datetime.strptime(date_debut_raw, "%Y-%m-%d").date() if date_debut_raw else datetime.now(timezone.utc).date()

            nouveau_recrutement = LesRecrutEntreprise(
                entreprise_id=current_user.entreprise_id,
                candidature_id=candidature.id,
                type_contrat=type_contrat,
                salaire_propose=salaire,
                date_debut=date_debut
            )
            db.session.add(nouveau_recrutement)
            flash(f"Félicitations ! {candidature.candidat.nom} a été recruté(e) sous contrat {type_contrat}.", "success")

        # Sauvegarde finale de toutes les modifications (Statut + Tables liées)
        db.session.commit()
        if nouveau_statut not in ['entretien', 'retenu']:
            flash("Le suivi de la candidature a été mis à jour avec succès !", "success")
            
    else:
        flash("Statut soumis invalide.", "danger")

    return redirect(url_for("recruteur.candidat_liste", offre_id=candidature.offre_id))

# ============================================================
# DÉTAILS INDIVIDUELS DE L'OFFRE
# ============================================================
@recruteur_bp.route("/offre/<int:offre_id>")
@login_required
@role_required("recruteur")
def detail_offre(offre_id):
    offre = Offre.query.get_or_404(offre_id)
    if offre.recruteur.entreprise_id != current_user.entreprise_id:
        flash("Accès refusé.", "danger")
        return redirect(url_for("recruteur.dashboard"))
        
    return render_template("detailOffre.html", offre=offre)


@recruteur_bp.route("/finaliser-recrutement/<int:candidature_id>", methods=["GET", "POST"])
@login_required
@role_required("recruteur")
def finaliser_recrutement(candidature_id):
    candidature = Candidature.query.get_or_404(candidature_id)
    
    # Sécurité collaborative : Vérifier que l'offre appartient bien à l'entreprise du recruteur
    if candidature.offre.recruteur.entreprise_id != current_user.entreprise_id:
        flash("Action non autorisée.", "danger")
        return redirect(url_for("recruteur.dashboard"))

    # 🟢 COMPORTEMENT A : ENREGISTREMENT DU CONTRAT (Méthode POST)
    if request.method == "POST":
        type_contrat = request.form.get("type_contrat")
        salaire_raw = request.form.get("salaire_propose")
        date_debut_raw = request.form.get("date_debut")

        # Validation de base des champs obligatoires
        if not type_contrat or not date_debut_raw:
            flash("Veuillez remplir tous les champs obligatoires (*).", "danger")
            return redirect(request.url)

        try:
            # 1. Conversion des données reçues du formulaire
            salaire = float(salaire_raw) if salaire_raw else None
            date_debut = datetime.strptime(date_debut_raw, "%Y-%m-%d").date()

            # 2. Création et liaison de la fiche de recrutement unique
            nouveau_recrutement = LesRecrutEntreprise(
                candidature_id=candidature.id,
                type_contrat=type_contrat,
                salaire_propose=salaire,
                date_debut=date_debut
            )
            
            # 3. Mise à jour officielle du statut de la candidature
            candidature.statut = "retenu"
            
            db.session.add(nouveau_recrutement)
            db.session.commit()
            
            flash(f"Félicitations ! Le recrutement de {candidature.candidat.nom} {candidature.candidat.prenom} a été enregistré avec succès.", "success")
            return redirect(url_for("recruteur.candidat_liste", offre_id=candidature.offre_id))

        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors de la création du contrat : {str(e)}", "danger")
            return redirect(request.url)

    # 🟢 COMPORTEMENT B : AFFICHAGE DU FORMULAIRE ADMINISTRATIF (Méthode GET)
    return render_template(
        "recruteur/finaliser_recrutement.html",
        candidature=candidature,
        candidat=candidature.candidat,
        offre=candidature.offre
    )

@recruteur_bp.route("/refuser-candidature/<int:candidature_id>", methods=["POST"])
@login_required
@role_required("recruteur")
def refuser_candidature(candidature_id):
    candidature = Candidature.query.get_or_404(candidature_id)
    
    # CORRECTION : On passe par offre.recruteur.entreprise_id
    if candidature.offre.recruteur.entreprise_id != current_user.entreprise_id:
        flash("Action non autorisée.", "danger")
        return redirect(url_for("recruteur.dashboard")) 
        
    candidature.statut = "refuse"
    db.session.commit()
    
    flash(f"La candidature de {candidature.candidat.nom} a été écartée.", "info")
    return redirect(url_for("recruteur.candidat_liste", offre_id=candidature.offre_id))

@recruteur_bp.route("/registre-recrutements", methods=["GET"])
@login_required
@role_required("recruteur")
def registre_recrutements():    
    # Jointure par étapes
    # On sélectionne les contrats validés dont l'offre d'emploi a été publiée 
    # par un recruteur appartenant à la même entreprise que l'utilisateur connecté.
    tous_les_recrutements = LesRecrutEntreprise.query\
        .join(Candidature)\
        .join(Offre)\
        .join(Recruteur, Offre.recruteur_id == Recruteur.id)\
        .filter(Recruteur.entreprise_id == current_user.entreprise_id)\
        .order_by(LesRecrutEntreprise.date_recrutement.desc())\
        .all()

    # Calcul de la masse salariale totale engagée
    masse_salariale = sum(r.salaire_propose for r in tous_les_recrutements if r.salaire_propose)

    return render_template(
        "recruteur/registre_recrutements.html",
        recrutements=tous_les_recrutements,
        total_recrutements=len(tous_les_recrutements),
        masse_salariale=masse_salariale
    )


def obtenir_classement_recrutement(id_de_loffre):
    """
    Retourne la liste de tous les candidats ayant postulé à une offre,
    classés par ordre décroissant de score de matching (IA).
    """
    # CORRECTION : Jointure correcte étape par étape à travers l'analyse du CV et de l'offre
    return Candidature.query.filter_by(offre_id=id_de_loffre)\
                            .join(CV)\
                            .join(CVAnalyser)\
                            .join(MatchResult, CVAnalyser.id == MatchResult.cv_analyser_id)\
                            .order_by(MatchResult.score.desc())\
                            .all()