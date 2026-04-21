import sys
from ocr_engine import OCREngine
from graph_manager import KnowledgeGraph
from exporter import Exporter


def run_app(image_path, category_tag):
    ocr = OCREngine()
    graph = KnowledgeGraph()

    latex_result = ocr.process(image_path)

    title = input("Introdu titlul lecției pentru această poză: ")

    status = graph.add_entry(title, latex_result, tags=[category_tag])
    print(status)

    # Exportă tot ce ține de acea categorie
    if input("Vrei să generezi documentul complet? (y/n): ")  == 'y':
        data = graph.get_all_by_tag(category_tag)
        file = Exporter.to_markdown(data, f"exports/{category_tag}_final.md")
        print(f"Document generat: {file}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_app(sys.argv[1], sys.argv[2])
    else:
        print("Utilizare: python main.py imagine.png algebra")