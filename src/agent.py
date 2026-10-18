# agent.py
# L'agent DocAgent, construit avec LangGraph.
# Un graphe = des étapes (noeuds) reliées par des flèches.
# Chaque noeud lit l'état (un dict partagé), fait son travail, et ajoute son résultat.
#
#   lire_pdf -> extraire -> classer -> verifier --(sûr)------> juger -> FIN
#                                               \--(incertain)-> marquer_pour_humain -> juger -> FIN

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from src.pdf_reader import lire_pdf, couper_texte
from src.extractor import extraire_infos
from src.classifier import classer_document
from src.validation import verifier
from src.judge import evaluer_extraction


class EtatAgent(TypedDict, total=False):
    chemin_pdf: str
    avec_juge: bool
    texte: str
    extraction: dict
    classification: dict
    validation: dict
    evaluation: dict | None
    etapes: list[str]  # pour garder une trace de ce que l'agent a fait


# ---------- les noeuds (= les étapes) ----------

def noeud_lire(etat: EtatAgent) -> dict:
    texte = couper_texte(lire_pdf(etat["chemin_pdf"]))
    return {"texte": texte, "etapes": ["lecture du PDF"]}


def noeud_extraire(etat: EtatAgent) -> dict:
    extraction = extraire_infos(etat["texte"])
    return {"extraction": extraction.model_dump(), "etapes": etat["etapes"] + ["extraction"]}


def noeud_classer(etat: EtatAgent) -> dict:
    classification = classer_document(etat["texte"])
    return {"classification": classification.model_dump(), "etapes": etat["etapes"] + ["classification"]}


def noeud_verifier(etat: EtatAgent) -> dict:
    from src.schemas import Classification
    validation = verifier(Classification(**etat["classification"]))
    return {"validation": validation, "etapes": etat["etapes"] + ["vérification de la confiance"]}


def noeud_marquer_pour_humain(etat: EtatAgent) -> dict:
    # ici on pourrait envoyer un mail, une notif Slack... on garde simple : on note juste l'info
    print("⚠️ Document mis de côté pour validation humaine :", ", ".join(etat["validation"]["raisons"]))
    return {"etapes": etat["etapes"] + ["mis en attente pour un humain"]}


def noeud_juger(etat: EtatAgent) -> dict:
    if not etat.get("avec_juge", True):
        return {"evaluation": None, "etapes": etat["etapes"] + ["juge désactivé"]}
    from src.schemas import ExtractionDocument
    evaluation = evaluer_extraction(etat["texte"], ExtractionDocument(**etat["extraction"]))
    return {"evaluation": evaluation, "etapes": etat["etapes"] + ["évaluation par le LLM-juge"]}


# ---------- la décision (flèche conditionnelle) ----------

def choisir_route(etat: EtatAgent) -> str:
    """Après la vérification : si c'est incertain on passe par l'humain, sinon on continue."""
    if etat["validation"]["statut"] == "en attente de validation humaine":
        return "incertain"
    return "sur"


# ---------- construction du graphe ----------

def construire_agent():
    graphe = StateGraph(EtatAgent)
    graphe.add_node("lire_pdf", noeud_lire)
    graphe.add_node("extraire", noeud_extraire)
    graphe.add_node("classer", noeud_classer)
    graphe.add_node("verifier", noeud_verifier)
    graphe.add_node("marquer_pour_humain", noeud_marquer_pour_humain)
    graphe.add_node("juger", noeud_juger)

    graphe.add_edge(START, "lire_pdf")
    graphe.add_edge("lire_pdf", "extraire")
    graphe.add_edge("extraire", "classer")
    graphe.add_edge("classer", "verifier")
    graphe.add_conditional_edges("verifier", choisir_route,
                                 {"sur": "juger", "incertain": "marquer_pour_humain"})
    graphe.add_edge("marquer_pour_humain", "juger")
    graphe.add_edge("juger", END)
    return graphe.compile()


agent = construire_agent()


def analyser_document(chemin_pdf: str, avec_juge: bool = True) -> dict:
    """Point d'entrée utilisé par main.py, l'API et Streamlit."""
    etat_final = agent.invoke({"chemin_pdf": chemin_pdf, "avec_juge": avec_juge})
    return {
        "extraction": etat_final["extraction"],
        "classification": etat_final["classification"],
        "validation": etat_final["validation"],
        "evaluation": etat_final.get("evaluation"),
        "etapes": etat_final["etapes"],
    }
