# schemas.py
# Ici on définit la "forme" du JSON qu'on veut obtenir avec Pydantic.
# Si le LLM renvoie un JSON qui ne respecte pas ce format -> erreur de validation (c'est voulu !)

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ---------- Fonctionnalité 1 : extraction ----------

class Personne(BaseModel):
    nom: str = Field(description="Nom de la personne ou de l'organisation")
    role: Optional[str] = Field(default=None, description="Son rôle dans le document (ex : signataire, client...)")


class DateCle(BaseModel):
    date: str = Field(description="La date, idéalement au format AAAA-MM-JJ")
    description: str = Field(description="À quoi correspond cette date")


class ExtractionDocument(BaseModel):
    titre: str
    type_document: str = Field(description="ex : contrat, facture, rapport, CV, article...")
    dates: list[DateCle] = []
    personnes: list[Personne] = []
    points_importants: list[str] = Field(default=[], description="3 à 5 points clés du document")
    resume: str = Field(description="Résumé en 2-3 phrases")


# ---------- Fonctionnalité 2 : classification ----------

# Literal = le LLM est OBLIGÉ de choisir dans cette liste (sinon Pydantic refuse)
TypesDocument = Literal["contrat", "facture", "cv", "rapport", "cours", "article", "courrier", "autre"]
NiveauxConfidentialite = Literal["public", "interne", "confidentiel"]


class Classification(BaseModel):
    type_document: TypesDocument
    confidentialite: NiveauxConfidentialite
    justification: str = Field(description="Pourquoi ce choix, en 1-2 phrases")
    citation: str = Field(description="Passage EXACT copié du document qui justifie le niveau de confidentialité")
    confiance: float = Field(ge=0, le=1, description="Confiance du modèle entre 0 et 1")
    citation_verifiee: bool = Field(default=False, description="Rempli par le code, pas par le LLM")
