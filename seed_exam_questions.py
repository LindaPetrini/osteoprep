#!/usr/bin/env python3
"""
Seed Italian MCQ exam questions (professioni sanitarie / TOLC-B/TOLC-F style).

CSV format for future bulk import (add rows to QUESTIONS list):
  (subject, topic_slug_or_None, source_year_or_None, question_it, [choice_a,...,choice_d], correct_index)
  subject: "biology" | "chemistry" | "physics" | "logic"
  correct_index: 0=A, 1=B, 2=C, 3=D
"""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "osteoprep.db")

# (subject, topic_slug, source_year, question_it, [choices], correct_index)
QUESTIONS = [
    # ---- BIOLOGY ----
    ("biology", "membrana-cellulare", None,
     "Qual è il modello che descrive meglio la struttura della membrana plasmatica?",
     ["Modello a strati rigidi", "Modello a mosaico fluido", "Modello a sandwich proteico", "Modello a doppia elica"], 1),

    ("biology", "nucleo-cellulare", None,
     "Il DNA negli eucarioti è localizzato principalmente:",
     ["Nel citoplasma libero", "Nei ribosomi", "Nel nucleo cellulare", "Nei mitocondri esclusivamente"], 2),

    ("biology", "mitocondri", None,
     "Quante molecole di ATP vengono prodotte per ogni molecola di glucosio nella respirazione cellulare aerobica (stima teorica)?",
     ["2 ATP", "8 ATP", "36-38 ATP", "100 ATP"], 2),

    ("biology", "dna-rna-proteine", None,
     "La traduzione è il processo attraverso cui:",
     ["Il DNA viene replicato", "L'mRNA viene sintetizzato dal DNA", "La sequenza dell'mRNA viene convertita in una proteina", "L'RNA viene trasportato nel nucleo"], 2),

    ("biology", "dna-rna-proteine", None,
     "Quale dei seguenti è un nucleotide del DNA?",
     ["Uridina monofosfato (UMP)", "Adenosina trifosfato con uracile", "Deossiadenosina monofosfato (dAMP)", "Ribosio-fosfato"], 2),

    ("biology", "membrana-cellulare", None,
     "L'osmosi è definita come il movimento spontaneo:",
     ["Di soluti da zone a bassa concentrazione a zone ad alta concentrazione", "Di acqua attraverso una membrana semipermeabile verso la soluzione più concentrata", "Di ioni attraverso proteine canale con consumo di ATP", "Di molecole lipidiche dalla membrana"], 1),

    ("biology", None, None,
     "Quale organello cellulare è responsabile della sintesi proteica?",
     ["Apparato di Golgi", "Reticolo endoplasmatico liscio", "Ribosomi", "Lisosomi"], 2),

    ("biology", None, None,
     "Il processo di mitosi produce:",
     ["Quattro cellule aploidi", "Due cellule diploidi geneticamente identiche", "Cellule con la metà del corredo cromosomico", "Una sola cellula con DNA duplicato"], 1),

    ("biology", None, None,
     "Quale delle seguenti molecole è coinvolta nel trasporto di ossigeno nel sangue?",
     ["Insulina", "Emoglobina", "Glucagone", "Fibrinogeno"], 1),

    ("biology", None, None,
     "La replicazione del DNA è definita 'semiconservativa' perché:",
     ["Viene replicato solo metà del genoma", "Ogni doppia elica figlia contiene un filamento parentale e uno nuovo", "Solo uno dei due filamenti viene conservato nella cellula", "La replicazione avviene solo nei mitocondri"], 1),

    # ---- CHEMISTRY ----
    ("chemistry", "legami-chimici", None,
     "Quanti protoni contiene un atomo di carbonio (C)?",
     ["2", "4", "6", "12"], 2),

    ("chemistry", "legami-chimici", None,
     "Il numero di massa di un atomo rappresenta:",
     ["Solo il numero di protoni", "Solo il numero di neutroni", "La somma di protoni e neutroni nel nucleo", "La somma di protoni ed elettroni"], 2),

    ("chemistry", "acidi-basi-ph", None,
     "Qual è il pH del sangue umano in condizioni fisiologiche normali?",
     ["6.0 – 6.5", "7.35 – 7.45", "7.8 – 8.0", "5.5 – 6.0"], 1),

    ("chemistry", "acidi-basi-ph", None,
     "Una soluzione con pH = 3 rispetto a una con pH = 6 è:",
     ["10 volte meno acida", "3 volte più acida", "1000 volte più acida", "Ugualmente acida"], 2),

    ("chemistry", "reazioni-chimiche", None,
     "Nella reazione: 2H₂ + O₂ → 2H₂O, quale affermazione è corretta?",
     ["L'idrogeno è il riducente e si ossida", "L'ossigeno si riduce e l'idrogeno si ossida", "L'acqua è il riducente", "Nessuna ossidazione avviene"], 1),

    ("chemistry", "legami-chimici", None,
     "Quale proprietà degli atomi determina la loro tendenza ad attrarre elettroni in un legame?",
     ["Massa atomica", "Numero di massa", "Elettronegatività", "Raggio atomico"], 2),

    ("chemistry", None, None,
     "La formula molecolare del glucosio è:",
     ["C₆H₁₂O₆", "C₁₂H₂₂O₁₁", "CH₃COOH", "C₆H₆"], 0),

    ("chemistry", None, None,
     "Un legame peptidico si forma tra:",
     ["Due carboidrati", "Il gruppo amminico di un aminoacido e il gruppo carbossilico di un altro", "Due basi azotate del DNA", "Un lipide e una proteina"], 1),

    ("chemistry", None, None,
     "Qual è il numero di Avogadro?",
     ["3.14 × 10²³", "6.022 × 10²³", "1.38 × 10⁻²³", "9.109 × 10⁻²⁸"], 1),

    ("chemistry", "reazioni-chimiche", None,
     "In una reazione chimica in equilibrio, aumentare la concentrazione dei reagenti secondo il Principio di Le Chatelier:",
     ["Non modifica l'equilibrio", "Sposta l'equilibrio verso i prodotti", "Sposta l'equilibrio verso i reagenti", "Ferma la reazione"], 1),

    # ---- Extra biology for variety ----
    ("biology", None, None,
     "Quale tipo di tessuto forma il rivestimento esterno del corpo umano?",
     ["Tessuto connettivo", "Tessuto muscolare", "Tessuto epiteliale", "Tessuto nervoso"], 2),

    ("biology", None, None,
     "Il sistema nervoso autonomo comprende:",
     ["Solo il sistema nervoso simpatico", "Il sistema nervoso somatico e periferico", "Il sistema nervoso simpatico e parasimpatico", "Solo le vie sensitive del midollo spinale"], 2),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    inserted = 0
    skipped = 0
    for subject, topic_slug, source_year, question_it, choices, correct_index in QUESTIONS:
        existing = conn.execute(
            "SELECT id FROM exam_questions WHERE question_it=?", (question_it,)
        ).fetchone()
        if existing:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO exam_questions (subject, topic_slug, source_year, question_it, choices_json, correct_index) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (subject, topic_slug, source_year, question_it,
             json.dumps(choices, ensure_ascii=False), correct_index),
        )
        inserted += 1
    conn.commit()
    conn.close()
    print(f"Seeded {inserted} exam questions, skipped {skipped} existing")


if __name__ == "__main__":
    seed()
