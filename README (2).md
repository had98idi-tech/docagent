# 📄 DocAgent

Agent IA qui analyse des documents PDF : extraction d'informations en JSON structuré, classification, questions-réponses (RAG) et évaluation par LLM-juge.

> 🚧 Projet en cours — README complet à venir.

## Fonctionnalités
- [x] Extraction PDF → JSON structuré (Pydantic + LLM via Groq)
- [x] Classification (type + confidentialité) avec justification citée et vérifiée
- [ ] Seuil de confiance + validation humaine
- [ ] RAG sur le document
- [ ] Évaluation « LLM as a judge »
- [ ] API FastAPI + démo Streamlit + Docker

## Installation
```bash
python -m venv venv && source venv/bin/activate   # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # puis mettre ta clé Groq dedans (gratuite sur console.groq.com)
python main.py data/exemple.pdf
```
