from sympy import false
from tinydb import TinyDB, Query
import re
import os
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ollama
import json
import customtkinter as ctkx
from pyvis.network import Network
import webbrowser

class KnowledgeGraph:
    def __init__(self, db_path='database/db_local.json'):
        os.makedirs('database', exist_ok=True)
        self.db = TinyDB(db_path)
        self.concepts = self.db.table('concepts')
        self.relations = self.db.table('relations')  # Tabel nou pentru legături

    def _generate_slug(self, text):
        return re.sub(r'\W+', '-', text.lower()).strip('-')

    def add_triplets(self, triplets):
        if not triplets:
            return False
        try:

            for s, r, o in triplets:
                self.relations.insert({'source': str(s).strip(),
                                       'relation': str(r).strip(),
                                       'target': str(o).strip()})
            return True
        except Exception as e:
            return False

    def visualize(self, master_window=None):
        all_rels = self.relations.all()
        if not all_rels:
            print("Graful e gol!")
            return

        net = Network(height="750px", width="100%", bgcolor="#2b2b2b", font_color="white", directed=True)

        for rel in all_rels:
            s, r, o = rel['source'], rel['relation'], rel['target']
            # Adaugam nodurile si muchia
            net.add_node(s, label=s, title=s, color="#1f538d")
            net.add_node(o, label=o, title=o, color="#1f538d")
            net.add_edge(s, o, label=r, color="#ffffff")

        # Fizica
        net.toggle_physics(True)

        # Save
        path = "knowledge_graph.html"
        net.save_graph(path)
        webbrowser.open(path)