from pix2tex.cli import LatexOCR
from PIL import Image
import subprocess
import json
import ollama

def convert_math_to_latex(image_path):
    model = LatexOCR()
    img = Image.open(image_path)
    latex_string = model(img)

    return latex_string

class LocalKnowledgeProcessor:
    def __init__(self):
        print("Încărcare Pix2TeX local...")
        self.ocr_model = LatexOCR()

    def get_latex(self, img_path):
        img = Image.open(img_path)
        return self.ocr_model(img)

    def process_with_local_llm(self, img_path, raw_latex):
        prompt = f"""
        Analizează această imagine de matematică și codul LaTeX brut: {raw_latex}
        Returnează un JSON strict pentru un Knowledge Graph cu:
        - main_topic
        - entities (id, name, content_latex, type)
        - relations (source, target, type)
        """
        response = ollama.chat(
            model='llava',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [img_path]
            }]
        )
        return response['message']['content']


def update_local_graph(new_data, graph_file='knowledge_graph.json'):
    try:
        with open(graph_file, 'r') as f:
            graph = json.load(f)
    except FileNotFoundError:
        graph = {"nodes": [], "edges": []}
    return graph

