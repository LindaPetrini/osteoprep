"""
One-time seed script to populate the topics table with Biology and Chemistry stubs.
Uses synchronous SQLite (not async) since it's a one-off script.
Run: python seed_topics.py
"""
import sqlite3
import os

TOPICS = [
    # Biology topics
    {"slug": "cellula-eucariotica", "title_it": "Cellula eucariotica", "title_en": "Eukaryotic cell", "subject": "biology", "order_in_subject": 1},
    {"slug": "membrana-cellulare", "title_it": "Membrana cellulare", "title_en": "Cell membrane", "subject": "biology", "order_in_subject": 2},
    {"slug": "nucleo-cellulare", "title_it": "Nucleo cellulare", "title_en": "Cell nucleus", "subject": "biology", "order_in_subject": 3},
    {"slug": "mitosi-meiosi", "title_it": "Mitosi e meiosi", "title_en": "Mitosis and meiosis", "subject": "biology", "order_in_subject": 4},
    {"slug": "dna-rna-proteine", "title_it": "DNA, RNA e sintesi proteica", "title_en": "DNA, RNA and protein synthesis", "subject": "biology", "order_in_subject": 5},
    {"slug": "respirazione-cellulare", "title_it": "Respirazione cellulare e ATP", "title_en": "Cellular respiration and ATP", "subject": "biology", "order_in_subject": 6},
    {"slug": "fotosintesi", "title_it": "Fotosintesi clorofilliana", "title_en": "Photosynthesis", "subject": "biology", "order_in_subject": 7},
    {"slug": "genetica-mendeliana", "title_it": "Genetica mendeliana", "title_en": "Mendelian genetics", "subject": "biology", "order_in_subject": 8},
    {"slug": "evoluzione-selezione", "title_it": "Evoluzione e selezione naturale", "title_en": "Evolution and natural selection", "subject": "biology", "order_in_subject": 9},
    {"slug": "sistema-nervoso", "title_it": "Sistema nervoso", "title_en": "Nervous system", "subject": "biology", "order_in_subject": 10},
    # Chemistry topics
    {"slug": "atomo-struttura", "title_it": "Struttura dell'atomo", "title_en": "Atomic structure", "subject": "chemistry", "order_in_subject": 1},
    {"slug": "tavola-periodica", "title_it": "Tavola periodica degli elementi", "title_en": "Periodic table", "subject": "chemistry", "order_in_subject": 2},
    {"slug": "legami-chimici", "title_it": "Legami chimici", "title_en": "Chemical bonds", "subject": "chemistry", "order_in_subject": 3},
    {"slug": "acidi-basi-ph", "title_it": "Acidi, basi e pH", "title_en": "Acids, bases and pH", "subject": "chemistry", "order_in_subject": 4},
    {"slug": "reazioni-chimiche", "title_it": "Reazioni chimiche e stechiometria", "title_en": "Chemical reactions and stoichiometry", "subject": "chemistry", "order_in_subject": 5},
    {"slug": "ossidoriduzione", "title_it": "Reazioni di ossidoriduzione", "title_en": "Oxidation-reduction reactions", "subject": "chemistry", "order_in_subject": 6},
    {"slug": "carboidrati", "title_it": "Carboidrati", "title_en": "Carbohydrates", "subject": "chemistry", "order_in_subject": 7},
    {"slug": "lipidi", "title_it": "Lipidi", "title_en": "Lipids", "subject": "chemistry", "order_in_subject": 8},
    {"slug": "proteine-struttura", "title_it": "Struttura delle proteine", "title_en": "Protein structure", "subject": "chemistry", "order_in_subject": 9},
    {"slug": "enzimi", "title_it": "Enzimi e catalisi", "title_en": "Enzymes and catalysis", "subject": "chemistry", "order_in_subject": 10},
]

def seed():
    db_path = "data/osteoprep.db"
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}. Run alembic upgrade head first.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    inserted = 0
    skipped = 0
    for topic in TOPICS:
        try:
            cur.execute(
                """INSERT OR IGNORE INTO topics
                   (slug, title_it, title_en, subject, order_in_subject, content_it, content_en, generated_at)
                   VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL)""",
                (topic["slug"], topic["title_it"], topic["title_en"],
                 topic["subject"], topic["order_in_subject"])
            )
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"ERROR inserting {topic['slug']}: {e}")

    conn.commit()
    conn.close()
    print(f"Seed complete: {inserted} inserted, {skipped} skipped (already existed)")

if __name__ == "__main__":
    seed()
