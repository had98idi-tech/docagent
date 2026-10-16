# schemas.py
# Ici on définit la "forme" du JSON qu'on veut obtenir avec Pydantic.
# Si le LLM renvoie un JSON qui ne respecte pas ce format -> erreur de validation (c'est voulu !)

from typing import Optional
from pydantic import BaseModel, Field


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
