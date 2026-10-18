# Dockerfile
# Une "boîte" qui contient Python + le projet + toutes les librairies.
# Comme ça le projet marche pareil sur n'importe quel ordinateur.

FROM python:3.11-slim

WORKDIR /app

# 1) torch en version CPU (beaucoup plus léger que la version GPU)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 2) les autres librairies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) on télécharge le modèle d'embeddings PENDANT la construction
#    -> pas d'attente au premier lancement
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

# 4) le code du projet
COPY . .

# 8501 = Streamlit, 8000 = API
EXPOSE 8501 8000

# par défaut on lance la démo Streamlit
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
