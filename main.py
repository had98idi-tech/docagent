# main.py
# Utilisation : python main.py data/mon_document.pdf

import sys
from pathlib import Path

from src.pdf_reader import lire_pdf, couper_texte
from src.extractor import extraire_infos


def main():
    if len(sys.argv) < 2:
        print("Usage : python main.py chemin/vers/document.pdf")
        return

    chemin_pdf = sys.argv[1]
    print(f"Lecture de {chemin_pdf}...")
    texte = couper_texte(lire_pdf(chemin_pdf))

    print("Extraction avec Mistral...")
    resultat = extraire_infos(texte)

    # affichage + sauvegarde du JSON dans outputs/
    json_txt = resultat.model_dump_json(indent=2)
    print(json_txt)
    Path("outputs").mkdir(exist_ok=True)
    sortie = Path("outputs") / (Path(chemin_pdf).stem + ".json")
    sortie.write_text(json_txt, encoding="utf-8")
    print(f"\nRésultat sauvegardé dans {sortie}")


if __name__ == "__main__":
    main()
