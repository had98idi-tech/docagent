# extractor.py
# Étape 2 : envoyer le texte au LLM (via Groq, gratuit) et récupérer un JSON
# qui respecte le schéma Pydantic

import os
import json

from dotenv import load_dotenv
from pydantic import ValidationError
from groq import Groq

from src.schemas import ExtractionDocument

load_dotenv(override=True)  # override=True -> la clé du .env passe en priorité
client = Groq(api_key=os.environ["GROQ_API_KEY"])
# le nom du modèle est dans le .env, comme ça on peut le changer sans toucher au code
MODELE = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

PROMPT_SYSTEME = """Tu es un assistant qui extrait les informations clés d'un document.
Réponds UNIQUEMENT avec un JSON valide qui respecte ce schéma :
{schema}
N'invente rien : si une info n'est pas dans le document, laisse la liste vide."""


def extraire_infos(texte: str, essais_max: int = 2) -> ExtractionDocument:
    # on donne le schéma JSON généré par Pydantic directement au LLM
    schema = json.dumps(ExtractionDocument.model_json_schema(), ensure_ascii=False)
    messages = [
        {"role": "system", "content": PROMPT_SYSTEME.format(schema=schema)},
        {"role": "user", "content": f"Document :\n{texte}"},
    ]

    for essai in range(essais_max):
        reponse = client.chat.completions.create(
            model=MODELE,
            messages=messages,
            response_format={"type": "json_object"},  # force une sortie JSON
            temperature=0,  # on veut des résultats stables
        )
        contenu = reponse.choices[0].message.content
        try:
            # Pydantic vérifie que le JSON a la bonne forme
            return ExtractionDocument.model_validate_json(contenu)
        except ValidationError as e:
            print(f"JSON invalide (essai {essai + 1}), on redemande au modèle...")
            # on renvoie l'erreur au LLM pour qu'il corrige
            messages.append({"role": "assistant", "content": contenu})
            messages.append({"role": "user", "content": f"Ton JSON est invalide : {e}. Corrige-le."})

    raise ValueError("Impossible d'obtenir un JSON valide après plusieurs essais")
