from models import MatchResult
from config.database import db





"""
matching_service.py

Ce service contient toute la logique métier permettant de comparer
les compétences extraites d'un CV avec celles d'une offre d'emploi.

Le matching repose actuellement uniquement sur les compétences
(skills), mais cette logique pourra évoluer plus tard pour intégrer :

- les années d'expérience
- les diplômes
- les langues
- les certifications
- les soft skills
- un score pondéré
"""


def calculer_matching(analyse_cv, analyse_offre):
    """
    Compare les compétences d'un CV avec celles d'une offre.

    Paramètres
    ----------
    analyse_cv : CVAnalyser
        Résultat de l'analyse du CV.

    analyse_offre : OffreAnalyser
        Résultat de l'analyse de l'offre.

    Retour
    ------
    dict contenant :

        score
        matching_skills
        missing_skills
        extra_skills
        recommendation
    """

    competences_cv = {
        skill.lower().strip()
        for skill in (analyse_cv.skills or [])
    }

    competences_offre = {
        skill.lower().strip()
        for skill in (analyse_offre.skills or [])
    }

    if not competences_offre:

        return {

            "score": 0,

            "matching_skills": [],

            "missing_skills": [],

            "extra_skills": [],

            "recommendation":
                "Impossible de calculer un matching : "
                "aucune compétence n'a été détectée dans l'offre."
        }
    # Calcul des compétences communes
    matching_skills = sorted(
        competences_cv.intersection(
            competences_offre
        )
    )
    # Compétences manquantes
    missing_skills = sorted(
        competences_offre.difference(
            competences_cv
        )
    )
    # Compétences supplémentaires du candidat
    extra_skills = sorted(
        competences_cv.difference(
            competences_offre
        )
    )
    # Calcul du score
    score = round(
        (
            len(matching_skills)
            /
            len(competences_offre)
        ) * 100,

        2
    )
    # Génération de la recommandation
    if score >= 80:

        recommendation = (
            "Excellent profil. "
            "Le candidat possède la majorité "
            "des compétences recherchées."
        )

    elif score >= 60:

        recommendation = (
            "Bon profil. "
            "Quelques compétences restent "
            "à renforcer mais le candidat "
            "mérite un entretien."
        )

    elif score >= 40:

        recommendation = (
            "Profil intermédiaire. "
            "Des écarts importants existent "
            "sur certaines compétences."
        )

    else:

        recommendation = (
            "Compatibilité faible. "
            "Le profil ne correspond pas "
            "aux exigences principales du poste."
        )

    # ---------------------------------------
    # Résultat du matching
    # ---------------------------------------

    return {

        "score": score,

        "matching_skills": matching_skills,

        "missing_skills": missing_skills,

        "extra_skills": extra_skills,

        "recommendation": recommendation,

        "matching_count": len(matching_skills),

        "missing_count": len(missing_skills),

        "required_count": len(competences_offre),

        "candidate_count": len(competences_cv)
    }


# Enregistrement du résultat du matching en base de données
# Cette fonction prend en charge la création d'une nouvelle entrée MatchResult

# Cette fonction prend en charge la création d'une nouvelle entrée MatchResult (Épurée)
def enregistrer_match_result(analyse_cv, analyse_offre, metriques):
    """
    Prend en charge l'instanciation et la sauvegarde du résultat du matching
    en reliant uniquement les deux analyses et toutes les métriques de compétences JSON.
    """
    try:
        # 🟢 CORRECTION : Instanciation propre sans user_id ni paramètre user
        nouveau_match = MatchResult(
            cv_analyser_id=int(analyse_cv.id),       
            offre_analyser_id=int(analyse_offre.id),

            score=metriques["score"],
            
            # Toutes les listes de compétences JSON calculées par le service
            matching_skills=metriques["matching_skills"],
            missing_skills=metriques["missing_skills"],
            extra_skills=metriques["extra_skills"], 
            
            recommendation=metriques["recommendation"]
        )
        
        db.session.add(nouveau_match)
        db.session.commit()
        
        return nouveau_match

    except Exception as e:
        db.session.rollback()
        raise e
