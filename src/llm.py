# llm.py
# Fonction commune pour appeler le LLM (Groq) et récupérer un JSON validé par Pydantic.
# Comme ça on n'écrit pas le même code dans extractor.py ET classifier.py

import os
import json

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from groq import Groq

load_dotenv(override=True)  # override=True -> la clé du .env passe en priorité
client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODELE = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def appeler_llm_json(prompt_systeme: str, texte: str, schema_pydantic: type[BaseModel], essais_max: int = 2):
    """Envoie le texte au LLM et renvoie un objet Pydantic valide (ou une erreur)."""
    # on ajoute le schéma JSON (généré par Pydantic) à la fin du prompt
    schema = json.dumps(schema_pydantic.model_json_schema(), ensure_ascii=False)
    messages = [
        {"role": "system", "content": prompt_systeme + "\n\nRéponds UNIQUEMENT avec un JSON valide qui respecte ce schéma :\n" + schema},
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
            return schema_pydantic.model_validate_json(contenu)
        except ValidationError as e:
            print(f"JSON invalide (essai {essai + 1}), on redemande au modèle...")
            # on renvoie l'erreur au LLM pour qu'il corrige
            messages.append({"role": "assistant", "content": contenu})
            messages.append({"role": "user", "content": f"Ton JSON est invalide : {e}. Corrige-le."})

    raise ValueError("Impossible d'obtenir un JSON valide après plusieurs essais")
