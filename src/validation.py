# validation.py
# Fonctionnalité 3 : repérer les cas incertains pour qu'un humain les vérifie
# (c'est ce qu'on appelle "human in the loop")

import os

from src.schemas import Classification

# seuil réglable dans le .env (par défaut 0.8 = 80 %)
SEUIL_CONFIANCE = float(os.getenv("SEUIL_CONFIANCE", "0.8"))
NIVEAUX = ["public", "interne", "confidentiel"]


def raisons_de_verifier(classification: Classification) -> list[str]:
    """Renvoie la liste des raisons pour lesquelles un humain doit vérifier.
    Liste vide = tout va bien, pas besoin de vérifier."""
    raisons = []
    if classification.confiance < SEUIL_CONFIANCE:
        raisons.append(f"confiance trop basse ({classification.confiance:.2f} < {SEUIL_CONFIANCE})")
    if not classification.citation_verifiee:
        raisons.append("la citation n'existe pas dans le document (hallucination ?)")
    if classification.type_document == "autre":
        raisons.append("type de document inconnu")
    return raisons


def verifier(classification: Classification) -> dict:
    """Décide si on valide automatiquement ou si un humain doit vérifier.
    Ici on ne pose PAS la question : c'est le terminal, l'API ou Streamlit qui le font."""
    raisons = raisons_de_verifier(classification)
    if not raisons:
        return {"statut": "validé automatiquement",
                "confidentialite_finale": classification.confidentialite, "raisons": []}
    return {"statut": "en attente de validation humaine",
            "confidentialite_finale": None, "raisons": raisons}


def appliquer_decision_humaine(validation: dict, niveau_choisi: str, proposition: str) -> dict:
    """Enregistre la décision de l'humain (utilisé par le terminal, l'API et Streamlit)."""
    if niveau_choisi not in NIVEAUX:
        raise ValueError(f"Niveau inconnu : {niveau_choisi} (choisir parmi {NIVEAUX})")
    statut = "validé par un humain" if niveau_choisi == proposition else "corrigé par un humain"
    return {**validation, "statut": statut, "confidentialite_finale": niveau_choisi}


def demander_dans_le_terminal(resultat: dict) -> dict:
    """Version terminal : affiche le problème et demande à l'humain de valider ou corriger."""
    classification, validation = resultat["classification"], resultat["validation"]
    print("\n⚠️  CAS INCERTAIN — validation humaine demandée")
    for r in validation["raisons"]:
        print(f"   - {r}")
    print(f"   Proposition du modèle : {classification['type_document']} / {classification['confidentialite']}")
    print(f"   Citation : « {classification['citation']} »")

    reponse = input("Tu valides ? (o = oui / n = non) : ").strip().lower()
    if reponse == "o":
        choix = classification["confidentialite"]
    else:
        choix = ""
        while choix not in NIVEAUX:
            choix = input("Quel est le bon niveau ? (public / interne / confidentiel) : ").strip().lower()
    return appliquer_decision_humaine(validation, choix, classification["confidentialite"])
