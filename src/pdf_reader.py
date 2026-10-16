# pdf_reader.py
# Étape 1 : lire le PDF et récupérer le texte brut (avec pypdf)

from pypdf import PdfReader


def lire_pdf(chemin: str) -> str:
    """Renvoie tout le texte du PDF, page par page."""
    reader = PdfReader(chemin)
    pages = []
    for i, page in enumerate(reader.pages):
        texte = page.extract_text() or ""  # si la page est vide/scannée -> ""
        pages.append(f"--- Page {i + 1} ---\n{texte}")
    return "\n\n".join(pages)


def couper_texte(texte: str, max_caracteres: int = 8000) -> str:
    """On coupe si le doc est trop long (pour pas exploser le contexte du LLM).
    TODO semaine 4 : faire mieux avec du chunking + RAG."""
    if len(texte) > max_caracteres:
        return texte[:max_caracteres] + "\n[... texte tronqué ...]"
    return texte
