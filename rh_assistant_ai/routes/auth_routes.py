from flask import Blueprint
auth_bp = Blueprint( 
    "auth", 
    __name__, 
    url_prefix="/auth" )
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from flask_login import login_required
from werkzeug.security import (generate_password_hash)
from config.database import db
from models.user import User
from werkzeug.security import (check_password_hash)
from flask_login import ( login_user )
from flask_login import logout_user


# inscription
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        email = request.form.get("email")
        password = request.form.get("password")

        # Vérifier si email existe
        user = User.query.filter_by(
            email=email
        ).first()

        if user:
            flash(
                "Email déjà utilisé",
                "danger"
            )
            return redirect(
                url_for("auth.register")
            )

        # Hash du mot de passe
        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            nom=nom,
            prenom=prenom,
            email=email,
            mot_de_passe=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash(
            "Compte créé avec succès",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/register.html"
    )


# Connexion
# @auth_bp.route("/login", methods=["GET", "POST"])
# def login():

#     if request.method == "POST":

#         email = request.form.get("email")
#         password = request.form.get("password")

#         user = User.query.filter_by(
#             email=email
#         ).first()

#         if user and check_password_hash(
#             user.mot_de_passe,
#             password
#         ):
        
#             login_user(user)

#             flash(
#                 "Connexion réussie",
#                 "success"
#             )

#             return redirect(
#                 url_for("home")
#             )

#         flash(
#             "Identifiants incorrects",
#             "danger"
#         )

#     return render_template(
#         "auth/login.html"
#     )

# 1. Affichage du formulaire de connexion (Méthode GET)
@auth_bp.route("/login", methods=["GET"])
def login():
    return render_template("auth/login.html")


# 2. Traitement des données du formulaire (Méthode POST)
@auth_bp.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")

    # Recherche de l'utilisateur
    user = User.query.filter_by(email=email).first()

    # Vérification du mot de passe
    if user and check_password_hash(user.mot_de_passe, password):
        login_user(user)
        flash("Connexion réussie", "success")

        # --- Redirection intelligente selon le profil ---
        if user.est_recruteur():
            #return redirect(url_for('recruteur_bp.liste_offres'))
            return redirect(url_for('recruteur.dashboard'))  # Redirection vers la page d'accueil pour les recruteurs
        else:
            return redirect(url_for('home'))
        # ------------------------------------------------

    # Si les identifiants sont incorrects
    flash("Identifiants incorrects", "danger")
    return redirect(url_for("auth_bp.login")) 

# Déconnexion
@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Déconnexion réussie",
        "success"
    )
 
 
    return redirect(
        url_for("auth.login")
    )

