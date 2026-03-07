#!/usr/bin/env python3
"""Seed baseline logic topics/questions for healthcare entry-test prep."""

import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "osteoprep.db")

QUIZ_QUESTIONS = [
    ("logica-proposizionale", "Se P e Q sono vere, quale espressione e sicuramente vera?", ["P OR NOT P", "P AND Q", "NOT P AND NOT Q", "P XOR Q"], 1),
    ("logica-proposizionale", "La negazione di 'Tutti gli studenti sono preparati' e:", ["Nessuno studente e preparato", "Alcuni studenti sono preparati", "Esiste almeno uno studente non preparato", "Tutti gli studenti non sono preparati"], 2),
    ("logica-proposizionale", "La proposizione 'Se piove, la strada e bagnata' e falsa solo quando:", ["Piove e la strada e bagnata", "Piove e la strada non e bagnata", "Non piove e la strada e bagnata", "Non piove e la strada non e bagnata"], 1),

    ("sillogismi", "Tutti i medici sono laureati. Alcuni laureati sono ricercatori. Quale conclusione e certa?", ["Tutti i ricercatori sono medici", "Alcuni medici sono ricercatori", "Nessun medico e ricercatore", "Nessuna delle precedenti"], 3),
    ("sillogismi", "Nessun batterio e eucariote. Alcuni microrganismi sono batteri. Quindi:", ["Alcuni microrganismi non sono eucarioti", "Tutti i microrganismi non sono eucarioti", "Tutti i batteri sono eucarioti", "Nessun microrganismo e batterio"], 0),
    ("sillogismi", "Tutti i mammiferi hanno cuore. Il delfino e un mammifero. Quindi:", ["Il delfino non ha cuore", "Il delfino ha cuore", "Solo alcuni delfini hanno cuore", "Non si puo concludere"], 1),

    ("ragionamento-condizionale", "Se studio, supero il test. Ho superato il test. Quale inferenza e logicamente valida?", ["Ho sicuramente studiato", "Potrei aver studiato ma non e certo", "Non ho studiato", "Studio solo se non supero il test"], 1),
    ("ragionamento-condizionale", "Se un farmaco e efficace allora riduce i sintomi. Il farmaco non riduce i sintomi. Quindi:", ["Il farmaco e efficace", "Il farmaco non e efficace", "Il farmaco e tossico", "Non si puo dire nulla"], 1),
    ("ragionamento-condizionale", "Se A allora B. Se B allora C. Quale affermazione e corretta?", ["Se A allora C", "Se C allora A", "Se non A allora non C", "A e C sono equivalenti"], 0),

    ("serie-numeriche", "Completa la serie: 2, 6, 12, 20, ...", ["28", "30", "32", "36"], 1),
    ("serie-numeriche", "Completa la serie: 81, 27, 9, 3, ...", ["1", "0", "-1", "1/3"], 0),
    ("serie-numeriche", "Completa la serie: 5, 10, 8, 16, 14, 28, ...", ["24", "26", "30", "32"], 1),

    ("brani-logici", "In un brano si afferma: 'La prevenzione riduce i costi sanitari nel lungo periodo'. Qual e l'implicazione piu diretta?", ["La prevenzione elimina tutte le malattie", "Investire in prevenzione puo essere economicamente vantaggioso", "I costi sanitari non dipendono dalla prevenzione", "La prevenzione e utile solo nel breve periodo"], 1),
    ("brani-logici", "Se un testo distingue tra correlazione e causalita, quale errore invita a evitare?", ["Confondere associazione con causa", "Usare dati numerici", "Confrontare due gruppi", "Formulare ipotesi"], 0),
    ("brani-logici", "Nel ragionamento 'dopo il vaccino e migliorato, quindi e stato il vaccino', il punto debole principale e:", ["Mancanza di sequenza temporale", "Assenza di una possibile causa alternativa", "Uso di termini tecnici", "Presenza di dati statistici"], 1),

    ("problem-solving", "Un test ha 60 domande. Risposta corretta +1, errata -0.25, omessa 0. Se fai 40 corrette e 8 errate, punteggio?", ["36", "38", "42", "44"], 1),
    ("problem-solving", "Una soluzione e diluita al 20%. Quanti mL di soluto ci sono in 250 mL di soluzione?", ["20", "40", "50", "80"], 2),
    ("problem-solving", "Per completare 120 esercizi in 6 giorni con ritmo costante, quanti esercizi al giorno?", ["12", "18", "20", "24"], 2),

    ("insiemi-relazioni", "In una classe: 18 studiano biologia, 12 chimica, 7 entrambe. Quanti studiano almeno una delle due?", ["23", "25", "30", "37"], 0),
    ("insiemi-relazioni", "Se A e sottoinsieme di B, quale affermazione e sempre vera?", ["B e sottoinsieme di A", "A unione B = A", "A intersezione B = A", "A e B sono disgiunti"], 2),
    ("insiemi-relazioni", "La relazione 'essere fratello di' e:", ["Riflessiva", "Simmetrica", "Antisimmetrica", "Transitiva"], 1),

    ("logica-argomentativa", "Quale e un tipico argomento ad hominem?", ["Criticare la persona invece dell'argomento", "Usare un controesempio", "Definire i termini", "Concludere da dati sperimentali"], 0),
    ("logica-argomentativa", "L'errore 'post hoc ergo propter hoc' consiste nel:", ["Negare l'antecedente", "Assumere che una successione temporale implichi causalita", "Usare una tautologia", "Confondere parte e tutto"], 1),
    ("logica-argomentativa", "Quale opzione rafforza di piu un'argomentazione scientifica?", ["Anecdote personali", "Dati replicabili e controllati", "Autorita non verificabili", "Generalizzazioni assolute"], 1),
]

