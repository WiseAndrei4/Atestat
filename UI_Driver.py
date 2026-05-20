import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import json
import glob
from PIL import Image
import os
import easyocr
import ollama
from graph_manager import KnowledgeGraph

models_path = os.path.join(os.getcwd(), "ollama_storage")
if not os.path.exists(models_path):
    os.makedirs(models_path)
os.environ["OLLAMA_MODELS"] = models_path

class MathNoteApp(ctk.CTk):
    def load_archive_from_disk(self):
        if os.path.exists("archive.json"):
            try:
                with open("archive.json", "r", encoding="utf-8") as f:
                    self.archive_data = json.load(f)
            except:
                self.archive_data = []
    def __init__(self):
        super().__init__()
        self.archive_data = []
        self.load_archive_from_disk()

        self.model='ministral-3:3b'
        self.kg = KnowledgeGraph()

        self.title("Study Assistant")
        self.geometry("1100x600")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Study Assistant", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_upload = ctk.CTkButton(self.sidebar_frame, text="Procesează Folder", command=self.batch_process)
        self.btn_upload.grid(row=1, column=0, padx=20, pady=10)

        self.btn_sync_kg = ctk.CTkButton(self.sidebar_frame, text="Introdu Text",
                                         command=self.sync_graph_from_text)
        self.btn_sync_kg.grid(row=5, column=0, padx=20, pady=10)

        self.btn_export = ctk.CTkButton(self.sidebar_frame, text="Export Markdown", command=self.export_event)
        self.btn_export.grid(row=2, column=0, padx=20, pady=10)

        self.btn_archive = ctk.CTkButton(self.sidebar_frame, text="Vezi Arhiva", command=self.open_archive)
        self.btn_archive.grid(row=3, column=0, padx=20, pady=10)

        self.btn_graph = ctk.CTkButton(self.sidebar_frame, text="Knowledge Graph", command=self.show_graph)
        self.btn_graph.grid(row=4, column=0, padx=20, pady=10)

        self.btn_chat = ctk.CTkButton(self.sidebar_frame, text="Discută pe baza Arhivei", command=self.open_chat_window)
        self.btn_chat.grid(row=6, column=0, padx=20, pady=10)

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.label_status = ctk.CTkLabel(self.main_frame, text="Așteptare folder...", font=ctk.CTkFont(size=14))
        self.label_status.grid(row=0, column=0, padx=20, pady=10)

        self.textbox = ctk.CTkTextbox(self.main_frame, width=600, height=300)
        self.textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

    def process_single_image(self, img_path):
        prompt = "Extract the text from the image, without any formatations. Just extract the text as it is seen."
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt, 'images': [img_path]}]
            )
            return response['message']['content']
        except Exception as e:
            return f"Eroare: {str(e)}"

    def batch_process(self):
        folder_path = filedialog.askdirectory()
        if not folder_path: return

        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(glob.glob(os.path.join(folder_path, ext)))

        if not image_files: return

        self.textbox.delete("0.0", "end")
        for i, img_path in enumerate(image_files):
            file_name = os.path.basename(img_path)
            self.label_status.configure(text=f"Procesez {i + 1}/{len(image_files)}: {file_name}")
            self.update()

            try:
                existing_rels = self.kg.relations.all()
                existing_context = ""
                if existing_rels:
                    # Daca sunt prea multe relatii, primele 40
                    existing_context = "\n".join(
                        [f"- {r['source']} -> {r['relation']} -> {r['target']}" for r in existing_rels[:40]])

                # 2. Prompt cu context
                prompt = (
                    "Extract text exactly as seen, using LaTeX formatting for formulas.\n"
                    "Additionally, identify the main entities and map the relations between them.\n"
                    "RETURN ONLY A JSON OBJECT with two keys: 'text' and 'triplets'.\n\n"
                    "CRITICAL FOR KNOWLEDGE GRAPH CONSISTENCY:\n"
                    "Look at the existing knowledge graph relations below. If the new image contains the same "
                    "concepts or entities, you MUST use the EXACT same names/spelling to avoid duplicate or split nodes.\n"
                    f"Existing Graph Relations:\n{existing_context if existing_context else 'None (Graph is empty)'}\n\n"
                    "Format output exactly like this: {'text': '...', 'triplets': [['entity1', 'relation', 'entity2']]}"
                )

                response = ollama.chat(
                    model=self.model,
                    messages=[{
                        'role': 'user',
                        'content': prompt,
                        'images': [img_path]
                    }],
                    format='json'
                )

                raw_content = response['message']['content'].strip()
                if "```" in raw_content:
                    raw_content = raw_content.split("```")[1]
                    if raw_content.startswith("json"):
                        raw_content = raw_content[4:]

                data = json.loads(raw_content)
                result_text = data.get('text', '')
                triplets = data.get('triplets', [])

                unique_triplets = []
                for s, r, o in triplets:
                    s_clean, r_clean, o_clean = str(s).strip(), str(r).strip(), str(o).strip()

                    # Verificare existenta triplete
                    from tinydb import Query
                    Rel = Query()
                    exists = self.kg.relations.search(
                        (Rel.source == s_clean) &
                        (Rel.relation == r_clean) &
                        (Rel.target == o_clean)
                    )

                    if not exists:
                        unique_triplets.append([s_clean, r_clean, o_clean])

                # Update UI
                entry_header = f"\n\n{'=' * 20}\n {file_name}\n{'=' * 20}\n\n"
                self.textbox.insert("end", entry_header + result_text)
                self.textbox.see("end")

                # Adaugarea tripletelor
                self.kg.add_triplets(unique_triplets)

                # Arhivare
                self.archive_data.append({"file_name": file_name, "path": img_path, "text": result_text})
                with open("archive.json", "w", encoding="utf-8") as f:
                    json.dump(self.archive_data, f, indent=4)

            except Exception as e:
                self.textbox.insert("end", f"\n[EROARE] {file_name}: {str(e)}")

            self.update()

        self.label_status.configure(text="Gata!")

    def show_graph(self):
        if hasattr(self, "graph_win") and self.graph_win.winfo_exists():
            self.graph_win.destroy()

        self.graph_win = ctk.CTkToplevel(self)
        self.graph_win.title("Knowledge Graph")
        self.graph_win.geometry("900x700")

        self.graph_win.lift()
        self.graph_win.attributes("-topmost", True)

        self.kg.visualize(self.graph_win)

    def export_event(self):
        content = self.textbox.get("0.0", "end").strip()
        if not content or content.startswith("Rezultatul"):
            messagebox.showerror("Eroare", "Nu există text de exportat!")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".md",
                                                 filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# Notițe Scanate\n\n")
                f.write(content)
            messagebox.showinfo("Succes", f"Fișierul a fost salvat la: {file_path}")

    def open_archive(self):
        if not self.archive_data:
            messagebox.showinfo("Arhivă", "Arhiva este goală momentan.")
            return

        archive_window = ctk.CTkToplevel(self)
        archive_window.title("Arhivă Istoric")
        archive_window.geometry("900x700")
        archive_window.attributes("-topmost", True)

        scroll_frame = ctk.CTkScrollableFrame(archive_window)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Reverse chronological order
        for item in reversed(self.archive_data):
            item_frame = ctk.CTkFrame(scroll_frame)
            item_frame.pack(pady=10, fill="x")

            lbl_title = ctk.CTkLabel(item_frame, text=item["file_name"], font=("Arial", 12, "bold"))
            lbl_title.pack(pady=5)

            # Container pentru imagine și text (stanga-dreapta)
            content_row = ctk.CTkFrame(item_frame, fg_color="transparent")
            content_row.pack(fill="x", padx=10, pady=5)

            try:
                img = Image.open(item["path"])
                img.thumbnail((250, 250))
                img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 250))
                ctk.CTkLabel(content_row, image=img_ctk, text="").grid(row=0, column=0, padx=5)
            except:
                ctk.CTkLabel(content_row, text="Imagine negăsită").grid(row=0, column=0, padx=5)

            txt = ctk.CTkTextbox(content_row, width=550, height=250)
            txt.insert("0.0", item["text"])
            txt.grid(row=0, column=1, padx=5)

    def sync_graph_from_text(self):
        content = self.textbox.get("0.0", "end").strip()
        if not content or len(content) < 10:
            messagebox.showwarning("Atenție", "Textul este prea scurt pentru a extrage entități!")
            return

        self.label_status.configure(text="Se extrag entitățile din text...")
        self.update()

        try:

            existing_rels = self.kg.relations.all()
            existing_context = ""
            if existing_rels:
                # Daca sunt prea multe relatii, primele 40
                existing_context = "\n".join(
                    [f"- {r['source']} -> {r['relation']} -> {r['target']}" for r in existing_rels[:40]])
            prompt = (
                "Identify the main entities and map the relations between them.\n"
                "RETURN ONLY A JSON OBJECT with one key: 'triplets'.\n\n"
                "CRITICAL FOR KNOWLEDGE GRAPH CONSISTENCY:\n"
                "Look at the existing knowledge graph relations below. If the new image contains the same "
                "concepts or entities, you MUST use the EXACT same names/spelling to avoid duplicate or split nodes.\n"
                f"Existing Graph Relations:\n{existing_context if existing_context else 'None (Graph is empty)'}\n\n"
                "Format output exactly like this: {'triplets': [['entity1', 'relation', 'entity2']]}."
                f"Text: {content}"
            )

            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )

            data = json.loads(response['message']['content'])
            triplets = data.get('triplets', [])

            if triplets:
                self.kg.add_triplets(triplets)
                messagebox.showinfo("Succes", f"Am adăugat {len(triplets)} relații noi în Knowledge Graph!")
            else:
                messagebox.showwarning("Info", "Nu am putut identifica relații clare în text.")

        except Exception as e:
            messagebox.showerror("Eroare", f"Eroare la procesarea textului: {str(e)}")

        self.label_status.configure(text="Gata!")

    def open_chat_window(self):
        if hasattr(self, "chat_win") and self.chat_win.winfo_exists():
            self.chat_win.lift()
            return

        self.chat_win = ctk.CTkToplevel(self)
        self.chat_win.title("Asistent Inteligent - Întrebări pe baza Grafului")
        self.chat_win.geometry("500x600")
        self.chat_win.attributes("-topmost", True)

        self.chat_win.grid_columnconfigure(0, weight=1)
        self.chat_win.grid_rowconfigure(0, weight=1)

        # Message Output
        self.chat_display = ctk.CTkTextbox(self.chat_win, state="disabled", wrap="word")
        self.chat_display.grid(row=0, column=0, padx=10, pady=10, columnspan=2, sticky="nsew")

        # User Input
        self.chat_input = ctk.CTkEntry(self.chat_win, placeholder_text="Pune o întrebare despre graf/notițe...")
        self.chat_input.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.chat_input.bind("<Return>", lambda event: self.send_chat_message())

        # Send Button
        self.btn_send = ctk.CTkButton(self.chat_win, text="Trimite", width=80, command=self.send_chat_message)
        self.btn_send.grid(row=1, column=1, padx=(5, 10), pady=10)

        #Welcome Message
        self.append_to_chat("Asistent",
                            "Salut! Pune-mi orice întrebare legată de conceptele și relațiile extrase din documentele tale.")

    def append_to_chat(self, sender, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{sender}: {message}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_chat_message(self):
        user_text = self.chat_input.get().strip()
        if not user_text:
            return

        self.append_to_chat("Tu", user_text)
        self.chat_input.delete(0, "end")

        # KG Context
        all_relations = self.kg.relations.all()

        context_str = ""
        for rel in all_relations:
            context_str += f"- {rel['source']} -> {rel['relation']} -> {rel['target']}\n"

        if not context_str:
            context_str = "Baza de date actuală este goală. Nu există relații extrase încă."

        try:
            prompt = (
                "You are an expert research assistant. Answer the user's question using ONLY the provided Knowledge Graph context. "
                "If the answer cannot be found or deduced from the relations, state politely that you do not have that information.\n\n"
                f"Knowledge Graph Context (Relations):\n{context_str}\n\n"
                f"User Question: {user_text}"
            )

            response = ollama.chat(
                model=self.model,  # Rapid și excelent pentru text formatat
                messages=[{'role': 'user', 'content': prompt}]
            )

            ai_response = response['message']['content']
            self.append_to_chat("Asistent", ai_response)

        except Exception as e:
            self.append_to_chat("Sistem", f"Eroare la generarea răspunsului: {str(e)}")

if __name__ == "__main__":
    app = MathNoteApp()
    app.mainloop()