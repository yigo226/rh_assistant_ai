"""
Gestion des fichiers CV et Offres.

Responsabilités :
- Extraction du texte PDF
- Extraction du texte DOCX
- Extraction du texte TXT
- Détection automatique du type de fichier
- Analyse sémantique et structuration en français
"""

from pathlib import Path
import pdfplumber
from docx import Document
from werkzeug.utils import secure_filename

# Importations de vos extracteurs NLP
from services.nlp.preprocessing import clean_text
from services.nlp.skill_extractor import extract_skills
from services.nlp.diploma_extractor import extract_diplomas
from services.nlp.experience_extractor import extract_experience


def extract_text_from_pdf(pdf_path):
    """Extrait le texte d'un fichier PDF."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def extract_text_from_docx(docx_path):
    """Extrait le texte d'un fichier DOCX."""
    document = Document(docx_path)
    paragraphs = []
    for paragraph in document.paragraphs:
        paragraphs.append(paragraph.text)
    return "\n".join(paragraphs).strip()


def extract_text_from_txt(txt_path):
    """Extrait le texte d'un fichier TXT."""
    with open(txt_path, "r", encoding="utf-8") as file:
        return file.read().strip()


def extract_text(file_path):
    """
    Détermine automatiquement le type de fichier et appelle le bon extracteur.
    Formats supportés : .pdf, .docx, .txt
    """
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)
    elif extension == ".docx":
        return extract_text_from_docx(file_path)
    elif extension == ".txt":
        return extract_text_from_txt(file_path)

    raise ValueError(f"Format non supporté : {extension}")


# ============================================================
#  ANALYSEUR AVEC DICTIONNAIRE 
# ============================================================
def analyseur_texte_extrait(text):
    """
    Analyse le texte brut, extrait les entités sémantiques 
    et retourne un dictionnaire structuré avec des clés en français.
    """
    # Nettoyage initial du texte
    texte_propre = clean_text(text)
    
    # Extraction NLP via vos modules dédiés
    liste_competences = extract_skills(texte_propre)
    liste_diplomes = extract_diplomas(texte_propre)
    liste_experiences = extract_experience(texte_propre)

    #  Clés renommées en français pour s'aligner sur les modèles SQL
    return {
        "competences": list(liste_competences) if liste_competences else [],
        "diplomes": list(liste_diplomes) if liste_diplomes else [],
        "experiences": list(liste_experiences) if liste_experiences else []
    }
