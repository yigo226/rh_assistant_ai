import os

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    jsonify,
)

from flask_login import (
    login_required,
    current_user
)

from werkzeug.utils import secure_filename

from config.database import db
from config.decorateurs import role_required
from models.offre import Offre

from werkzeug.utils import secure_filename
from models.offre_analyser import OffreAnalyser
from services.offre_service import analyseur_texte_extrait, save_offre
from models.entreprise_model import Departement
from services.file_service import extract_text 

import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required



offre_bp = Blueprint(
    "offre",
    __name__,
    url_prefix="/offre"
)
import os
from datetime import datetime, timezone
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

@offre_bp.route("/creer", methods=["GET", "POST"])
@login_required
@role_required("recruteur")
def creer_offre():
    # Sécurité : On vérifie immédiatement que le recruteur a bien une entreprise associée
    if not current_user.entreprise_id:
        flash("Vous devez être rattaché à une entreprise pour poster une offre.", "danger")
        return redirect(url_for("recruteur.dashboard"))

    if request.method == "POST":
        titre = request.form.get("titre")
        description = request.form.get("description")
        departement_id = request.form.get("departement_id")
        
        # 1. Conversion de la date limite reçue du HTML (input type="datetime-local" ou "date")
        # On ajoute impérativement l'information du fuseau horaire UTC pour éviter le conflit
        date_limite_raw = request.form.get("date_limite")
        if date_limite_raw:
            # datetime.fromisoformat convertit la chaîne, puis .replace(tzinfo=timezone.utc) la rend "Aware"
            date_limite = datetime.fromisoformat(date_limite_raw).replace(tzinfo=timezone.utc)
        else:
            flash("La date limite est obligatoire", "danger")
            return redirect(request.url)
        
        # Gestion du fichier PDF
        file = request.files.get("fichier_pdf")
        if file and file.filename != '':
            nom_fichier = secure_filename(file.filename)
            # Bonne pratique : s'assurer que le dossier existe sur le serveur
            os.makedirs("static/uploads/offres", exist_ok=True)
            chemin_fichier = os.path.join("static/uploads/offres", nom_fichier)
            file.save(chemin_fichier)
            contenu_texte = "Texte extrait du PDF..." # Votre logique d'extraction
        else:
            flash("Le fichier PDF est obligatoire", "danger")
            return redirect(request.url)

        # 2. Récupération automatique du nom de l'entreprise via la relation de l'utilisateur connecté
        nom_entreprise = current_user.entreprise.nom

        # 3. Validation de sécurité pour le département
        # On s'assure que le département choisi appartient bien à l'entreprise du recruteur connecté
        id_dep_selectionne = int(departement_id)
        dep_valide = Departement.query.filter_by(id=id_dep_selectionne, entreprise_id=current_user.entreprise_id).first()
        
        if not dep_valide:
            flash("Département sélectionné invalide.", "danger")
            return redirect(request.url)

        # Création de l'offre
        nouvelle_offre = Offre(
            titre=titre,
            entreprise=nom_entreprise,
            description=description,
            nom_fichier=nom_fichier,
            chemin_fichier=chemin_fichier,
            contenu_texte=contenu_texte,
            date_limite=date_limite,       # Désormais synchronisé en UTC !
            user_id=current_user.id,
            departement_id=id_dep_selectionne
        )
        
        db.session.add(nouvelle_offre)
        db.session.commit()
        
        flash("L'offre a été créée avec succès !", "success")
        return redirect(url_for("recruteur.dashboard"))

    # En méthode GET : Récupération des départements liés uniquement à l'entreprise du recruteur
    departements = Departement.query.filter_by(entreprise_id=current_user.entreprise_id).all()
    
    return render_template("offre/create.html", departements=departements)


@offre_bp.route("/upload", methods=["POST"])
@login_required
def upload_offre():
    file = request.files.get("file") 

    if not file:
        return jsonify({"success": False, "message": "Aucun fichier sélectionné"}), 400

    # Chaque upload crée une nouvelle entrée indépendante dans l'historique de l'utilisateur
    
    # Traiter et sauvegarder la nouvelle offre
    offre, synthese_criteres_offre, informations_extraites = save_offre(file, current_user)

    # On stocke l'ID de cette offre précise en session pour savoir sur laquelle 
    # l'utilisateur travaille actuellement
    session['current_offre_id'] = offre.id

    return jsonify({
        "success": True,
        "message": "Offre ajoutée à votre historique et analysée",
        "offre_id": offre.id,
        "analysis_id": synthese_criteres_offre.id,
        "filename": offre.nom_fichier
    })

# ❌ ici on SUPPRIME L'ANCIENNE OFFRE 

# @offre_bp.route("/upload", methods=["GET", "POST"])
# @login_required
# def upload_offre():
#     # 1. Rechercher si l'utilisateur a déjà une offre enregistrée
#     existing_offre = Offre.query.filter_by(user_id=current_user.id).first()

#     # Récupération du fichier via la clé définie dans le script JS du template
#     file = request.files.get("file") 

#     if not file:
#         return jsonify({
#             "success": False,
#             "message": "Aucun fichier sélectionné"
#         }), 400

#     # 2. Nettoyer l'ancienne offre et son fichier physique si elle existe
#     if existing_offre:
#         if existing_offre.chemin_fichier and os.path.exists(existing_offre.chemin_fichier):
#             try:
#                 os.remove(existing_offre.chemin_fichier)
#             except Exception as e:
#                 print(f"Erreur lors de la suppression du fichier physique : {e}")

#         db.session.delete(existing_offre)
#         db.session.commit()
    
#     # 3. Traiter et sauvegarder la nouvelle offre
#     # Aligné sur le triplet retourné par votre logique (Objet, Analyse_Objet, Données_brutes)
#     offre, synthese_criteres_offre, informations_extraites = save_offre(file, current_user)

#     print("type synthese_criteres_offre dans offre_route :", type(synthese_criteres_offre))
#     print(f"ID Analyse Offre : {synthese_criteres_offre.id}")
#     print("Fin d'affichage du type synthese_criteres_offre dans offre_route")

#     # 4. Retourner la réponse JSON attendue par le script AJAX du formulaire
#     return jsonify({
#         "success": True,
#         "message": "Offre analysée avec succès dans le système",
#         "offre_id": offre.id,
#         "analysis_id": synthese_criteres_offre.id,
#         "filename": offre.nom_fichier
#     })


@offre_bp.route("/result/<int:analysis_id>")
@login_required
def view_result(analysis_id):
    # Récupérer les critères extraits de l'offre ou renvoyer une erreur 404
    informations_extraites = OffreAnalyser.query.get_or_404(analysis_id)
    print("Le contenu de informations_extraites dans offre_route : ", informations_extraites)

    # Accès à l'offre parente via la relation back_populates du modèle
    offre_utilisateur = informations_extraites.offre
    print("Le contenu de offre_utilisateur dans offre_route : ", offre_utilisateur)
    
    print(type(informations_extraites.skills))
    print(informations_extraites.skills)
    return render_template(
        "offre/result.html",
        offre_utilisateur=offre_utilisateur,
        informations_extraites=informations_extraites
    )


