import os
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from config.database import db
from config.decorateurs import role_required
from models import Offre, OffreAnalyser, Departement
from models.utilisateur import Recruteur
from services.offre_service import save_offre

offre_bp = Blueprint(
    "offre",
    __name__,
    url_prefix="/offre"
)

@offre_bp.route("/creer", methods=["GET", "POST"])
@login_required
@role_required("recruteur")
def creer_offre():
    # Sécurité Établissement
    if not current_user.entreprise_id:
        flash("Vous devez être rattaché à une entreprise pour poster une offre.", "danger")
        return redirect(url_for("recruteur.dashboard"))

    if request.method == "POST":
        titre = request.form.get("titre")
        description = request.form.get("description")
        departement_id = request.form.get("departement_id")
        
        # Traitement de la date limite en UTC moderne avec fuseau horaire
        date_limite_raw = request.form.get("date_limite")
        if date_limite_raw:
            date_limite = datetime.fromisoformat(date_limite_raw).replace(tzinfo=timezone.utc)
        else:
            flash("La date limite est obligatoire", "danger")
            return redirect(request.url)
        
        # Récupération du fichier PDF
        file = request.files.get("fichier_pdf")
        if not file or file.filename == '':
            flash("Le fichier PDF officiel de l'offre est obligatoire", "danger")
            return redirect(request.url)

        # Validation de sécurité pour le département
        id_dep_selectionne = int(departement_id)
        dep_valide = Departement.query.filter_by(id=id_dep_selectionne, entreprise_id=current_user.entreprise_id).first()
        if not dep_valide:
            flash("Département sélectionné invalide.", "danger")
            return redirect(request.url)

        # 🟢 CORRECTION : Appel de save_offre débarrassé du paramètre nom_entreprise
        offre, synthese, infos = save_offre(
            fichier=file,
            recruteur=current_user,
            titre=titre,
            description=description,
            date_limite=date_limite,
            departement_id=id_dep_selectionne
        )
        
        # Archivage de l'ID en session pour les processus de matching automatiques
        session['current_offre_id'] = offre.id
        
        flash("L'offre a été créée, enregistrée et analysée par l'IA avec succès !", "success")
        return redirect(url_for("recruteur.dashboard"))

    # En méthode GET : Récupération des services de l'entreprise pour alimenter le select
    departements = Departement.query.filter_by(entreprise_id=current_user.entreprise_id).all()
    return render_template("offre/create.html", departements=departements)


# ============================================================
# 2. UPLOAD RAPIDE D'OFFRE (Via Requête AJAX du Matching)
# ============================================================
@offre_bp.route("/upload", methods=["POST"])
@login_required
def upload_offre():
    file = request.files.get("file") 

    if not file:
        return jsonify({"success": False, "message": "Aucun fichier sélectionné"}), 400

    # 🟢 CORRECTION ALIGNEMENT ARGUMENTS : Extraction de valeurs de secours pour éviter le crash à 7 paramètres
    # On utilise le nom du fichier nettoyé comme titre par défaut
    titre_secours = secure_filename(file.filename).rsplit('.', 1)[0]
    
    # On affecte arbitrairement le premier département de l'entreprise ou une date limite à J+30
    from datetime import timedelta
    date_limite_secours = datetime.now(timezone.utc) + timedelta(days=30)
    
    # Récupération sécurisée du département de l'entreprise
    premier_dep = Departement.query.filter_by(entreprise_id=current_user.entreprise_id).first()
    id_dep = premier_dep.id if premier_dep else 1
    nom_ent = current_user.entreprise.nom if current_user.entreprise else "Entreprise Externe"

    # Traiter et sauvegarder la nouvelle offre en lui injectant les 7 paramètres requis
    offre, synthese_criteres_offre, informations_extraites = save_offre(
        fichier=file,
        recruteur=current_user,
        titre=titre_secours,
        description="Fiche de poste importée via l'interface d'analyse rapide.",
        date_limite=date_limite_secours,
        departement_id=id_dep,
        nom_entreprise=nom_ent
    )

    session['current_offre_id'] = offre.id

    return jsonify({
        "success": True,
        "message": "Offre ajoutée à votre historique et analysée",
        "offre_id": offre.id,
        "analysis_id": synthese_criteres_offre.id,
        "filename": offre.nom_fichier
    })