EXAM_QUESTIONS = [
    ("logic", "logica-proposizionale", None, "La negazione di 'Almeno un candidato ha risposto correttamente' e:", ["Nessun candidato ha risposto correttamente", "Tutti i candidati hanno risposto correttamente", "Almeno un candidato non ha risposto correttamente", "Solo un candidato ha risposto correttamente"], 0),
    ("logic", "sillogismi", None, "Tutti i farmaci efficaci superano i trial clinici. Alcuni composti non superano i trial. Quale conclusione e valida?", ["Alcuni composti non sono farmaci efficaci", "Tutti i composti sono farmaci efficaci", "Nessun composto e efficace", "Tutti i trial sono inefficaci"], 0),
    ("logic", "ragionamento-condizionale", None, "Se una sostanza e tossica allora e pericolosa. La sostanza non e pericolosa. Quindi:", ["La sostanza e tossica", "La sostanza non e tossica", "La sostanza e sicuramente innocua", "Non si puo concludere"], 1),
    ("logic", "serie-numeriche", None, "Completa: 3, 6, 11, 18, 27, ...", ["34", "36", "38", "40"], 2),
    ("logic", "problem-solving", None, "Un candidato risponde a 50 domande: 35 corrette, 10 errate, 5 omesse. Punteggio con +1/-0.25/0?", ["30.5", "32.5", "35", "37.5"], 1),
    ("logic", "insiemi-relazioni", None, "In un gruppo: 40 studiano biologia, 25 chimica, 15 entrambe. Quanti studiano solo biologia?", ["10", "15", "20", "25"], 3),
    ("logic", "logica-argomentativa", None, "Quale opzione identifica una falsa dicotomia?", ["Presentare solo due alternative escludendo altre possibilita", "Confrontare due ipotesi", "Definire un termine ambiguo", "Usare un esempio concreto"], 0),
    ("logic", "brani-logici", None, "Un testo dice: 'L'aumento delle diagnosi dipende anche da migliori strumenti'. Quale inferenza e piu prudente?", ["La malattia e sicuramente piu diffusa", "Parte dell'aumento puo dipendere da migliore rilevazione", "Gli strumenti causano la malattia", "Le diagnosi precedenti erano tutte errate"], 1),
]


def seed_topics(conn: sqlite3.Connection) -> tuple[int, int]:
    topics = [
        ("logica-proposizionale", "Logica proposizionale", "Propositional logic", "logic", 1),
        ("sillogismi", "Sillogismi e deduzioni", "Syllogisms and deductions", "logic", 2),
        ("ragionamento-condizionale", "Ragionamento condizionale", "Conditional reasoning", "logic", 3),
        ("serie-numeriche", "Serie numeriche", "Numerical sequences", "logic", 4),
        ("brani-logici", "Comprensione di brani logici", "Logical reading comprehension", "logic", 5),
        ("problem-solving", "Problem solving", "Problem solving", "logic", 6),
        ("insiemi-relazioni", "Insiemi e relazioni", "Sets and relations", "logic", 7),
        ("logica-argomentativa", "Logica argomentativa", "Argumentative logic", "logic", 8),
    ]
    inserted = 0
    skipped = 0
    for slug, title_it, title_en, subject, order_in_subject in topics:
        cur = conn.execute(
            """INSERT OR IGNORE INTO topics
               (slug, title_it, title_en, subject, order_in_subject, content_it, content_en, generated_at)
               VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL)""",
            (slug, title_it, title_en, subject, order_in_subject),
        )
        if cur.rowcount > 0:
            inserted += 1
        else:
            skipped += 1
    return inserted, skipped


def seed_quiz(conn: sqlite3.Connection) -> tuple[int, int]:
    inserted = 0
    skipped = 0
    for topic_slug, question_it, choices, correct_index in QUIZ_QUESTIONS:
        existing = conn.execute(
            "SELECT id FROM quiz_questions WHERE question_it=?", (question_it,)
        ).fetchone()
        if existing:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO quiz_questions (topic_slug, question_it, choices_json, correct_index) VALUES (?, ?, ?, ?)",
            (topic_slug, question_it, json.dumps(choices, ensure_ascii=False), correct_index),
        )
        inserted += 1
    return inserted, skipped


def seed_exam(conn: sqlite3.Connection) -> tuple[int, int]:
    inserted = 0
    skipped = 0
    for subject, topic_slug, source_year, question_it, choices, correct_index in EXAM_QUESTIONS:
        existing = conn.execute(
            "SELECT id FROM exam_questions WHERE question_it=?", (question_it,)
        ).fetchone()
        if existing:
            skipped += 1
            continue
        conn.execute(
            """INSERT INTO exam_questions
               (subject, topic_slug, source_year, question_it, choices_json, correct_index)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (subject, topic_slug, source_year, question_it, json.dumps(choices, ensure_ascii=False), correct_index),
        )
        inserted += 1
    return inserted, skipped


def main() -> None:
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        t_i, t_s = seed_topics(conn)
        q_i, q_s = seed_quiz(conn)
        e_i, e_s = seed_exam(conn)
        conn.commit()
    finally:
        conn.close()

    print(f"Topics: inserted={t_i}, skipped={t_s}")
    print(f"Quiz questions: inserted={q_i}, skipped={q_s}")
    print(f"Exam questions: inserted={e_i}, skipped={e_s}")


if __name__ == "__main__":
    main()
