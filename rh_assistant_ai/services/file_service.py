import pdfplumber


def extract_text_from_pdf(pdf_path):
    """
    Extrait le texte d'un fichier PDF.
    """

    text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text