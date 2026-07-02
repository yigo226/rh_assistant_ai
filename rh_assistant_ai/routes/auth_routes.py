from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import db

# Importation de la classe mère et des deux classes enfants exclusivités
from models.utilisateur import Utilisateur, Recruteur, Candidat

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ============================================================
# INSCRIPTION (Gère dynamiquement les Candidats et Recruteurs)
# ============================================================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        email = request.form.get("email")
        password = request.form.get("password")

        # Vérifier si l'email existe déjà
        utilisateur_existant = Utilisateur.query.filter_by(email=email).first()
        if utilisateur_existant:
            flash("Email déjà utilisé", "danger")
            return redirect(url_for("auth.register"))

        # Hachage du mot de passe
        hashed_password = generate_password_hash(password)

        # 🟢 SÉCURITÉ : Tout le monde s'inscrit en tant que "Candidat"
        nouveau_candidat = Candidat(
            nom=nom,
            prenom=prenom,
            email=email,
            mot_de_passe=hashed_password
        )

        db.session.add(nouveau_candidat)
        db.session.commit()

        flash("Votre compte candidat a été créé avec succès !", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

# ============================================================
# CONNEXION (Méthode GET — Affichage)
# ============================================================
@auth_bp.route("/login", methods=["GET"])
def login():
    return render_template("auth/login.html")


# ============================================================
# CONNEXION (Méthode POST — Traitement)
# ============================================================
@auth_bp.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")

    # Recherche globale sur la table parente 'utilisateurs'.
    # Grâce au polymorphisme, 'utilisateur' sera un objet Recruteur ou Candidat complet.
    utilisateur = Utilisateur.query.filter_by(email=email).first()

    # Vérification du mot de passe
    if utilisateur and check_password_hash(utilisateur.mot_de_passe, password):
        login_user(utilisateur)
        flash("Connexion réussie", "success")

        # Redirection intelligente selon la nature de l'objet (ou le rôle)
        if isinstance(utilisateur, Recruteur) or utilisateur.est_recruteur():
            return redirect(url_for('recruteur.dashboard'))
        else:
            return redirect(url_for('candidat.espace_candidat'))

    # 🟢 FIX SÉCURITÉ : La route de redirection exacte est auth.login (et non auth_bp.login)
    flash("Identifiants incorrects", "danger")
    return redirect(url_for("auth.login")) 


# ============================================================
# DÉCONNEXION
# ============================================================
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Déconnexion réussie", "success")
    return redirect(url_for("auth.login"))
