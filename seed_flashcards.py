"""
Seed flashcards for Biology and Chemistry nomenclature topics.
Uses synchronous sqlite3 (same pattern as seed_topics.py).
Run: python seed_flashcards.py
"""
import json
import os
import sqlite3
from datetime import datetime, timezone

from fsrs import Card

FLASHCARDS = [
    # Biology: membrana-cellulare
    {
        "topic_slug": "membrana-cellulare",
        "front_it": "La membrana cellulare",
        "back_it": "Struttura a doppio strato fosfolipidico con proteine integrali e periferiche. Regola il passaggio di sostanze tra interno ed esterno della cellula (permeabilita' selettiva).",
        "front_en": "The cell membrane",
        "back_en": "Phospholipid bilayer structure with integral and peripheral proteins. Regulates passage of substances between inside and outside the cell (selective permeability).",
    },
    {
        "topic_slug": "membrana-cellulare",
        "front_it": "Trasporto attivo",
        "back_it": "Movimento di molecole contro gradiente di concentrazione che richiede energia (ATP). Esempio: pompa sodio-potassio (Na+/K+ ATPasi).",
        "front_en": "Active transport",
        "back_en": "Movement of molecules against concentration gradient requiring energy (ATP). Example: sodium-potassium pump (Na+/K+ ATPase).",
    },
    # Biology: nucleo-cellulare
    {
        "topic_slug": "nucleo-cellulare",
        "front_it": "Il nucleo cellulare",
        "back_it": "Organello delimitato dalla doppia membrana nucleare. Sede del DNA genomico e del controllo dell'espressione genica. Contiene il nucleolo per la sintesi dell'rRNA.",
        "front_en": "The cell nucleus",
        "back_en": "Organelle bounded by the double nuclear membrane. Contains genomic DNA and controls gene expression. Contains nucleolus for rRNA synthesis.",
    },
    {
        "topic_slug": "nucleo-cellulare",
        "front_it": "La cromatina",
        "back_it": "Complesso di DNA e proteine istoniche nel nucleo. Eterocromatina = condensata, trascrizionalmente inattiva. Eucromatina = dispersa, trascrizionalmente attiva.",
        "front_en": "Chromatin",
        "back_en": "Complex of DNA and histone proteins in the nucleus. Heterochromatin = condensed, transcriptionally inactive. Euchromatin = dispersed, transcriptionally active.",
    },
    # Biology: respirazione-cellulare
    {
        "topic_slug": "respirazione-cellulare",
        "front_it": "I mitocondri",
        "back_it": "Organelli a doppia membrana, detti 'centrale energetica della cellula'. Producono ATP tramite fosforilazione ossidativa. Hanno DNA proprio (mtDNA) e origine endosimbiontica.",
        "front_en": "Mitochondria",
        "back_en": "Double-membrane organelles, called the 'powerhouse of the cell'. Produce ATP via oxidative phosphorylation. Have their own DNA (mtDNA) and endosymbiotic origin.",
    },
    {
        "topic_slug": "respirazione-cellulare",
        "front_it": "L'ATP (Adenosintrifosfato)",
        "back_it": "Principale vettore di energia chimica nella cellula. Idrolisi di ATP -> ADP + Pi libera circa 30.5 kJ/mol. Prodotto principalmente nella catena di trasporto degli elettroni mitocondriale.",
        "front_en": "ATP (Adenosine triphosphate)",
        "back_en": "Main carrier of chemical energy in the cell. Hydrolysis of ATP -> ADP + Pi releases ~30.5 kJ/mol. Produced mainly in the mitochondrial electron transport chain.",
    },
    # Biology: dna-rna-proteine
    {
        "topic_slug": "dna-rna-proteine",
        "front_it": "Il DNA (Acido desossiribonucleico)",
        "back_it": "Polimero di nucleotidi con basi azotate A, T, G, C. Struttura a doppia elica antiparallela (Watson-Crick). Porta l'informazione genetica trasmessa per replicazione semiconservativa.",
        "front_en": "DNA (Deoxyribonucleic acid)",
        "back_en": "Polymer of nucleotides with nitrogenous bases A, T, G, C. Antiparallel double helix structure (Watson-Crick). Carries genetic information transmitted by semiconservative replication.",
    },
    {
        "topic_slug": "dna-rna-proteine",
        "front_it": "L'RNA messaggero (mRNA)",
        "back_it": "RNA sintetizzato per trascrizione dal DNA template. Porta il codice genetico dai geni ai ribosomi per la traduzione in proteina. Processato nel nucleo: cappuccio 5', coda poli-A, splicing degli introni.",
        "front_en": "Messenger RNA (mRNA)",
        "back_en": "RNA synthesized by transcription from DNA template. Carries genetic code from genes to ribosomes for translation into protein. Processed in nucleus: 5' cap, poly-A tail, intron splicing.",
    },
    # Chemistry: legami-chimici
    {
        "topic_slug": "legami-chimici",
        "front_it": "Legame covalente",
        "back_it": "Legame formato dalla condivisione di una o piu' coppie di elettroni tra due atomi. Puo' essere singolo (sigma), doppio (sigma + pi) o triplo. Caratterizza le molecole organiche.",
        "front_en": "Covalent bond",
        "back_en": "Bond formed by sharing one or more pairs of electrons between two atoms. Can be single (sigma), double (sigma + pi), or triple. Characterizes organic molecules.",
    },
    {
        "topic_slug": "legami-chimici",
        "front_it": "Legame ionico",
        "back_it": "Legame formato dal trasferimento completo di uno o piu' elettroni da un atomo all'altro. Genera ioni positivi (cationi) e negativi (anioni). Tipico tra metalli e non metalli (es. NaCl).",
        "front_en": "Ionic bond",
        "back_en": "Bond formed by complete transfer of one or more electrons from one atom to another. Generates positive (cations) and negative (anions) ions. Typical between metals and non-metals (e.g., NaCl).",
    },
    # Chemistry: acidi-basi-ph
    {
        "topic_slug": "acidi-basi-ph",
        "front_it": "pH",
        "back_it": "Misura dell'acidita' di una soluzione. pH = -log[H+]. pH < 7 = acido; pH 7 = neutro; pH > 7 = basico. Scala da 0 a 14. Il sangue ha pH fisiologico 7.35-7.45.",
        "front_en": "pH",
        "back_en": "Measure of acidity of a solution. pH = -log[H+]. pH < 7 = acid; pH 7 = neutral; pH > 7 = basic. Scale from 0 to 14. Blood has physiological pH 7.35-7.45.",
    },
    {
        "topic_slug": "acidi-basi-ph",
        "front_it": "Acido di Bronsted-Lowry",
        "back_it": "Sostanza che dona protoni (H+) in soluzione acquosa. La base coniugata e' la specie che rimane dopo la donazione del protone. Acidi forti si dissociano completamente (HCl, H2SO4).",
        "front_en": "Bronsted-Lowry acid",
        "back_en": "Substance that donates protons (H+) in aqueous solution. The conjugate base is the species remaining after proton donation. Strong acids dissociate completely (HCl, H2SO4).",
    },
    # Chemistry: atomo-struttura
    {
        "topic_slug": "atomo-struttura",
        "front_it": "Numero atomico (Z)",
        "back_it": "Numero di protoni nel nucleo di un atomo. Identifica univocamente l'elemento chimico. In un atomo neutro, Z = numero di elettroni. Es: C ha Z=6 (6 protoni, 6 elettroni).",
        "front_en": "Atomic number (Z)",
        "back_en": "Number of protons in the nucleus of an atom. Uniquely identifies the chemical element. In a neutral atom, Z = number of electrons. E.g., C has Z=6 (6 protons, 6 electrons).",
    },
    # Chemistry: reazioni-chimiche
    {
        "topic_slug": "reazioni-chimiche",
        "front_it": "Isomeri",
        "back_it": "Molecole con la stessa formula molecolare ma diversa struttura (o disposizione spaziale). Isomeri di struttura: catena diversa. Stereoisomeri: stessa connettivita', diversa disposizione 3D (enantiomeri, diastereomeri).",
        "front_en": "Isomers",
        "back_en": "Molecules with the same molecular formula but different structure (or spatial arrangement). Structural isomers: different connectivity. Stereoisomers: same connectivity, different 3D arrangement (enantiomers, diastereoisomers).",
    },
]


