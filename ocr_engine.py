from pix2tex.cli import LatexOCR
from PIL import Image
import subprocess
import json
import ollama

class OCREngine:
    def __init__(self):
        self.model = LatexOCR()

    def process(self, image_path):
        img = Image.open(image_path)
        return self.model(img)

    def ollama_ocr(image_path):
        prompt = """
        Analyse the text and extract the mathematical text.
        - Use Markdown for structure.
        - Use LaTex for mathematical formulas (between $ or $$).
        - Identify titles and lists.
        - Ignore textbook lining and noise.
        """
        try:
            response = ollama.chat(
                model='ministral-3',
                messages=[{'role': 'user', 'content': prompt, 'images': [image_path]}]
            )
            return response['message']['content']
        except Exception as e:
            return f"Eroare la procesarea AI: {str(e)}"
