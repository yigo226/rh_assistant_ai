from models import MatchResult
from config.database import db
from datetime import datetime, timezone

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
    Compare de manière exhaustive les compétences, diplômes et expériences
    d'un CV avec ceux d'une offre d'emploi.
    """
    # ============================================================
    # 1. PRÉPARATION ET EXTRACTION DES DONNÉES EN FRANÇAIS
    # ============================================================
    competences_cv = {c.lower().strip() for c in (analyse_cv.competences or [])}
    competences_offre = {c.lower().strip() for c in (analyse_offre.competences or [])}

    diplomes_cv = {d.lower().strip() for d in (analyse_cv.diplomes or [])}
    diplomes_offre = {d.lower().strip() for d in (analyse_offre.diplomes or [])}

    experiences_cv = {e.lower().strip() for e in (analyse_cv.experiences or [])}
    experiences_offre = {e.lower().strip() for e in (analyse_offre.experiences or [])}

    # Sécurité : Si l'offre ne contient aucun critère
    if not competences_offre and not diplomes_offre:
        return {
            "score": 0.0,
            "competences_validees": [], "competences_manquantes": [], "competences_bonus": [],
            "diplomes_valides": [], "diplomes_manquants": [],
            "experiences_validees": [], "experiences_manquantes": [],
            "recommandation": "Impossible d'analyser : aucun critère détecté dans l'offre."
        }

    # ============================================================
    # 2. CALCULS ALGORITHMIQUES (INTERSECTIONS & DIFFÉRENCES)
    # ============================================================
    # Bloc Compétences
    competences_validees = sorted(competences_cv.intersection(competences_offre))
    competences_manquantes = sorted(competences_offre.difference(competences_cv))
    competences_bonus = sorted(competences_cv.difference(competences_offre))

    # Bloc Diplômes
    diplomes_valides = sorted(diplomes_cv.intersection(diplomes_offre))
    diplomes_manquants = sorted(diplomes_offre.difference(diplomes_cv))

    # Bloc Expériences
    experiences_validees = sorted(experiences_cv.intersection(experiences_offre))
    experiences_manquantes = sorted(experiences_offre.difference(experiences_cv))

    # ============================================================
    # 3. CALCUL DU SCORE COMPOSITE ET PONDÉRÉ
    # ============================================================
    # On donne un poids de 60% aux compétences, 30% aux diplômes, 10% aux expériences
    score_comp = 0.0
    poids_total = 0.0

    if competences_offre:
        score_comp += (len(competences_validees) / len(competences_offre)) * 60.0
        poids_total += 60.0
    if diplomes_offre:
        score_comp += (len(diplomes_valides) / len(diplomes_offre)) * 30.0
        poids_total += 30.0
    if experiences_offre:
        score_comp += (len(experiences_validees) / len(experiences_offre)) * 100.0 * 0.10 # 10%
        poids_total += 10.0

    score_final = round((score_comp / poids_total) * 100, 2) if poids_total > 0 else 0.0

    # ============================================================
    # 4. GÉNÉRATION DE LA RECOMMANDATION SÉMANTIQUE
    # ============================================================
    if score_final >= 80:
        recommandation = "Excellent profil. Le candidat possède la grande majorité des critères recherchés."
    elif score_final >= 60:
        recommandation = "Bon profil. Quelques critères restent à renforcer mais le candidat mérite un entretien."
    elif score_final >= 40:
        recommandation = "Profil intermédiaire. Des écarts notables existent sur des compétences ou diplômes clés."
    else:
        recommandation = "Compatibilité faible. Le profil ne correspond pas aux exigences principales du poste."

    return {
        "score": score_final,
        "competences_validees": competences_validees,
        "competences_manquantes": competences_manquantes,
        "competences_bonus": competences_bonus,
        "diplomes_valides": diplomes_valides,
        "diplomes_manquants": diplomes_manquants,
        "experiences_validees": experiences_validees,
        "experiences_manquantes": experiences_manquantes,
        "recommandation": recommandation
    }


# ============================================================
# 5. ENREGISTREMENT ET MASTAGE EN BDD (NOMS DE CHAMPS EN FR)
# ============================================================
def enregistrer_match_result(analyse_cv, analyse_offre, metriques):
    """
    Prend en charge l'instanciation et la sauvegarde du résultat du matching
    en insérant l'intégralité des nouveaux champs français en BDD.
    """
    try:
        nouveau_match = MatchResult(
            cv_analyser_id=int(analyse_cv.id),       
            offre_analyser_id=int(analyse_offre.id),
            score=metriques["score"],
            recommandation=metriques["recommandation"],
            
            # Injection des clés françaises dans votre table match_results
            competences_validees=metriques["competences_validees"],
            competences_manquantes=metriques["competences_manquantes"],
            competences_bonus=metriques["competences_bonus"],
            
            diplomes_valides=metriques["diplomes_valides"],
            diplomes_manquants=metriques["diplomes_manquants"],
            
            experiences_validees=metriques["experiences_validees"],
            experiences_manquantes=metriques["experiences_manquantes"]
        )
        
        db.session.add(nouveau_match)
        db.session.commit()
        
        return nouveau_match

    except Exception as e:
        db.session.rollback()
        raise e
