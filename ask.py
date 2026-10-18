# ask.py
# Poser des questions sur un PDF (RAG)
# Utilisation : python ask.py data/mon_document.pdf

import sys

from src.pdf_reader import lire_pages
from src.rag import IndexRAG, poser_question


def main():
    if len(sys.argv) < 2:
        print("Usage : python ask.py chemin/vers/document.pdf")
        return

    pages = lire_pages(sys.argv[1])
    index = IndexRAG(pages)

    print("\nPose ta question (ou tape 'q' pour quitter)")
    while True:
        question = input("\n❓ Question : ").strip()
        if question.lower() in ("q", "quit", "exit", ""):
            break
        r = poser_question(index, question)
        print(f"💬 {r['reponse']}")
        pages_sources = ", ".join(str(s["page"]) for s in r["sources"])
        print(f"📄 Sources : page(s) {pages_sources}")
        if not r["trouve_dans_document"]:
            print("⚠️ La réponse n'a pas été trouvée dans le document.")


if __name__ == "__main__":
    main()
