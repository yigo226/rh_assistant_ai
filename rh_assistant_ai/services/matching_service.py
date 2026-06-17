


# matching_service.py
# ici nous allons implémenter la logique de calcul du score de compatibilité entre un CV et une offre d'emploi
# Nous allons comparer les compétences extraites du CV avec celles de l'offre et calculer un score basé sur le nombre de compétences correspondantes par rapport au nombre total de compétences requises par l'offre.
# Nous allons également identifier les compétences manquantes pour le candidat.
# Le résultat de cette comparaison sera stocké dans la base de données pour pouvoir être affiché à l'utilisateur.
def calculate_match_score(
        cv_skills,
        offre_skills
):
    """
    Calcule le score de compatibilité.
    """

    cv_set = set(
        skill.lower()
        for skill in cv_skills
    )

    offre_set = set(
        skill.lower()
        for skill in offre_skills
    )

    matching = list(
        cv_set.intersection(
            offre_set
        )
    )

    missing = list(
        offre_set.difference(
            cv_set
        )
    )

    if len(offre_set) == 0:

        score = 0

    else:

        score = round(
            (
                len(matching)
                /
                len(offre_set)
            ) * 100,
            2
        )

    return {

        "score": score,

        "matching_skills": matching,

        "missing_skills": missing
    }

# en fonction du score calculé, nous allons générer une recommandation pour le candidat sur la base de seuils prédéfinis.
# Par exemple, un score supérieur à 80% pourrait être considéré comme excellent, entre 60% et 80% comme bon, entre 40% et 60% comme acceptable, et en dessous de 40% comme faible.

def generate_recommendation(score):

    if score >= 80:

        return (
            "Excellent profil. "
            "Candidat fortement recommandé."
        )

    elif score >= 60:

        return (
            "Bon profil. "
            "Entretien recommandé."
        )

    elif score >= 40:

        return (
            "Profil acceptable "
            "mais certaines compétences "
            "sont manquantes."
        )

    return (
        "Compatibilité faible."
    )

