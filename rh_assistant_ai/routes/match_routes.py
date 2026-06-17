from flask import (
    Blueprint,
    render_template
)

from flask_login import (
    login_required
)
from models.offre import Offre 
from models.cv import CV

from flask_login import current_user
from config.database import db

from models.cv_analyser import CVAnalyser

from models.offre_analyser import OffreAnalyser

from models.match_result import MatchResult


from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from config.database import db

from models.cv import CV
from models.offre import Offre
from models.cv_analyser import CVAnalyser
from models.offre_analyser import OffreAnalyser
from models.match_result import MatchResult

from services.matching_service import (
    calculate_match_score,
    generate_recommendation
)

# Ces services sont à adapter à ton projet
from services.cv_service import save_cv
from services.offre_service import save_offre


from services.matching_service import (
    calculate_match_score,
    generate_recommendation
)

match_bp = Blueprint(
    "match",
    __name__,
    url_prefix="/match"
)

@match_bp.route(
    "/select-offre/<int:cv_id>"
)

@login_required
def select_offre(cv_id):

    cv = CV.query.get_or_404(
        cv_id
    )

    offres = Offre.query.filter_by(

        user_id=current_user.id

    ).all()

    return render_template(

        "match/select_offre.html",

        cv=cv,

        offres=offres

    )

@match_bp.route(
    "/select-cv/<int:offre_id>"
)
@login_required
def select_cv(offre_id):

    offre = Offre.query.get_or_404(
        offre_id
    )

    cvs = CV.query.filter_by(

        user_id=current_user.id

    ).all()

    return render_template(

        "match/select_cv.html",

        offre=offre,

        cvs=cvs

    )


# Route pour afficher le résultat du matching entre un CV et une offre
# Nous allons récupérer les analyses du CV et de l'offre, calculer le score de compatibilité, générer une recommandation, puis stocker le résultat dans la base de données avant de l'afficher à l'utilisateur.
# L'URL de cette route inclura les IDs du CV et de l'offre pour pouvoir effectuer le matching spécifique entre ces deux éléments.
@match_bp.route("/<int:cv_id>/<int:offre_id>")
@login_required
def match(cv_id, offre_id):

    cv_analysis = CVAnalyser.query.filter_by(
        cv_id=cv_id
    ).first()

    offre_analysis = OffreAnalyser.query.filter_by(
        offre_id=offre_id
    ).first()

    cv_skills = (
        cv_analysis.skills.split(",")
        if cv_analysis.skills
        else []
    )

    offre_skills = (
        offre_analysis.skills.split(",")
        if offre_analysis.skills
        else []
    )

    result = calculate_match_score(
        cv_skills,
        offre_skills
    )

    recommendation = (
        generate_recommendation(
            result["score"]
        )
    )

    match_result = MatchResult(

        score=result["score"],

        matching_skills=",".join(
            result["matching_skills"]
        ),

        missing_skills=",".join(
            result["missing_skills"]
        ),

        recommendation=recommendation,

        cv_id=cv_id,

        offre_id=offre_id
    )

    db.session.add(
        match_result
    )

    db.session.commit()

    return render_template(
        "match/result.html",
        
        result=result,
        recommendation=recommendation,
    )



@match_bp.route("/start",
    methods=["GET", "POST"]
)
@login_required
def start_match():

    # ---------------------------------
    # CV actuellement enregistré
    # ---------------------------------

    cv = (
        CV.query
        .filter_by(user_id=current_user.id)
        .order_by(CV.id.desc())
        .first()
    )

    if request.method == "GET":

        return render_template(
            "match/start_match.html",
            cv=cv
        )

    # ---------------------------------
    # POST
    # ---------------------------------

    cv_file = request.files.get("cv")
    offre_file = request.files.get("offre")

    # -------------------------------
    # Gestion du CV
    # -------------------------------

    # L'utilisateur a choisi un nouveau CV
    if cv_file and cv_file.filename != "":
        print("ici, nouveau CV uploadé : ")
        # analyser et le sauvegarder dans la base de données
        cv = save_cv(
            file=cv_file,
            user=current_user
        )

        print("CV analysé et sauvegardé : ", cv.id)
        # analyse du CV en format texte
        #analyze_cv(cv)

    # Aucun nouveau CV
    else:

        if cv is None:

            flash(
                "Veuillez charger un CV avant de lancer un matching.",
                "warning"
            )

            return redirect(
                url_for("match.start_match")
            )

    # -------------------------------
    # Gestion de l'offre
    # -------------------------------

    if (
        offre_file is None
        or offre_file.filename == ""
    ):

        flash(
            "Veuillez sélectionner une offre d'emploi.",
            "warning"
        )

        return redirect(
            url_for("match.start_match")
        )

    offre = save_offre(
        file=offre_file,
        user=current_user
    )
    print("Offre analysée et sauvegardée : ", offre.id)

    # analyze_offre(offre) est appelé dans save_offre, pas besoin de le rappeler ici
    # analyze_offre(offre)

    # -------------------------------
    # Récupération des analyses
    # -------------------------------

    cv_analysis = CVAnalyser.query.filter_by(
        cv_id=cv.id
    ).first()

    offre_analysis = OffreAnalyser.query.filter_by(
        offer_id=offre.id
    ).first()

    cv_skills = (
        cv_analysis.skills.split(",")
        if cv_analysis and cv_analysis.skills
        else []
    )

    offre_skills = (
        offre_analysis.skills.split(",")
        if offre_analysis and offre_analysis.skills
        else []
    )

    # -------------------------------
    # Matching
    # -------------------------------

    result = calculate_match_score(
        cv_skills,
        offre_skills
    )

    recommendation = generate_recommendation(
        result["score"]
    )

    match_result = MatchResult(

        score=result["score"],

        matching_skills=",".join(
            result["matching_skills"]
        ),

        missing_skills=",".join(
            result["missing_skills"]
        ),

        recommendation=recommendation,

        cv_id=cv.id,

        offer_id=offre.id
    )

    db.session.add(match_result)
    db.session.commit()

    return render_template(
        "match/result.html",
        result=result,
        recommendation=recommendation,
        cv=cv,
        offre=offre
    )

