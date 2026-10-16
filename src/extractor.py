# extractor.py
# Fonctionnalité 1 : extraire les infos clés du document en JSON

from src.llm import appeler_llm_json
from src.schemas import ExtractionDocument

PROMPT_EXTRACTION = """Tu es un assistant qui extrait les informations clés d'un document.
N'invente rien : si une info n'est pas dans le document, laisse la liste vide."""


def extraire_infos(texte: str) -> ExtractionDocument:
    return appeler_llm_json(PROMPT_EXTRACTION, texte, ExtractionDocument)