# ============================================================
# 3. VISUALISATION DES COMPÉTENCES EXTRAITES PAR L'IA
# ============================================================
@offre_bp.route("/result/<int:analysis_id>")
@login_required
def view_result(analysis_id):
    # Récupérer les critères extraits ou renvoyer une erreur 404
    informations_extraites = OffreAnalyser.query.get_or_404(analysis_id)
    offre_utilisateur = informations_extraites.offre
    
    return render_template(
        "offre/result.html",
        offre_utilisateur=offre_utilisateur,
        informations_extraites=informations_extraites
    )


# ============================================================
# 4. ENVOI FLUIDE DU PDF (Pour la Modale Intégrée de l'Œil 👁️)
# ============================================================
@offre_bp.route("/pdf/<int:offre_id>")
@login_required
def voir_pdf(offre_id):
    offre = Offre.query.get_or_404(offre_id)

    # 🟢 SÉCURITÉ COLLABORATIVE : Un recruteur ne peut voir que les PDF de sa propre boîte
    if current_user.est_recruteur():
        if offre.recruteur.entreprise_id != current_user.entreprise_id:
            abort(403) # Interdit si l'offre appartient à une entreprise concurrente
            
    # Si le chemin du fichier n'existe pas physiquement sur le disque
    if not offre.chemin_fichier or not os.path.exists(offre.chemin_fichier):
        abort(404)

    # Envoi sécurisé du flux binaire interprétable directement par l'iframe HTML
    return send_file(
        offre.chemin_fichier,
        mimetype="application/pdf",
        as_attachment=False
    )

# ============================================================
# GRILLE DE QUESTIONS D'ENTRETIEN (DEPUIS LA BDD)
# ============================================================
import json
from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
# Importez vos modèles selon votre structure (ex: from models import Offre, QuestionEntretien)

@offre_bp.route("/questions_entretien", methods=["GET"])
@login_required
@role_required("recruteur")
def questions_entretien():
    # 1. Sécurité : Récupérer uniquement les offres de l'entreprise du recruteur connecté
    offres = Offre.query\
        .join(Recruteur)\
        .filter(Recruteur.entreprise_id == current_user.entreprise_id)\
        .all()
        
    # 2. Récupérer l'ID de l'offre sélectionnée dans l'URL (ex: /questions_entretien?offre_id=5)
    offre_id_arg = request.args.get("offre_id", type=int)
    
    offre_selectionnee = None
    questions_list = []

    if offre_id_arg:
        # Charger l'offre demandée
        offre_selectionnee = Offre.query.get(offre_id_arg)
        
        # Vérification de sécurité : l'offre appartient-elle bien à l'entreprise du recruteur ?
        if offre_selectionnee and offre_selectionnee.recruteur.entreprise_id == current_user.entreprise_id:
            
            # Récupérer l'enregistrement de la table questions_entretien lié à cette offre
            # (Utilise la relation back_populates='questions' définie dans votre modèle)
            question_record = offre_selectionnee.questions  # Peut retourner une liste ou un objet selon votre backref
            
            # Si la relation retourne une liste (cas standard), on prend le premier élément
            if isinstance(question_record, list) and len(question_record) > 0:
                question_record = question_record[0]
                
            if question_record and question_record.donnees_json:
                try:
                    # Décoder le texte JSON pour l'envoyer sous forme de dictionnaire/liste au template
                    questions_list = json.loads(question_record.donnees_json)
                except json.JSONDecodeError:
                    flash("Erreur lors de la lecture des questions (Format JSON invalide).", "danger")
        else:
            flash("Action non autorisée ou offre introuvable.", "danger")
            return redirect(url_for("offre.questions_entretien"))

    return render_template(
        "offre/questions_entretien.html",
        offres=offres,
        offre_selectionnee=offre_selectionnee,
        questions=questions_list
    )