def seed():
    db_path = "data/osteoprep.db"
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}. Run alembic upgrade head first.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    new_card_json = Card().to_json()

    inserted_cards = 0
    skipped_cards = 0
    inserted_srs = 0
    topics_affected = set()

    for fc in FLASHCARDS:
        # Check if flashcard already exists by front_it + topic_slug
        existing = cur.execute(
            "SELECT id FROM flashcards WHERE front_it = ? AND topic_slug = ?",
            (fc["front_it"], fc["topic_slug"]),
        ).fetchone()

        if existing:
            skipped_cards += 1
            continue

        # Insert flashcard
        cur.execute(
            """INSERT INTO flashcards (topic_slug, front_it, back_it, front_en, back_en)
               VALUES (?, ?, ?, ?, ?)""",
            (fc["topic_slug"], fc["front_it"], fc["back_it"],
             fc.get("front_en"), fc.get("back_en")),
        )
        flashcard_id = cur.lastrowid
        inserted_cards += 1
        topics_affected.add(fc["topic_slug"])

        # Insert SRS state with card due immediately
        cur.execute(
            """INSERT INTO srs_states (flashcard_id, card_json, due_at, updated_at)
               VALUES (?, ?, ?, ?)""",
            (flashcard_id, new_card_json, now_utc, now_utc),
        )
        inserted_srs += 1

    conn.commit()
    conn.close()
    print(f"Seeded {inserted_cards} flashcards for {len(topics_affected)} topics "
          f"({skipped_cards} skipped — already existed)")
    print(f"SRS states created: {inserted_srs}")


if __name__ == "__main__":
    seed()
