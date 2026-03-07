#!/usr/bin/env python3
"""Raise logic coverage to parity and map legacy exam questions to concrete topics."""

import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "osteoprep.db")

LOGIC_QUIZ_V2 = [
    ("logica-proposizionale", "Quale delle seguenti e una tautologia?", ["P AND NOT P", "P OR NOT P", "P -> Q", "P XOR Q"], 1),
    ("logica-proposizionale", "Secondo De Morgan, la negazione di (P AND Q) e:", ["NOT P AND NOT Q", "NOT P OR NOT Q", "P OR Q", "NOT(P -> Q)"], 1),
    ("logica-proposizionale", "Quando due proposizioni sono logicamente equivalenti?", ["Quando hanno sempre la stessa verita", "Quando hanno simboli uguali", "Quando sono entrambe semplici", "Quando sono entrambe false"], 0),
    ("logica-proposizionale", "La formula P AND NOT P e:", ["Una tautologia", "Una contingenza", "Una contraddizione", "Un'implicazione valida"], 2),
    ("logica-proposizionale", "L'implicazione P -> Q e falsa solo se:", ["P vera e Q falsa", "P falsa e Q vera", "P e Q vere", "P e Q false"], 0),

    ("sillogismi", "Tutti gli infermieri sono operatori sanitari. Laura e infermiera. Quindi:", ["Laura non e operatrice sanitaria", "Laura e operatrice sanitaria", "Laura e medico", "Non si puo concludere"], 1),
    ("sillogismi", "Nessun virus e un batterio. Alcuni patogeni sono virus. Ne segue che:", ["Alcuni patogeni non sono batteri", "Tutti i patogeni sono batteri", "Nessun patogeno e virus", "Alcuni batteri sono virus"], 0),
    ("sillogismi", "Tutti i candidati preparati superano il test. Marco non ha superato il test. Conclusione valida:", ["Marco non era preparato", "Marco era preparato", "Marco non ha studiato medicina", "Non esiste conclusione certa"], 3),
    ("sillogismi", "Alcuni studenti sono lavoratori. Tutti i lavoratori sono maggiorenni. Quindi:", ["Alcuni studenti sono maggiorenni", "Tutti gli studenti sono maggiorenni", "Nessuno studente e maggiorenne", "Solo i lavoratori sono studenti"], 0),
    ("sillogismi", "Se tutte le cellule eucariotiche hanno nucleo e i neuroni sono cellule eucariotiche, allora:", ["I neuroni non hanno nucleo", "Alcuni neuroni hanno nucleo", "I neuroni hanno nucleo", "Solo i neuroni hanno nucleo"], 2),

    ("ragionamento-condizionale", "Se il campione e contaminato, il test e invalido. Il test e invalido. Cosa segue?", ["Campione sicuramente contaminato", "Campione forse contaminato, ma non e certo", "Campione certamente pulito", "Nessuna opzione"], 1),
    ("ragionamento-condizionale", "Se studio con costanza, miglioro il punteggio. Studio con costanza. Quindi:", ["Miglioro il punteggio", "Non miglioro il punteggio", "Resto uguale per forza", "Il punteggio peggiora"], 0),
    ("ragionamento-condizionale", "Se A allora B. Non B. Quale inferenza valida?", ["A", "Non A", "B", "A e B"], 1),
    ("ragionamento-condizionale", "Qual e un esempio di negazione dell'antecedente (fallacia)?", ["Se A allora B; A; quindi B", "Se A allora B; non B; quindi non A", "Se A allora B; non A; quindi non B", "Se A allora B; B; quindi A"], 2),
    ("ragionamento-condizionale", "Se un farmaco e approvato allora ha superato i trial. Il farmaco non e approvato. Possiamo dire che:", ["Non ha superato i trial con certezza", "Ha superato i trial con certezza", "Potrebbe o no aver superato i trial", "E sicuramente inefficace"], 2),

    ("serie-numeriche", "Completa: 1, 4, 9, 16, ...", ["20", "24", "25", "27"], 2),
    ("serie-numeriche", "Completa: 2, 3, 5, 8, 13, ...", ["18", "20", "21", "22"], 2),
    ("serie-numeriche", "Completa: 100, 50, 25, 12.5, ...", ["10", "8", "6.25", "5"], 2),
    ("serie-numeriche", "Completa: 7, 10, 16, 25, 37, ...", ["49", "50", "52", "54"], 2),
    ("serie-numeriche", "Completa: 3, 12, 48, 192, ...", ["384", "576", "768", "960"], 2),

    ("brani-logici", "In un brano: 'I dati osservazionali suggeriscono associazione, non causalita'. Cosa implica?", ["La causalita e dimostrata", "Serve prudenza nell'interpretazione causale", "I dati sono inutili", "Ogni associazione e falsa"], 1),
    ("brani-logici", "Se un testo riporta solo casi favorevoli, quale bias e probabile?", ["Bias di selezione", "Randomizzazione", "Doppio cieco", "Meta-analisi"], 0),
    ("brani-logici", "Nel brano: 'Il campione era ridotto'. Il limite principale e:", ["Bassa potenza statistica", "Eccesso di randomizzazione", "Mancanza di variabili", "Troppi endpoint"], 0),
    ("brani-logici", "Se una conclusione va oltre i dati disponibili, il problema e:", ["Inferenza eccessiva", "Ipotesi nulla", "Controllo positivo", "Rilevanza clinica"], 0),
    ("brani-logici", "Un autore distingue rischio relativo e assoluto. Quale lettura e migliore?", ["Guardare solo il relativo", "Guardare solo l'assoluto", "Valutare entrambi nel contesto", "Ignorare entrambi"], 2),

    ("problem-solving", "Una soluzione al 12% contiene quanti grammi di soluto in 250 g?", ["20 g", "24 g", "30 g", "36 g"], 2),
    ("problem-solving", "In 45 minuti si risolvono 30 quiz. A ritmo costante, in 90 minuti quanti quiz?", ["45", "50", "55", "60"], 3),
    ("problem-solving", "Un punteggio passa da 48 a 60. Incremento percentuale?", ["20%", "25%", "30%", "35%"], 1),
    ("problem-solving", "Se 3 tutor seguono 18 studenti in modo uniforme, quanti studenti per tutor?", ["4", "5", "6", "7"], 2),
    ("problem-solving", "Completare 280 pagine in 14 giorni richiede al giorno:", ["18", "20", "22", "24"], 1),

    ("insiemi-relazioni", "Se |A|=20, |B|=15, |A∩B|=6, allora |A∪B|=", ["29", "35", "41", "21"], 0),
    ("insiemi-relazioni", "Se A⊆B e B⊆C, allora:", ["A⊆C", "C⊆A", "A=C", "A e C disgiunti"], 0),
    ("insiemi-relazioni", "Quale relazione e riflessiva?", ["x<y", "x e fratello di y", "x=x", "x e padre di y"], 2),
    ("insiemi-relazioni", "In un gruppo 30 studiano bio, 18 chimica, 10 entrambe. Solo chimica =", ["6", "8", "10", "12"], 1),
    ("insiemi-relazioni", "Se A e B sono disgiunti, allora A∩B =", ["A", "B", "∅", "A∪B"], 2),

    ("logica-argomentativa", "Generalizzare da un singolo caso e:", ["Argomento valido", "Generalizzazione indebita", "Dilemma corretto", "Inferenza deduttiva"], 1),
    ("logica-argomentativa", "Appellarsi al prestigio senza evidenze e:", ["Appello all'autorita", "Modus ponens", "Riduzione all'assurdo", "Causalita robusta"], 0),
    ("logica-argomentativa", "Attribuire all'avversario una tesi distorta e:", ["Cherry picking", "Straw man", "Slippery slope", "Petizione di principio"], 1),
    ("logica-argomentativa", "Quale elemento rende forte un'argomentazione clinica?", ["Aneddoti isolati", "Convergenza di evidenze indipendenti", "Solo opinioni di forum", "Assenza di controlli"], 1),
    ("logica-argomentativa", "Dire 'funziona perche e naturale' e un esempio di:", ["Argomento valido", "Fallacia naturalistica", "Sillogismo corretto", "Analogia forte"], 1),
]

