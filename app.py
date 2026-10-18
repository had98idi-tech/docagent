# app.py
# Démo visuelle avec Streamlit
# Lancer : streamlit run app.py   -> s'ouvre dans le navigateur

import tempfile
from pathlib import Path

import streamlit as st

from src.agent import analyser_document
from src.pdf_reader import lire_pages
from src.rag import IndexRAG, poser_question
from src.validation import NIVEAUX, appliquer_decision_humaine

st.set_page_config(page_title="DocAgent", page_icon="📄", layout="wide")
st.title("📄 DocAgent")
st.caption("Agent IA d'analyse de documents PDF — extraction, classification, validation humaine, RAG, LLM-juge")

# st.session_state = la "mémoire" de la page (sinon tout est perdu à chaque clic)
if "resultat" not in st.session_state:
    st.session_state.resultat = None
    st.session_state.index = None
    st.session_state.historique = []

# ---------- 1. Envoi du PDF ----------
with st.sidebar:
    st.header("1. Ton document")
    fichier = st.file_uploader("Choisis un PDF", type="pdf")
    avec_juge = st.checkbox("Évaluer avec le LLM-juge", value=True)
    lancer = st.button("Analyser", type="primary", disabled=fichier is None)

if lancer and fichier:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(fichier.getvalue())
        chemin = tmp.name
    with st.spinner("L'agent analyse le document..."):
        st.session_state.resultat = analyser_document(chemin, avec_juge=avec_juge)
        st.session_state.index = IndexRAG(lire_pages(chemin))
        st.session_state.historique = []
    Path(chemin).unlink(missing_ok=True)

res = st.session_state.resultat
if res is None:
    st.info("👈 Envoie un PDF dans la barre de gauche pour commencer.")
    st.stop()

st.caption("Étapes de l'agent : " + " → ".join(res["etapes"]))
col1, col2 = st.columns(2)

# ---------- 2. Extraction ----------
with col1:
    st.subheader("Informations extraites")
    ext = res["extraction"]
    st.markdown(f"**{ext['titre']}** · _{ext['type_document']}_")
    st.write(ext["resume"])
    if ext["points_importants"]:
        st.markdown("**Points importants**")
        for p in ext["points_importants"]:
            st.markdown(f"- {p}")
    if ext["personnes"]:
        st.markdown("**Personnes** : " + ", ".join(
            p["nom"] + (f" ({p['role']})" if p.get("role") else "") for p in ext["personnes"]))
    if ext["dates"]:
        st.markdown("**Dates** : " + ", ".join(f"{d['date']} ({d['description']})" for d in ext["dates"]))
    with st.expander("Voir le JSON"):
        st.json(ext)

# ---------- 3. Classification + validation humaine ----------
with col2:
    st.subheader("Classification")
    cl, val = res["classification"], res["validation"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Type", cl["type_document"])
    c2.metric("Confidentialité", cl["confidentialite"])
    c3.metric("Confiance", f"{cl['confiance']:.0%}")
    st.markdown(f"**Justification** : {cl['justification']}")
    st.markdown(f"> {cl['citation']}")
    st.caption("✅ Citation trouvée dans le document" if cl["citation_verifiee"]
               else "⚠️ Citation introuvable dans le document")

    if val["statut"] == "en attente de validation humaine":
        st.warning("Cas incertain : " + " ; ".join(val["raisons"]))
        choix = st.radio("Bon niveau de confidentialité ?", NIVEAUX,
                         index=NIVEAUX.index(cl["confidentialite"]), horizontal=True)
        if st.button("Valider ma décision"):
            res["validation"] = appliquer_decision_humaine(val, choix, cl["confidentialite"])
            st.rerun()
    else:
        st.success(f"{val['statut']} → {val['confidentialite_finale']}")

    # ---------- 4. LLM-juge ----------
    if res["evaluation"]:
        st.subheader("Évaluation par le LLM-juge")
        ev = res["evaluation"]
        j1, j2, j3, j4 = st.columns(4)
        j1.metric("Global", f"{ev['score_global']}/5")
        j2.metric("Fidélité", f"{ev['fidelite']}/5")
        j3.metric("Complétude", f"{ev['completude']}/5")
        j4.metric("Sans hallucination", f"{ev['absence_hallucination']}/5")
        st.write(ev["commentaire"])
        for p in ev["problemes"]:
            st.markdown(f"- ⚠️ {p}")
        st.caption(f"Juge : {ev['modele_juge']}")

# ---------- 5. Questions (RAG) ----------
st.divider()
st.subheader("💬 Pose une question sur le document")
for echange in st.session_state.historique:
    st.chat_message("user").write(echange["question"])
    with st.chat_message("assistant"):
        st.write(echange["reponse"])
        pages = ", ".join(str(s["page"]) for s in echange["sources"])
        st.caption(f"📄 Sources : page(s) {pages}"
                   + ("" if echange["trouve_dans_document"] else " — ⚠️ réponse non trouvée dans le document"))

if q := st.chat_input("Ta question..."):
    with st.spinner("Recherche dans le document..."):
        st.session_state.historique.append(poser_question(st.session_state.index, q))
    st.rerun()
