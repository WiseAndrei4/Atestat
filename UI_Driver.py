import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import glob
from pix2tex.cli import LatexOCR
from PIL import Image


class MathNoteApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Inițializăm motorul OCR (Poate dura câteva secunde)
        self.model = None

        self.title("MathKnowledge Graph OCR")
        self.geometry("1100x600")

        # --- UI LAYOUT (Sidebar & Main) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="MATH OCR", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_upload = ctk.CTkButton(self.sidebar_frame, text="Procesează Folder", command=self.batch_process)
        self.btn_upload.grid(row=1, column=0, padx=20, pady=10)

        self.btn_export = ctk.CTkButton(self.sidebar_frame, text="Export Markdown", command=self.export_event)
        self.btn_export.grid(row=2, column=0, padx=20, pady=10)

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.label_status = ctk.CTkLabel(self.main_frame, text="Așteptare folder...", font=ctk.CTkFont(size=14))
        self.label_status.grid(row=0, column=0, padx=20, pady=10)

        self.textbox = ctk.CTkTextbox(self.main_frame, width=600, height=300)
        self.textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

    def load_model(self):
        """Încarcă modelul doar când e nevoie, pentru a nu bloca pornirea aplicației."""
        if self.model is None:
            self.label_status.configure(text="Se încarcă modelul AI (te rugăm așteaptă)...")
            self.update()
            self.model = LatexOCR()

    def batch_process(self):
        # 1. Selectăm folderul
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return

        # 2. Căutăm pozele
        extensions = ['*.jpg', '*.jpeg', '*.png']
        image_files = []
        for ext in extensions:
            image_files.extend(glob.glob(os.path.join(folder_path, ext)))

        if not image_files:
            messagebox.showwarning("Atenție", "Nu am găsit imagini în folderul selectat!")
            return

        import ollama
        self.textbox.delete("0.0", "end")
        self.label_status.configure(text=f"Inițializare AI pentru {len(image_files)} imagini...")
        self.update()

        full_content = ""

        # 3. Iterăm prin fiecare imagine
        for i, img_path in enumerate(image_files):
            file_name = os.path.basename(img_path)
            self.label_status.configure(text=f"AI procesează {i + 1}/{len(image_files)}: {file_name}")
            self.update()

            prompt = f"""
            Analizează imaginea '{file_name}' de matematică.
            - Extrage textul și formulele în LaTeX ($ pentru inline, $$ pentru bloc).
            - Păstrează structura (Titlu, Exemple, Teoreme).
            - Curăță orice eroare de scriere de mână.
            """

            try:
                # Trimitem imaginea curentă la Ollama
                response = ollama.chat(
                    model='moondream',
                    messages=[{'role': 'user', 'content': prompt, 'images': [img_path]}]
                )

                result = response['message']['content']

                # Formatăm frumos în interfață
                entry_header = f"\n\n{'=' * 20}\n FIȘIER: {file_name}\n{'=' * 20}\n\n"
                self.textbox.insert("end", entry_header + result)
                self.textbox.see("end")  # Auto-scroll la final
                full_content += entry_header + result

            except Exception as e:
                error_msg = f"\n\n [EROARE] la fișierul {file_name}: {str(e)}"
                self.textbox.insert("end", error_msg)

        self.label_status.configure(text="Procesare Batch Finalizată!")

    def export_event(self):
        content = self.textbox.get("0.0", "end").strip()
        if not content or content.startswith("Rezultatul"):
            messagebox.showerror("Eroare", "Nu există text de exportat!")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".md",
                                                 filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# Notițe Matematice Scanate\n\n")
                f.write(content)
            messagebox.showinfo("Succes", f"Fișierul a fost salvat la: {file_path}")


if __name__ == "__main__":
    app = MathNoteApp()
    app.mainloop()