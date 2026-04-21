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
