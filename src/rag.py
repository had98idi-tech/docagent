# rag.py
# Fonctionnalité 4 : répondre aux questions sur le document (RAG)
# Principe : 1) on coupe le doc en petits morceaux (chunks)
#            2) on transforme chaque morceau en vecteur (embedding)
#            3) pour une question, on cherche les morceaux les plus proches
#            4) on donne SEULEMENT ces morceaux au LLM pour qu'il réponde

import numpy as np
from pydantic import BaseModel, Field

from src.llm import appeler_llm_json

# modèle d'embeddings multilingue (marche en français), tourne en local et gratuit
MODELE_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_modele = None  # on garde le modèle en mémoire pour ne le charger qu'UNE fois


def charger_modele():
    global _modele
    if _modele is None:
        from sentence_transformers import SentenceTransformer  # import ici car c'est lent
        print("Chargement du modèle d'embeddings (long la 1re fois)...")
        _modele = SentenceTransformer(MODELE_EMBEDDINGS)
    return _modele


class ReponseRAG(BaseModel):
    reponse: str = Field(description="La réponse à la question, en français")
    trouve_dans_document: bool = Field(description="false si la réponse n'est pas dans les extraits")


def decouper(pages: list[str], taille: int = 800, chevauchement: int = 150) -> list[dict]:
    """Coupe chaque page en morceaux de ~800 caractères.
    Le chevauchement évite de couper une idée importante en deux."""
    chunks = []
    for num_page, texte in enumerate(pages, start=1):
        debut = 0
        while debut < len(texte):
            morceau = texte[debut:debut + taille].strip()
            if morceau:
                chunks.append({"page": num_page, "texte": morceau})
            debut += taille - chevauchement
    return chunks


class IndexRAG:
    def __init__(self, pages: list[str]):
        self.modele = charger_modele()
        self.chunks = decouper(pages)
        textes = [c["texte"] for c in self.chunks]
        # normalize -> on peut utiliser un simple produit scalaire = similarité cosinus
        self.vecteurs = self.modele.encode(textes, normalize_embeddings=True)
        print(f"Index prêt : {len(self.chunks)} morceaux")

    def rechercher(self, question: str, k: int = 3) -> list[dict]:
        """Renvoie les k morceaux les plus proches de la question."""
        if not self.chunks:
            return []
        v_question = self.modele.encode([question], normalize_embeddings=True)[0]
        scores = self.vecteurs @ v_question          # similarité avec chaque morceau
        meilleurs = np.argsort(scores)[::-1][:k]     # indices des k meilleurs scores
        return [{**self.chunks[i], "score": round(float(scores[i]), 3)} for i in meilleurs]


PROMPT_RAG = """Tu réponds à une question en utilisant UNIQUEMENT les extraits du document donnés.
Si la réponse n'est pas dans les extraits, dis-le et mets trouve_dans_document à false.
N'invente rien."""


def poser_question(index: IndexRAG, question: str) -> dict:
    extraits = index.rechercher(question)
    contexte = "\n\n".join(f"[Page {e['page']}] {e['texte']}" for e in extraits)
    message = f"Extraits :\n{contexte}\n\nQuestion : {question}"

    resultat = appeler_llm_json(PROMPT_RAG, message, ReponseRAG)
    return {
        "question": question,
        "reponse": resultat.reponse,
        "trouve_dans_document": resultat.trouve_dans_document,
        "sources": [{"page": e["page"], "score": e["score"], "extrait": e["texte"][:200]} for e in extraits],
    }
