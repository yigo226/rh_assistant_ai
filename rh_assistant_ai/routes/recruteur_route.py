
import os
from config.database import db

# Blueprint pour les routes liées aux CV
from flask import Blueprint, render_template
from flask_login import current_user, login_required
from config.decorateurs import role_required
from flask import request, render_template, redirect, url_for, session, flash, jsonify
from flask_login import login_required, current_user
from models.offre import Offre
from models.entreprise_model import Departement
from models.user import User
from models.match_result import MatchResult
from services.cv_service import save_cv


recruteur_bp = Blueprint(
    "recruteur",
    __name__,
    url_prefix="/recruteur"
)

# poster un offre d'emploi
# charger les offres lier à son entreprise
# Validation des candidats pour qu'il deviennent des employes

@recruteur_bp.route("/dashboard")
@login_required
@role_required("recruteur")
def dashboard():

    offres = (
        Offre.query
        .filter_by(user_id=current_user.id)
        .order_by(Offre.date_creation.desc())
        .all()
    )

    departements = (
        Departement.query
        .filter_by(
            entreprise_id=current_user.entreprise_id
        )
        .all()
    )

    equipe = (
        User.query
        .filter_by(
            entreprise_id=current_user.entreprise_id
        )
        .all()
    )

    # total_matchings = (
    #     MatchResult.query
    #     .join(Offre)
    #     .filter(
    #         Offre.user_id == current_user.id
    #     )
    #     .count()
    # )

    # total_employes = (
    #     MatchResult.query
    #     .join(Offre)
    #     .filter(
    #         Offre.user_id == current_user.id,
    #         MatchResult.score >= 70
    #     )
    #     .count()
    # )

    return render_template(
        "dashboardRecruteur.html",

        offres=offres,

        departements=departements,

        equipe=equipe,
    )

@recruteur_bp.route("/offre/<int:offre_id>")
@login_required
@role_required("recruteur")
def detail_offre(offre_id):
    return render_template("detailOffre.html", offre_id=offre_id)