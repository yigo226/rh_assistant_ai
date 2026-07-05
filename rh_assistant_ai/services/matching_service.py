import os
import numpy as np
from datetime import datetime, timezone
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from config.database import db
from models import MatchResult
"""
    V2.1.0 : Algorithme Hybride Local (NLP & Similarité Cosinus).
    Compare les compétences, diplômes et expériences extraits en français.
    """

# Chargement du modèle sémantique léger (all-MiniLM-L6-v2)
_moteur_vectoriel_instance = None

def _get_moteur_vectoriel():
    """
    Pattern Lazy Loading : Charge le modèle Sentence-Transformers en RAM 
    uniquement au moment du premier clic de comparaison, puis réutilise l'instance.
    """
    global _moteur_vectoriel_instance
    if _moteur_vectoriel_instance is None:
        print("🤖 [IA MATCHING] Premier calcul détecté : Chargement de all-MiniLM-L6-v2 en RAM...")
        # L'utilisation du cache local de Hugging Face évite tout retéléchargement
        _moteur_vectoriel_instance = SentenceTransformer('all-MiniLM-L6-v2')
        print("✨ [IA MATCHING] Modèle vectoriel prêt pour la similarité sémantique.")
    return _moteur_vectoriel_instance


def calculer_matching(analyse_cv, analyse_offre):
    """
    V2.1.0 : Algorithme Hybride Local optimisé (Lazy Loading).
    """
    # 1. Récupération des données nettoyées de la BDD
    comp_cv = [c.lower().strip() for c in (analyse_cv.competences or [])]
    comp_offre = [c.lower().strip() for c in (analyse_offre.competences or [])]

    dipl_cv = [d.lower().strip() for d in (analyse_cv.diplomes or [])]
    dipl_offre = [d.lower().strip() for d in (analyse_offre.diplomes or [])]
    
    exp_cv = [e.lower().strip() for e in (analyse_cv.experiences or [])]
    exp_offre = [e.lower().strip() for e in (analyse_offre.experiences or [])]
   
    # 2. Vérification de la présence de données pour chaque dimension
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
    competences_bonus = list(set(comp_cv))

    score_competences = 0.0

    if comp_offre and comp_cv:
        # 🟢 APPEL UNIQUE DU MODÈLE VIA LE SINGLETON :
        moteur_vectoriel = _get_moteur_vectoriel()

        # Transformation des textes en vecteurs mathématiques de sens
        vectors_offre = moteur_vectoriel.encode(comp_offre)
        vectors_cv = moteur_vectoriel.encode(comp_cv)

        # Calcul de la matrice de similarité cosinus entre chaque mot
        matrice_similarite = cosine_similarity(vectors_offre, vectors_cv)

        total_scores = 0.0
        for i, comp_req in enumerate(comp_offre):
            meilleur_index_cv = np.argmax(matrice_similarite[i])
            meilleur_score = matrice_similarite[i][meilleur_index_cv]

            if meilleur_score >= 0.65:
                competences_validees.append(comp_req)
                total_scores += meilleur_score
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
    score_composite = 0.0
    poids_total = 0.0

    if comp_offre:
        score_composite += score_competences * 0.60
        poids_total += 60.0
    if dipl_offre:
        score_diplomes = (len(diplomes_valides) / len(dipl_offre)) * 100
        score_composite += score_diplomes * 0.30
        poids_total += 30.0
    if exp_offre:
        score_exp = (len(experiences_validees) / len(exp_offre)) * 100
        score_composite += score_exp * 0.10
        poids_total += 10.0

    score_final = float(round((score_composite / poids_total) * 100, 2)) if poids_total > 0 else 0.0
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
    
    print(f"======= Matching calculé : Score={score_final}, Compétences validées={competences_validees}, Compétences manquantes={competences_manquantes}, Compétences bonus={competences_bonus}, Diplômes validés={diplomes_valides}, Diplômes manquants={diplomes_manquants}, Expériences validées={experiences_validees}, Expériences manquantes={experiences_manquantes}, Recommandation='{recommandation}'")
    
    return {
        "score": score_final,
        "competences_validees": sorted(list(set(competences_validees))),
        "competences_manquantes": sorted(list(set(competences_manquantes))),
        "competences_bonus": sorted(competences_bonus),
        "diplomes_valides": diplomes_valides,
        "diplomes_manquants": diplomes_manquants,
        "experiences_validees": experiences_validees,
        "experiences_manquantes": experiences_manquantes,
        "recommandation": recommandation,
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
