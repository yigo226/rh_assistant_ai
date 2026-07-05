"""
Module de Normalisation (Étape 5 de l'architecture modulaire V2.1.0)
Responsabilités :
- Éliminer les doublons sémantiques ou textuels proches
- Nettoyer le bruit résiduel pour harmoniser les intitulés finaux
"""

def harmoniser_et_dedupliquer(liste_elements: list[str]) -> list[str]:
    """
    Prend une liste de termes extraits, applique des filtres de nettoyage,
    et élimine les redondances sémantiques évidentes.
    """
    if not liste_elements:
        return []

    # 1. Nettoyage de base : passage en casse propre (Title) et suppression des espaces blancs
    elements_propres = []
    for elem in liste_elements:
        terme = str(elem).strip()
        if len(terme) > 2 and not terme.isdigit():
            elements_propres.append(terme)

    # 2. Algorithme de déduplication sémantique par sous-chaînes
    # Trie du plus court au plus long pour fusionner les déclinaisons vers la racine
    elements_tries = sorted(list(set(elements_propres)), key=len)
    resultat_final = []

    for item in elements_tries:
        item_lower = item.lower()
        
        # Mots génériques à exclure impérativement des compétences RH
        mots_parasites = ["missions", "profil", "recherché", "poste", "travail", "équipe", "projet", "cadre", "cas", "votre"]
        if item_lower in mots_parasites:
            continue

        # Si un terme plus court et déjà validé est contenu dans ce terme long, on évite la redondance
        # Exemple: Si "Python" est déjà dans la liste, on n'ajoute pas "Langage Python"
        deja_present = False
        for valid_item in resultat_final:
            if valid_item.lower() in item_lower or item_lower in valid_item.lower():
                deja_present = True
                break
        
        if not deja_present:
            # Capitalisation propre (ex: python -> Python)
            if item_lower in ["python", "react", "node.js", "typescript", "figma", "sql", "nosql", "ux/ui"]:
                # Forcer l'écriture standardisée des acronymes ou technos reines
                mappage = {"python": "Python", "react": "React", "node.js": "Node.js", "typescript": "TypeScript", "figma": "Figma", "sql": "SQL", "nosql": "NoSQL", "ux/ui": "UX/UI"}
                resultat_final.append(mappage[item_lower])
            else:
                resultat_final.append(item.title())

    return sorted(resultat_final)
