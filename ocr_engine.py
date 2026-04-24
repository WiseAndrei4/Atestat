from pix2tex.cli import LatexOCR
from PIL import Image
import subprocess
import json
import ollama

class OCREngine:
    def __init__(self):
        # Încarcă modelele în VRAM (dacă există GPU) sau RAM
        self.model = LatexOCR()

    def process(self, image_path):
        img = Image.open(image_path)
        return self.model(img)

    def advanced_vision_ocr(image_path):
        prompt = """
        Analizează imaginea și extrage textul și formulele matematice.
        - Folosește Markdown pentru structură.
        - Folosește LaTeX pentru toate formulele matematice (încadrate în $ sau $$).
        - Identifică titlurile și listele.
        - Ignoră liniile de caiet și zgomotul.
        """
        try:
            response = ollama.chat(
                model='llava',
                messages=[{'role': 'user', 'content': prompt, 'images': [image_path]}]
            )
            return response['message']['content']
        except Exception as e:
            return f"Eroare la procesarea AI: {str(e)}"