LOGIC_EXAM_V2 = [
    ("logic", "logica-proposizionale", None, "La negazione di '(P OR Q)' e:", ["NOT P OR NOT Q", "NOT P AND NOT Q", "P AND Q", "P -> NOT Q"], 1),
    ("logic", "logica-proposizionale", None, "Quale coppia e logicamente equivalente?", ["P->Q e NOT P->NOT Q", "P->Q e NOT Q->NOT P", "P OR Q e NOT P OR NOT Q", "P AND Q e P OR Q"], 1),
    ("logic", "logica-proposizionale", None, "La proposizione 'P OR NOT P' in logica classica e:", ["Contraddizione", "Contingenza", "Tautologia", "Paradosso"], 2),
    ("logic", "logica-proposizionale", None, "Quando e vera l'implicazione P->Q?", ["Solo se P e Q vere", "Sempre, tranne quando P vera e Q falsa", "Solo se P falsa", "Solo se Q vera"], 1),
    ("logic", "logica-proposizionale", None, "Se P e falsa, il valore di verita di P->Q e:", ["Sempre falso", "Sempre vero", "Uguale a Q", "Indefinito"], 1),

    ("logic", "sillogismi", None, "Tutti i composti ionici contengono ioni. NaCl e composto ionico. Quindi:", ["NaCl non contiene ioni", "NaCl contiene ioni", "Solo alcuni NaCl contengono ioni", "Non e deducibile"], 1),
    ("logic", "sillogismi", None, "Nessun metallo e gas a temperatura ambiente. Il mercurio e metallo. Conclusione:", ["Mercurio e gas", "Mercurio non e gas", "Mercurio e non metallo", "Non deducibile"], 1),
    ("logic", "sillogismi", None, "Alcuni candidati sono lavoratori. Tutti i lavoratori hanno poco tempo. Quindi:", ["Tutti i candidati hanno poco tempo", "Alcuni candidati hanno poco tempo", "Nessun candidato ha poco tempo", "I lavoratori non sono candidati"], 1),
    ("logic", "sillogismi", None, "Tutti i neuroni sono cellule. Nessuna cellula e procariote. Quindi:", ["Nessun neurone e procariote", "Alcuni neuroni sono procarioti", "Tutti i procarioti sono neuroni", "Nessuna conclusione"], 0),
    ("logic", "sillogismi", None, "Se tutte le vitamine idrosolubili si eliminano con urine e la vitamina C e idrosolubile:", ["Vitamina C non si elimina", "Vitamina C si elimina con urine", "Solo talvolta si elimina", "Nessuna inferenza"], 1),

    ("logic", "ragionamento-condizionale", None, "Se un test e positivo, allora il marker e presente. Il marker non e presente. Quindi:", ["Il test e positivo", "Il test non e positivo", "Il test e falso positivo", "Nessuna inferenza"], 1),
    ("logic", "ragionamento-condizionale", None, "Se A allora B. Se B allora C. Sapendo A, segue:", ["B e C", "Solo C", "Solo B", "Nessuna"], 0),
    ("logic", "ragionamento-condizionale", None, "Quale schema e valido?", ["Affermare il conseguente", "Negare l'antecedente", "Modus tollens", "Circolo vizioso"], 2),
    ("logic", "ragionamento-condizionale", None, "Se il campione e adeguato, il risultato e affidabile. Il risultato non e affidabile. Quindi:", ["Campione adeguato", "Campione non adeguato", "Campione casuale", "Nessuna info"], 1),
    ("logic", "ragionamento-condizionale", None, "Da 'Se studio allora supero' e 'non studio' possiamo concludere che:", ["Non supero sicuramente", "Posso ancora superare per altre ragioni", "Supero sicuramente", "La frase e contraddittoria"], 1),

    ("logic", "serie-numeriche", None, "Completa: 4, 9, 16, 25, ...", ["30", "34", "36", "49"], 2),
    ("logic", "serie-numeriche", None, "Completa: 1, 2, 4, 8, 16, ...", ["24", "30", "32", "36"], 2),
    ("logic", "serie-numeriche", None, "Completa: 15, 12, 9, 6, ...", ["5", "4", "3", "2"], 2),
    ("logic", "serie-numeriche", None, "Completa: 2, 6, 18, 54, ...", ["108", "144", "162", "216"], 2),
    ("logic", "serie-numeriche", None, "Completa: 11, 13, 17, 23, ...", ["27", "29", "31", "33"], 1),

    ("logic", "brani-logici", None, "Un brano conclude causalita da sola correlazione. L'errore piu probabile e:", ["Campione grande", "Confondimento non controllato", "Eccesso di randomizzazione", "Meta-analisi"], 1),
    ("logic", "brani-logici", None, "Se un testo cita solo studi positivi ignorando i negativi, si ha:", ["Publication bias/cherry picking", "Doppio cieco", "Rischio assoluto", "Inferenza deduttiva"], 0),
    ("logic", "brani-logici", None, "L'espressione 'potrebbe suggerire' indica:", ["Certezza causale", "Inferenza prudente", "Errore matematico", "Assenza di dati"], 1),
    ("logic", "brani-logici", None, "Nel valutare un brano scientifico e fondamentale:", ["Guardare solo il titolo", "Distinguere risultati da interpretazioni", "Ignorare i limiti", "Usare solo intuizione"], 1),
    ("logic", "brani-logici", None, "Un'affermazione e piu solida quando:", ["E supportata da dati e metodo replicabile", "E molto popolare", "E espressa con sicurezza", "Ha termini complessi"], 0),

    ("logic", "problem-solving", None, "Un quiz assegna +1/-0.25/0. Con 28 corrette, 8 errate, 4 omesse, punteggio:", ["24", "25", "26", "27"], 2),
    ("logic", "problem-solving", None, "Una classe ha 120 studenti: 30% fuori sede. Quanti fuori sede?", ["24", "30", "36", "40"], 2),
    ("logic", "problem-solving", None, "Un treno percorre 180 km in 2 ore. Velocita media?", ["70 km/h", "80 km/h", "90 km/h", "100 km/h"], 2),
    ("logic", "problem-solving", None, "Ridurre 250 di un 12% da:", ["220", "222", "224", "226"], 0),
    ("logic", "problem-solving", None, "Per fare 90 quesiti in 75 minuti, ritmo medio richiesto e:", ["0.6 quesiti/min", "1.0 quesiti/min", "1.2 quesiti/min", "1.5 quesiti/min"], 2),

    ("logic", "insiemi-relazioni", None, "Se A={1,2,3} e B={3,4}, A∩B =", ["{1,2}", "{3}", "{1,2,3,4}", "∅"], 1),
    ("logic", "insiemi-relazioni", None, "Se 50 studenti fanno bio, 35 chimica, 20 entrambe, almeno una materia:", ["65", "70", "75", "85"], 0),
    ("logic", "insiemi-relazioni", None, "Una relazione simmetrica soddisfa:", ["Se aRb allora bRa", "Se aRb e bRc allora aRc", "Ogni aRa", "Se aRb allora non bRa"], 0),
    ("logic", "insiemi-relazioni", None, "Se A e sottoinsieme proprio di B:", ["A=B", "A contiene B", "Esiste almeno un elemento di B non in A", "A e B disgiunti"], 2),
    ("logic", "insiemi-relazioni", None, "In due insiemi disgiunti con cardinalita 12 e 9, l'unione ha cardinalita:", ["3", "12", "21", "108"], 2),

    ("logic", "logica-argomentativa", None, "Quale e una petizione di principio?", ["Usare la conclusione come premessa", "Confutare con dati", "Usare analogia pertinente", "Fornire controesempio"], 0),
    ("logic", "logica-argomentativa", None, "Lo slippery slope consiste nel:", ["Concludere conseguenze estreme senza passaggi solidi", "Confrontare due studi randomizzati", "Negare il conseguente", "Usare definizioni precise"], 0),
    ("logic", "logica-argomentativa", None, "Un argomento robusto in ambito test e:", ["Ripetibile, coerente, basato su evidenze", "Basato su intuizione personale", "Basato su autorita unica", "Ricco di retorica"], 0),
    ("logic", "logica-argomentativa", None, "Il cherry picking e:", ["Selezionare solo dati favorevoli", "Usare tutti i dati disponibili", "Fare meta-analisi", "Applicare randomizzazione"], 0),
    ("logic", "logica-argomentativa", None, "Confondere frequenza con gravita del rischio e un errore di:", ["Pertinenza statistica", "Pronuncia", "Ortografia", "Geometria"], 0),
]

