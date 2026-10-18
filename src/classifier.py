# classifier.py
# Fonctionnalité 2 : classer le document (type + confidentialité) avec une justification
# qui cite un passage du texte

from src.llm import appeler_llm_json
from src.schemas import Classification

PROMPT_CLASSIFICATION = """Tu es un assistant qui classe des documents.
1. Choisis le type du document dans la liste autorisée.
2. Choisis le niveau de confidentialité :
   - public : peut être diffusé à tout le monde (article, cours, page web...)
   - interne : réservé à une organisation, mais pas sensible (note de service, procédure...)
   - confidentiel : contient des données personnelles, financières, juridiques ou une mention "confidentiel"
3. Justifie en citant un passage EXACT du document (copié mot pour mot, une phrase maximum).
4. Donne ta confiance entre 0 et 1 (1 = sûr à 100 %)."""


def normaliser(texte: str) -> str:
    """Met en minuscules et enlève les espaces en trop (pour comparer plus facilement)."""
    return " ".join(texte.lower().split())


def classer_document(texte: str) -> Classification:
    resultat = appeler_llm_json(PROMPT_CLASSIFICATION, f"Document :\n{texte}", Classification)

    # Anti-hallucination : on vérifie que la citation existe VRAIMENT dans le document
    resultat.citation_verifiee = normaliser(resultat.citation) in normaliser(texte)
    if not resultat.citation_verifiee:
        print("⚠️ Attention : la citation donnée par le modèle n'est pas dans le document !")

    return resultat
