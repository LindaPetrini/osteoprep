#!/usr/bin/env python3
"""
Seed Italian MCQ questions for topic quizzes.
CSV format for future bulk import:
  topic_slug,question_it,choice_a,choice_b,choice_c,choice_d,correct_index
  correct_index: 0=A, 1=B, 2=C, 3=D
"""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "osteoprep.db")

QUESTIONS = [
    # topic_slug, question_it, [choice_a, choice_b, choice_c, choice_d], correct_index
    # --- BIOLOGY: membrana-cellulare ---
    ("membrana-cellulare",
     "Qual è il principale componente strutturale della membrana plasmatica?",
     ["Glicogeno", "Fosfolipidi", "Proteine integrali", "Colesterolo"], 1),

    ("membrana-cellulare",
     "Quale funzione svolge il colesterolo nella membrana plasmatica a temperature fisiologiche?",
     ["Aumenta la permeabilità ai glucosio", "Stabilizza la fluidità della membrana", "Fornisce energia alla cellula", "Trasporta ioni sodio"], 1),

    ("membrana-cellulare",
     "Cosa si intende per 'permeabilità selettiva' della membrana plasmatica?",
     ["La membrana lascia passare solo l'acqua", "La membrana è impermeabile a tutte le molecole", "La membrana regola il passaggio di molecole in base a dimensione e polarità", "La membrana permette il passaggio solo di ioni"], 2),

    # --- BIOLOGY: nucleo-cellulare ---
    ("nucleo-cellulare",
     "Qual è la funzione principale dell'involucro nucleare?",
     ["Sintetizzare proteine", "Separare il DNA dal citoplasma e regolare gli scambi", "Produrre ATP", "Immagazzinare calcio"], 1),

    ("nucleo-cellulare",
     "Dove avviene la sintesi dell'RNA ribosomale (rRNA)?",
     ["Nel citoplasma", "Nel reticolo endoplasmatico", "Nel nucleolo", "Nei mitocondri"], 2),

    # --- BIOLOGY: mitocondri ---
    ("mitocondri",
     "Qual è il prodotto finale principale della catena di trasporto degli elettroni mitocondriale?",
     ["NADH", "CO2", "ATP", "Glucosio"], 2),

    ("mitocondri",
     "La membrana mitocondriale interna è caratterizzata da numerose ripiegature chiamate:",
     ["Cisterne", "Cristae", "Villi", "Lamelle"], 1),

    ("mitocondri",
     "Quale molecola entra nel ciclo di Krebs come substrato iniziale?",
     ["Glucosio", "Piruvato", "Acetil-CoA", "FADH2"], 2),

    # --- BIOLOGY: dna-rna-proteine ---
    ("dna-rna-proteine",
     "Quale base azotata è presente nell'RNA ma non nel DNA?",
     ["Adenina", "Uracile", "Guanina", "Citosina"], 1),

    ("dna-rna-proteine",
     "La trascrizione del DNA produce:",
     ["Una molecola di DNA figlia", "Una molecola di RNA messaggero", "Una proteina direttamente", "Un ribosoma"], 1),

    ("dna-rna-proteine",
     "Il codone di stop UAA indica al ribosoma di:",
     ["Iniziare la traduzione", "Aggiungere un aminoacido specifico", "Terminare la sintesi proteica", "Spostare l'mRNA"], 2),

    # --- CHEMISTRY: legami-chimici ---
    ("legami-chimici",
     "Quale tipo di legame si forma per condivisione di una coppia di elettroni tra due atomi?",
     ["Legame ionico", "Legame covalente", "Legame idrogeno", "Legame di Van der Waals"], 1),

    ("legami-chimici",
     "Il legame ionico si forma tipicamente tra:",
     ["Due non metalli", "Un metallo e un non metallo", "Due atomi dello stesso elemento", "Due molecole d'acqua"], 1),

    # --- CHEMISTRY: acidi-basi-ph ---
    ("acidi-basi-ph",
     "Un acido forte in soluzione acquosa ha un pH:",
     ["Vicino a 7", "Maggiore di 7", "Minore di 7", "Uguale a 14"], 2),

    ("acidi-basi-ph",
     "La costante di dissociazione acida Ka per un acido forte è:",
     ["Molto piccola (Ka << 1)", "Circa uguale a 1", "Molto grande (Ka >> 1)", "Uguale a zero"], 2),

    # --- CHEMISTRY: reazioni-chimiche ---
    ("reazioni-chimiche",
     "In una reazione esotermica, l'energia del sistema:",
     ["Rimane costante", "Aumenta", "Diminuisce, liberando calore nell'ambiente", "Viene assorbita dall'ambiente"], 2),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    inserted = 0
    skipped = 0
    for topic_slug, question_it, choices, correct_index in QUESTIONS:
        existing = conn.execute(
            "SELECT id FROM quiz_questions WHERE topic_slug=? AND question_it=?",
            (topic_slug, question_it)
        ).fetchone()
        if existing:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO quiz_questions (topic_slug, question_it, choices_json, correct_index) VALUES (?, ?, ?, ?)",
            (topic_slug, question_it, json.dumps(choices, ensure_ascii=False), correct_index)
        )
        inserted += 1
    conn.commit()
    conn.close()
    print(f"Seeded {inserted} questions, skipped {skipped} existing")


if __name__ == "__main__":
    seed()
