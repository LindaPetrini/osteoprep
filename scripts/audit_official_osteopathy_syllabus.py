#!/usr/bin/env python3
"""Audit app curriculum against official Professioni Sanitarie syllabus (DM 586/2025, Allegato A)."""

import argparse
import os
import sqlite3
from dataclasses import dataclass

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "osteoprep.db")


@dataclass
class Area:
    code: str
    label: str
    subject_scope: tuple[str, ...]
    must_tokens: tuple[str, ...]
    nice_tokens: tuple[str, ...] = ()


AREAS = [
    Area(
        code="A1",
        label="Competenze di lettura + conoscenze storico-sociali/istituzionali",
        subject_scope=("logic",),
        must_tokens=("brani", "argoment"),
        nice_tokens=("storia", "istituz", "cittadin"),
    ),
    Area(
        code="A2",
        label="Ragionamento logico e problemi",
        subject_scope=("logic",),
        must_tokens=("logic", "sillog", "condizion", "problem", "serie"),
    ),
    Area(
        code="B1",
        label="Biologia cellulare, virus, membrana",
        subject_scope=("biology",),
        must_tokens=("cellula", "membrana", "nucleo", "virus"),
    ),
    Area(
        code="B2",
        label="Ciclo cellulare, ereditarieta, genetica, mutazioni, evoluzione, biotech",
        subject_scope=("biology",),
        must_tokens=("mitosi", "genetic", "dna", "evoluz", "biotecn"),
    ),
    Area(
        code="B3",
        label="Anatomia/fisiologia, tessuti, sistemi, omeostasi, bioenergetica",
        subject_scope=("biology",),
        must_tokens=("tessuti", "sistemi", "nervoso", "respirazione", "fotosintesi"),
    ),
    Area(
        code="C1",
        label="Struttura materia, atomo, tavola periodica, legami",
        subject_scope=("chemistry",),
        must_tokens=("atomo", "tavola", "legami"),
    ),
    Area(
        code="C2",
        label="Stechiometria, soluzioni, equilibrio, redox, acidi-basi, pH, buffer",
        subject_scope=("chemistry",),
        must_tokens=("reazioni", "soluzioni", "equilibrio", "ossidor", "acidi"),
    ),
    Area(
        code="C3",
        label="Organica + gruppi funzionali + biomolecole",
        subject_scope=("chemistry",),
        must_tokens=("organica", "carboidrati", "lipidi", "proteine", "enzimi"),
    ),
    Area(
        code="M1",
        label="Matematica: algebra, funzioni, geometria/trigonometria, probabilita/statistica",
        subject_scope=("physics",),
        must_tokens=("algebra", "funzioni", "geometria", "probabil"),
    ),
    Area(
        code="F1",
        label="Fisica: grandezze/misure, cinematica, dinamica, fluidi",
        subject_scope=("physics",),
        must_tokens=("grandezze", "cinematica", "dinamica", "fluid"),
    ),
    Area(
        code="F2",
        label="Fisica: termodinamica, elettromagnetismo",
        subject_scope=("physics",),
        must_tokens=("termodinamica", "elettromagnet"),
    ),
]


def _norm(text: str) -> str:
    return (text or "").lower()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit app curriculum against official osteopathy-entry syllabus areas."
    )
    parser.add_argument(
        "--db-path",
        default=DB_PATH,
        help=f"SQLite DB path (default: {DB_PATH})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any area is PARTIAL or GAP.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.db_path):
        raise SystemExit(f"Database not found: {args.db_path}")

    conn = sqlite3.connect(args.db_path)
    try:
        rows = conn.execute(
            "select subject, slug, title_it, title_en from topics order by subject, order_in_subject"
        ).fetchall()
    finally:
        conn.close()

    by_subject: dict[str, list[tuple[str, str, str]]] = {}
    for subject, slug, title_it, title_en in rows:
        by_subject.setdefault(subject, []).append((slug, _norm(title_it), _norm(title_en)))

    print("=== OFFICIAL SYLLABUS ALIGNMENT (DM 586/2025 Allegato A) ===")
    covered = 0
    partial = 0
    gaps = 0

    for area in AREAS:
        tokens_found = set()
        matched_slugs: list[str] = []
        candidates = []
        for subject in area.subject_scope:
            candidates.extend(by_subject.get(subject, []))
        for slug, title_it, title_en in candidates:
            haystack = f"{slug} {title_it} {title_en}"
            if any(token in haystack for token in area.must_tokens):
                matched_slugs.append(slug)
            for token in area.must_tokens:
                if token in haystack:
                    tokens_found.add(token)

        required = len(area.must_tokens)
        found = len(tokens_found)
        ratio = found / required if required else 0.0

        if ratio >= 0.8:
            status = "COVERED"
            covered += 1
        elif ratio > 0:
            status = "PARTIAL"
            partial += 1
        else:
            status = "GAP"
            gaps += 1

        uniq = sorted(set(matched_slugs))
        print(f"\n[{area.code}] {status} ({found}/{required}) - {area.label}")
        print(f"  tokens found: {', '.join(sorted(tokens_found)) if tokens_found else '-'}")
        print(f"  mapped topics: {', '.join(uniq) if uniq else '-'}")

        if area.nice_tokens:
            nice_found = []
            for token in area.nice_tokens:
                if any(token in f'{slug} {it} {en}' for slug, it, en in candidates):
                    nice_found.append(token)
            print(f"  nice-to-have signals: {', '.join(nice_found) if nice_found else '-'}")

    print("\n--- SUMMARY ---")
    print(f"Areas covered: {covered}")
    print(f"Areas partial: {partial}")
    print(f"Areas gap:     {gaps}")
    if args.strict and (partial > 0 or gaps > 0):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
