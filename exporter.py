class Exporter:
    @staticmethod
    def to_markdown(entries, filename="curs_complet.md"):
        with open(filename, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(f"# {entry['title']}\n\n")
                f.write(f"$$\n{entry['content']}\n$$\n\n")
                f.write("---\n")
        return filename