NULL_TOPIC_MAP = {
    "sintesi proteica": "cellula-eucariotica",
    "processo di mitosi": "mitosi-meiosi",
    "trasporto di ossigeno": "sistemi-organo",
    "semiconservativa": "dna-rna-proteine",
    "formula molecolare del glucosio": "carboidrati",
    "legame peptidico": "proteine-struttura",
    "numero di avogadro": "atomo-struttura",
    "rivestimento esterno del corpo umano": "tessuti-animali",
    "sistema nervoso autonomo": "sistema-nervoso",
}


def seed_quiz(conn: sqlite3.Connection) -> tuple[int, int]:
    inserted = 0
    skipped = 0
    for topic_slug, question_it, choices, correct_index in LOGIC_QUIZ_V2:
        existing = conn.execute("SELECT id FROM quiz_questions WHERE question_it=?", (question_it,)).fetchone()
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
    for subject, topic_slug, source_year, question_it, choices, correct_index in LOGIC_EXAM_V2:
        existing = conn.execute("SELECT id FROM exam_questions WHERE question_it=?", (question_it,)).fetchone()
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


def map_null_topics(conn: sqlite3.Connection) -> int:
    updated = 0
    rows = conn.execute("SELECT id, question_it FROM exam_questions WHERE topic_slug IS NULL").fetchall()
    for row_id, text in rows:
        normalized = (text or "").lower()
        mapped_slug = None
        for key, slug in NULL_TOPIC_MAP.items():
            if key in normalized:
                mapped_slug = slug
                break
        if mapped_slug:
            conn.execute("UPDATE exam_questions SET topic_slug=? WHERE id=?", (mapped_slug, row_id))
            updated += 1
    return updated


def main() -> None:
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        quiz_i, quiz_s = seed_quiz(conn)
        exam_i, exam_s = seed_exam(conn)
        mapped = map_null_topics(conn)
        conn.commit()
    finally:
        conn.close()

    print(f"Logic quiz v2: inserted={quiz_i}, skipped={quiz_s}")
    print(f"Logic exam v2: inserted={exam_i}, skipped={exam_s}")
    print(f"Mapped legacy exam topic_slug from NULL: {mapped}")


if __name__ == "__main__":
    main()
