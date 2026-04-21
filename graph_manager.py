from tinydb import TinyDB, Query
import re

class KnowledgeGraph:
    def __init__(self, db_path='database/db_local.json'):
        self.db = TinyDB(db_path)
        self.concepts = self.db.table('concepts')

    def _generate_slug(self, text):
        return re.sub(r'\W+', '-', text.lower()).strip('-')

    def add_entry(self, title, content_latex, tags=None):
        slug = self._generate_slug(title)
        Concept = Query()
        existing = self.concepts.get(Concept.id == slug)

        if existing:
            if content_latex not in existing['content']:
                new_content = existing['content'] + "\n\n" + content_latex
                self.concepts.update({'content': new_content}, Concept.id == slug)
                return f"Actualizat: {title}"
        else:
            self.concepts.insert({
                'id': slug,
                'title': title,
                'content': content_latex,
                'tags': tags or []
            })
            return f"Adăugat: {title}"

    def get_all_by_tag(self, tag):
        Concept = Query()
        return self.concepts.search(Concept.tags.any([tag]))