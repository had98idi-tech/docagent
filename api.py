# api.py
# Fonctionnalité 6 : exposer DocAgent via une API REST (FastAPI)
# Lancer : uvicorn api:app --reload
# Puis ouvrir http://localhost:8000/docs  -> FastAPI génère une page pour tester l'API !

import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.agent import analyser_document
from src.pdf_reader import lire_pages
from src.rag import IndexRAG, poser_question
from src.validation import appliquer_decision_humaine

app = FastAPI(
    title="DocAgent API",
    description="Agent IA d'analyse de PDF : extraction, classification, validation humaine, RAG, LLM-juge",
    version="1.0",
)

# "base de données" très simple : un dict en mémoire (perdu quand on relance le serveur)
DOCUMENTS: dict[str, dict] = {}


class Question(BaseModel):
    question: str


class DecisionHumaine(BaseModel):
    confidentialite: str  # public / interne / confidentiel


@app.get("/")
def accueil():
    return {"message": "DocAgent API — va sur /docs pour tester"}


@app.post("/documents")
def analyser(fichier: UploadFile = File(...), avec_juge: bool = True):
    """Envoie un PDF -> renvoie l'analyse complète + un id pour poser des questions ensuite."""
    if not fichier.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    # on enregistre le PDF dans un fichier temporaire pour pouvoir le lire
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(fichier.file, tmp)
        chemin = tmp.name

    try:
        resultat = analyser_document(chemin, avec_juge=avec_juge)
        index = IndexRAG(lire_pages(chemin))  # on prépare le RAG tout de suite
    finally:
        Path(chemin).unlink(missing_ok=True)  # on supprime le fichier temporaire

    doc_id = str(uuid.uuid4())[:8]
    DOCUMENTS[doc_id] = {"nom": fichier.filename, "resultat": resultat, "index": index}
    return {"doc_id": doc_id, "nom": fichier.filename, **resultat}


@app.get("/documents/{doc_id}")
def voir(doc_id: str):
    doc = recuperer(doc_id)
    return {"doc_id": doc_id, "nom": doc["nom"], **doc["resultat"]}


@app.post("/documents/{doc_id}/questions")
def question(doc_id: str, q: Question):
    """Pose une question sur un document déjà envoyé (RAG)."""
    doc = recuperer(doc_id)
    return poser_question(doc["index"], q.question)


@app.post("/documents/{doc_id}/validation")
def valider(doc_id: str, decision: DecisionHumaine):
    """Un humain valide ou corrige le niveau de confidentialité."""
    doc = recuperer(doc_id)
    resultat = doc["resultat"]
    try:
        resultat["validation"] = appliquer_decision_humaine(
            resultat["validation"], decision.confidentialite, resultat["classification"]["confidentialite"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return resultat["validation"]


def recuperer(doc_id: str) -> dict:
    if doc_id not in DOCUMENTS:
        raise HTTPException(status_code=404, detail="Document introuvable (le serveur a peut-être redémarré)")
    return DOCUMENTS[doc_id]
