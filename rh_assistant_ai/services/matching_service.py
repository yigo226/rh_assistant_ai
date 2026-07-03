import os
import numpy as np
from datetime import datetime, timezone
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from config.database import db
from models import MatchResult

# 🟢 Chargement du modèle sémantique léger (all-MiniLM-L6-v2)
# Téléchargement automatique unique de ~90 Mo, puis 100% hors-ligne et gratuit.
moteur_vectoriel = SentenceTransformer('all-MiniLM-L6-v2')

def calculer_matching(analyse_cv, analyse_offre):
    """
    V2.1.0 : Algorithme Hybride Local (NLP & Similarité Cosinus).
    Compare les compétences, diplômes et expériences extraits en français.
    """
    # 1. Récupération des données nettoyées de la BDD
    comp_cv = [c.lower().strip() for c in (analyse_cv.competences or [])]
    comp_offre = [c.lower().strip() for c in (analyse_offre.competences or [])]

    dipl_cv = [d.lower().strip() for d in (analyse_cv.diplomes or [])]
    dipl_offre = [d.lower().strip() for d in (analyse_offre.diplomes or [])]

    exp_cv = [e.lower().strip() for e in (analyse_cv.experiences or [])]
    exp_offre = [e.lower().strip() for e in (analyse_offre.experiences or [])]

    # Sécurité : Si l'offre est totalement vide, calcul impossible
    if not comp_offre and not dipl_offre and not exp_offre:
        return {
            "score": 0.0,
            "competences_validees": [], "competences_manquantes": [], "competences_bonus": [],
            "diplomes_valides": [], "diplomes_manquants": [],
            "experiences_validees": [], "experiences_manquantes": [],
            "recommandation": "Analyse impossible : Aucun critère sémantique n'a été détecté dans l'offre."
        }

    # ============================================================
    # A. ANALYSE SÉMANTIQUE DES COMPÉTENCES (Sentence-Transformers)
    # ============================================================
    competences_validees = []
    competences_manquantes = []
    competences_bonus = list(set(comp_cv)) # Initialisation avec tout le CV

    score_competences = 0.0

    if comp_offre and comp_cv:
        # Transformation des textes en vecteurs mathématiques de sens
        vectors_offre = moteur_vectoriel.encode(comp_offre)
        vectors_cv = moteur_vectoriel.encode(comp_cv)

        # Calcul de la matrice de similarité cosinus entre chaque mot
        matrice_similarite = cosine_similarity(vectors_offre, vectors_cv)

        total_scores = 0.0
        # Pour chaque compétence requise par l'offre, on cherche la plus proche dans le CV
        for i, comp_req in enumerate(comp_offre):
            meilleur_index_cv = np.argmax(matrice_similarite[i])
            meilleur_score = matrice_similarite[i][meilleur_index_cv]

            # 🧠 SEUIL DE TOLÉRANCE SÉMANTIQUE (0.65)
            # Permet d'accepter des synonymes comme "postgres" et "postgresql"
            if meilleur_score >= 0.65:
                competences_validees.append(comp_req)
                total_scores += meilleur_score
                # On retire de la liste des bonus ce qui a été validé
                comp_trouvee_cv = comp_cv[meilleur_index_cv]
                if comp_trouvee_cv in competences_bonus:
                    competences_bonus.remove(comp_trouvee_cv)
            else:
                competences_manquantes.append(comp_req)

        score_competences = (total_scores / len(comp_offre)) * 100
    elif comp_offre:
        competences_manquantes = comp_offre

    # ============================================================
    # B. ANALYSE ENSEMBLISTE DES DIPLÔMES ET EXPÉRIENCES
    # ============================================================
    diplomes_valides = sorted(list(set(dipl_cv).intersection(set(dipl_offre))))
    diplomes_manquants = sorted(list(set(dipl_offre).difference(set(dipl_cv))))

    experiences_validees = sorted(list(set(exp_cv).intersection(set(exp_offre))))
    experiences_manquantes = sorted(list(set(exp_offre).difference(set(exp_cv))))

    # ============================================================
    # C. CALCUL DU SCORE COMPOSITE PONDÉRÉ
    # ============================================================
    # Pondération : Compétences (60%), Diplômes (30%), Expériences (10%)
    score_composite = 0.0
    poids_total = 0.0

    if comp_offre:
        score_composite += score_competences * 0.60
        poids_total += 60.0
    if dipl_offre:
        score_diplomes = (len(diplomes_valides) / len(diplomes_offre)) * 100
        score_composite += score_diplomes * 0.30
        poids_total += 30.0
    if experiences_offre:
        score_exp = (len(experiences_validees) / len(experiences_offre)) * 100
        score_composite += score_exp * 0.10
        poids_total += 10.0

    score_final = round((score_composite / poids_total) * 100, 2) if poids_total > 0 else 0.0
    # Normalisation pour ne pas dépasser 100%
    score_final = min(score_final, 100.0)

    # ============================================================
    # D. RECOMMANDATION AUTOMATIQUE LOCALE SANS LLM
    # ============================================================
    if score_final >= 80:
        recommandation = "Excellent profil. L'analyse sémantique locale confirme une adéquation majeure avec le poste."
    elif score_final >= 60:
        recommandation = "Bon profil. Les compétences fondamentales sont validées, des points secondaires restent à vérifier."
    elif score_final >= 40:
        recommandation = "Profil intermédiaire. Des écarts notables apparaissent sur des compétences ou diplômes clés."
    else:
        recommandation = "Compatibilité faible. Le parcours ne couvre pas les exigences critiques de la fiche de poste."

    return {
        "score": score_final,
        "competences_validees": sorted(list(set(competences_validees))),
        "competences_manquantes": sorted(list(set(competences_manquantes))),
        "competences_bonus": sorted(competences_bonus),
        "diplomes_valides": diplomes_valides,
        "diplomes_manquants": diplomes_manquants,
        "experiences_validees": experiences_validees,
        "experiences_manquantes": experiences_manquantes,
        "recommandation": recommandation
    }


def enregistrer_match_result(analyse_cv, analyse_offre, metriques):
    """Sauvegarde le résultat du matching local v2.1.0 en BDD."""
    try:
        nouveau_match = MatchResult(
            cv_analyser_id=int(analyse_cv.id),       
            offre_analyser_id=int(analyse_offre.id),
            score=metriques["score"],
            recommandation=metriques["recommandation"],
            
            # Injection des colonnes de résultats calculées
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
