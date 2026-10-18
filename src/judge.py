# judge.py
# Fonctionnalité 5 : "LLM as a judge"
# Un 2e LLM (un autre modèle) relit le document + l'extraction et donne une note.
# Ça permet d'évaluer la qualité SANS avoir besoin d'annoter des données à la main.

import os
import json

from pydantic import BaseModel, Field

from src.llm import appeler_llm_json
from src.schemas import ExtractionDocument

# on prend un modèle DIFFÉRENT de celui qui a fait l'extraction (sinon il se note lui-même !)
MODELE_JUGE = os.getenv("JUDGE_MODEL", "openai/gpt-oss-20b")


class Evaluation(BaseModel):
    fidelite: int = Field(ge=1, le=5, description="Les infos sont-elles vraies par rapport au document ? (1 à 5)")
    completude: int = Field(ge=1, le=5, description="Les infos importantes sont-elles toutes là ? (1 à 5)")
    absence_hallucination: int = Field(ge=1, le=5, description="5 = rien d'inventé, 1 = beaucoup d'inventions")
    problemes: list[str] = Field(default=[], description="Liste des erreurs ou oublis repérés (vide si aucun)")
    commentaire: str = Field(description="Avis général en 1-2 phrases")


PROMPT_JUGE = """Tu es un évaluateur strict. On te donne un DOCUMENT et une EXTRACTION faite par une autre IA.
Note l'extraction de 1 à 5 sur chaque critère, en comparant UNIQUEMENT avec le document.
Signale précisément chaque information fausse, inventée ou oubliée."""


def evaluer_extraction(texte: str, extraction: ExtractionDocument) -> dict:
    message = (f"DOCUMENT :\n{texte}\n\n"
               f"EXTRACTION À ÉVALUER :\n{json.dumps(extraction.model_dump(), ensure_ascii=False, indent=2)}")
    evaluation = appeler_llm_json(PROMPT_JUGE, message, Evaluation, modele=MODELE_JUGE)

    resultat = evaluation.model_dump()
    # score global sur 5 = moyenne des 3 critères
    resultat["score_global"] = round((evaluation.fidelite + evaluation.completude + evaluation.absence_hallucination) / 3, 2)
    resultat["modele_juge"] = MODELE_JUGE
    return resultat
