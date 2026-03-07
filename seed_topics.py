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
    {"slug": "mitocondri", "title_it": "Mitocondri e respirazione cellulare", "title_en": "Mitochondria and cellular respiration", "subject": "biology", "order_in_subject": 11},
    {"slug": "tessuti-animali", "title_it": "Tessuti animali", "title_en": "Animal tissues", "subject": "biology", "order_in_subject": 12},
    {"slug": "sistemi-organo", "title_it": "Sistemi d'organo umani", "title_en": "Human organ systems", "subject": "biology", "order_in_subject": 13},
    {"slug": "virus-procarioti", "title_it": "Virus e procarioti", "title_en": "Viruses and prokaryotes", "subject": "biology", "order_in_subject": 14},
    {"slug": "biotecnologie-dna", "title_it": "Biotecnologie e DNA ricombinante", "title_en": "Biotechnology and recombinant DNA", "subject": "biology", "order_in_subject": 15},
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
    {"slug": "soluzioni-proprieta", "title_it": "Soluzioni e proprietà", "title_en": "Solutions and properties", "subject": "chemistry", "order_in_subject": 11},
    {"slug": "equilibrio-chimico", "title_it": "Equilibrio chimico e tamponi", "title_en": "Chemical equilibrium and buffers", "subject": "chemistry", "order_in_subject": 12},
    {"slug": "nomenclatura-inorganica", "title_it": "Nomenclatura composti inorganici", "title_en": "Inorganic compound nomenclature", "subject": "chemistry", "order_in_subject": 13},
    {"slug": "chimica-organica", "title_it": "Chimica organica: idrocarburi e gruppi funzionali", "title_en": "Organic chemistry: hydrocarbons and functional groups", "subject": "chemistry", "order_in_subject": 14},
    # Logic topics
    {"slug": "logica-proposizionale", "title_it": "Logica proposizionale", "title_en": "Propositional logic", "subject": "logic", "order_in_subject": 1},
    {"slug": "sillogismi", "title_it": "Sillogismi e deduzioni", "title_en": "Syllogisms and deductions", "subject": "logic", "order_in_subject": 2},
    {"slug": "ragionamento-condizionale", "title_it": "Ragionamento condizionale", "title_en": "Conditional reasoning", "subject": "logic", "order_in_subject": 3},
    {"slug": "serie-numeriche", "title_it": "Serie numeriche", "title_en": "Numerical sequences", "subject": "logic", "order_in_subject": 4},
    {"slug": "brani-logici", "title_it": "Comprensione di brani logici", "title_en": "Logical reading comprehension", "subject": "logic", "order_in_subject": 5},
    {"slug": "problem-solving", "title_it": "Problem solving", "title_en": "Problem solving", "subject": "logic", "order_in_subject": 6},
    {"slug": "insiemi-relazioni", "title_it": "Insiemi e relazioni", "title_en": "Sets and relations", "subject": "logic", "order_in_subject": 7},
    {"slug": "logica-argomentativa", "title_it": "Logica argomentativa", "title_en": "Argumentative logic", "subject": "logic", "order_in_subject": 8},
    # Physics / Math topics (new subject: "physics")
    {"slug": "grandezze-fisiche", "title_it": "Grandezze fisiche e misura", "title_en": "Physical quantities and measurement", "subject": "physics", "order_in_subject": 1},
    {"slug": "cinematica", "title_it": "Cinematica", "title_en": "Kinematics", "subject": "physics", "order_in_subject": 2},
    {"slug": "dinamica", "title_it": "Dinamica e le leggi di Newton", "title_en": "Dynamics and Newton's laws", "subject": "physics", "order_in_subject": 3},
    {"slug": "meccanica-fluidi", "title_it": "Meccanica dei fluidi", "title_en": "Fluid mechanics", "subject": "physics", "order_in_subject": 4},
    {"slug": "termodinamica", "title_it": "Termodinamica", "title_en": "Thermodynamics", "subject": "physics", "order_in_subject": 5},
    {"slug": "elettromagnetismo", "title_it": "Elettromagnetismo", "title_en": "Electromagnetism", "subject": "physics", "order_in_subject": 6},
    {"slug": "algebra-aritmetica", "title_it": "Algebra e aritmetica", "title_en": "Algebra and arithmetic", "subject": "physics", "order_in_subject": 7},
    {"slug": "funzioni", "title_it": "Funzioni matematiche", "title_en": "Mathematical functions", "subject": "physics", "order_in_subject": 8},
    {"slug": "geometria", "title_it": "Geometria e trigonometria", "title_en": "Geometry and trigonometry", "subject": "physics", "order_in_subject": 9},
    {"slug": "probabilita-statistica", "title_it": "Probabilità e statistica", "title_en": "Probability and statistics", "subject": "physics", "order_in_subject": 10},
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
