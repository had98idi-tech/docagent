# main.py
# Analyse complète d'un PDF dans le terminal
# Utilisation : python main.py data/mon_document.pdf
#               python main.py data/mon_document.pdf --sans-juge   (plus rapide)

import sys
import json
from pathlib import Path

from src.agent import analyser_document
from src.validation import demander_dans_le_terminal


def main():
    if len(sys.argv) < 2:
        print("Usage : python main.py chemin/vers/document.pdf [--sans-juge]")
        return

    chemin_pdf = sys.argv[1]
    avec_juge = "--sans-juge" not in sys.argv

    print(f"Analyse de {chemin_pdf}...")
    resultat = analyser_document(chemin_pdf, avec_juge=avec_juge)

    # si l'agent a mis le document de côté -> on demande à l'humain ici
    if resultat["validation"]["statut"] == "en attente de validation humaine":
        resultat["validation"] = demander_dans_le_terminal(resultat)

    json_txt = json.dumps(resultat, indent=2, ensure_ascii=False)
    print(json_txt)

    # sauvegarde dans outputs/
    Path("outputs").mkdir(exist_ok=True)
    sortie = Path("outputs") / (Path(chemin_pdf).stem + ".json")
    sortie.write_text(json_txt, encoding="utf-8")

    print(f"\nRésultat sauvegardé dans {sortie}")
    print(f"Statut : {resultat['validation']['statut']}")
    if resultat["evaluation"]:
        print(f"Note du LLM-juge : {resultat['evaluation']['score_global']}/5")


if __name__ == "__main__":
    main()
