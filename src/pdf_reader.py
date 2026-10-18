# pdf_reader.py
# Lire le PDF et récupérer le texte brut (avec pypdf)

from pypdf import PdfReader


def lire_pages(chemin: str) -> list[str]:
    """Renvoie une liste : 1 élément = le texte d'une page (utile pour le RAG)."""
    reader = PdfReader(chemin)
    return [page.extract_text() or "" for page in reader.pages]  # page vide/scannée -> ""


def lire_pdf(chemin: str) -> str:
    """Renvoie tout le texte du PDF d'un coup, avec le numéro de chaque page."""
    pages = lire_pages(chemin)
    return "\n\n".join(f"--- Page {i + 1} ---\n{texte}" for i, texte in enumerate(pages))


def couper_texte(texte: str, max_caracteres: int = 8000) -> str:
    """On coupe si le doc est trop long (pour pas exploser le contexte du LLM).
    Pour les questions sur un long document, on utilise le RAG (rag.py)."""
    if len(texte) > max_caracteres:
        return texte[:max_caracteres] + "\n[... texte tronqué ...]"
    return texte
