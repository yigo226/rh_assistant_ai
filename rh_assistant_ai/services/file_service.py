"""
Gestion des fichiers CV et Offres.

Responsabilités :
- Extraction du texte PDF
- Extraction du texte DOCX
- Extraction du texte TXT
- Détection automatique du type de fichier
"""

from pathlib import Path
import pdfplumber
from docx import Document

from services.nlp.preprocessing import clean_text
from services.nlp.skill_extractor import extract_skills

from services.nlp.diploma_extractor import extract_diplomas
from services.nlp.experience_extractor import extract_experience

from werkzeug.utils import secure_filename
# Fonctions d'extraction de texte pour différents formats de fichiers
def extract_text_from_pdf(pdf_path):
    """
    Extrait le texte d'un PDF.

    Args:
        pdf_path (str): chemin du PDF

    Returns:
        str
    """

    text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text.strip()

# Fonctions d'extraction de texte pour différents formats de fichiers
def extract_text_from_docx(docx_path):
    """
    Extrait le texte d'un fichier DOCX.

    Args:
        docx_path (str)

    Returns:
        str
    """

    document = Document(docx_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        paragraphs.append(paragraph.text)

    return "\n".join(paragraphs).strip()

# Fonctions d'extraction de texte pour différents formats de fichiers
def extract_text_from_txt(txt_path):
    """
    Extrait le texte d'un fichier TXT.

    Args:
        txt_path (str)

    Returns:
        str
    """

    with open(txt_path, "r", encoding="utf-8") as file:
        return file.read().strip()

# extrateur de texte
def extract_text(file_path):
    """
    Détermine automatiquement le type
    de fichier et appelle le bon extracteur.

    Formats supportés :
    - pdf
    - docx
    - txt

    Args:
        file_path (str)

    Returns:
        str
    """

    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    elif extension == ".docx":
        return extract_text_from_docx(file_path)

    elif extension == ".txt":
        return extract_text_from_txt(file_path)

    raise ValueError(
        f"Format non supporté : {extension}"
    )


# Analyseur de texte 
def analyseur_texte_extrait(text):
    text = clean_text(text)
    skills = extract_skills(text)
    diplomas = extract_diplomas(text)
    experiences = extract_experience(text)

    return {
        "skills": skills,
        "diplomas": diplomas,
        "experiences": experiences
    }