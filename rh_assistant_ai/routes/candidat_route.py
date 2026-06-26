
import os
from config.database import db

# Blueprint pour les routes liées aux CV
from flask import Blueprint, request, render_template
from flask_login import current_user, login_required
from config.decorateurs import role_required
from models.offre import Offre
from services.cv_service import save_cv
from models.match_result import MatchResult


candidat_bp = Blueprint(
    "candidat",
    __name__,
    url_prefix="/candidat"
)

@candidat_bp.route("/mon-matching")
@login_required
@role_required("candidat")
def espace_candidat():
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
        "ListeOffre.html",
        offres=offres,
        scores_deja_calcules=scores_deja_calcules,
        recherche=recherche
    )
