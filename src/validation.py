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


def validation_humaine(classification: Classification, raisons: list[str]) -> dict:
    """Affiche le problème dans le terminal et demande à l'humain de valider ou corriger."""
    print("\n⚠️  CAS INCERTAIN — validation humaine demandée")
    for r in raisons:
        print(f"   - {r}")
    print(f"   Proposition du modèle : {classification.type_document} / {classification.confidentialite}")
    print(f"   Citation : « {classification.citation} »")

    reponse = input("Tu valides ? (o = oui / n = non) : ").strip().lower()
    if reponse == "o":
        return {"statut": "validé par un humain", "confidentialite_finale": classification.confidentialite}

    # l'humain corrige le niveau de confidentialité
    nouveau = ""
    while nouveau not in NIVEAUX:
        nouveau = input("Quel est le bon niveau ? (public / interne / confidentiel) : ").strip().lower()
    return {"statut": "corrigé par un humain", "confidentialite_finale": nouveau}


def verifier(classification: Classification) -> dict:
    """Point d'entrée : décide si on valide automatiquement ou si on demande à un humain."""
    raisons = raisons_de_verifier(classification)
    if not raisons:
        return {"statut": "validé automatiquement", "confidentialite_finale": classification.confidentialite, "raisons": []}

    decision = validation_humaine(classification, raisons)
    decision["raisons"] = raisons
    return decision
