# main.py
# Utilisation : python main.py data/mon_document.pdf

import sys
import json
from pathlib import Path

from src.pdf_reader import lire_pdf, couper_texte
from src.extractor import extraire_infos
from src.classifier import classer_document


def main():
    if len(sys.argv) < 2:
        print("Usage : python main.py chemin/vers/document.pdf")
        return

    chemin_pdf = sys.argv[1]
    print(f"Lecture de {chemin_pdf}...")
    texte = couper_texte(lire_pdf(chemin_pdf))

    print("1) Extraction des informations...")
    extraction = extraire_infos(texte)

    print("2) Classification du document...")
    classification = classer_document(texte)

    # on regroupe les 2 résultats dans un seul JSON
    resultat = {
        "extraction": extraction.model_dump(),
        "classification": classification.model_dump(),
    }
    json_txt = json.dumps(resultat, indent=2, ensure_ascii=False)
    print(json_txt)

    # sauvegarde dans outputs/
    Path("outputs").mkdir(exist_ok=True)
    sortie = Path("outputs") / (Path(chemin_pdf).stem + ".json")
    sortie.write_text(json_txt, encoding="utf-8")
    print(f"\nRésultat sauvegardé dans {sortie}")


if __name__ == "__main__":
    main()
