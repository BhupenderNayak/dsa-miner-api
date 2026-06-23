"""Automatically assign DSA patterns to untagged LeetCode problems.

The script treats problems with no pattern mapping, or only an
"Uncategorized" mapping, as untagged. It is safe to rerun because database
inserts use PostgreSQL ON CONFLICT handling.
"""

import argparse
import os
from collections.abc import Iterator, Sequence
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


DEFAULT_DATABASE_URL = (
    "postgresql+psycopg2://postgres:postgres@localhost:5432/dsa_miner"
)
DEFAULT_MODEL = "facebook/bart-large-mnli"
MIN_CONFIDENCE = 0.35
hypothesis_template=(
    "This programming problem focuses on the concept or language of {}."
),

# Natural-language labels improve zero-shot inference. Values are canonical
# database names, which avoids creating aliases such as both "BFS" and
# "Breadth-First Search (BFS)" in the patterns table.
PATTERN_LABELS = {
    "arrays, hashing, prefix sums, matrices, or Kadane's algorithm": "Arrays / Hashing",
    "strings, parsing, tries, or string matching": "Strings",
    "two pointers, sliding window, or fast and slow pointers": "Two Pointers / Sliding Window",
    "binary search, sorting, or divide and conquer": "Binary Search / Sorting",
    "stacks, monotonic stacks, queues, or deques": "Stack / Queue",
    "linked list manipulation": "Linked Lists",
    "graphs, trees, BFS, DFS, shortest paths, topological sort, or union find": "Graphs / Trees",
    "dynamic programming, recursion, or backtracking": "Dynamic Programming / Backtracking",
    "greedy algorithms, intervals, or scheduling": "Greedy / Intervals",
    "heaps or priority queues": "Heap / Priority Queue",
    "math, number theory, or bit manipulation": "Math / Bit Manipulation",
    "custom data structure or object-oriented design": "Design / Data Structures",
    "JavaScript, web APIs, promises, closures, or frontend programming": "JavaScript/Web",
    "Pandas, DataFrames, tabular data, or data manipulation": "Pandas/Data Manipulation",
    "SQL, relational databases, joins, grouping, or database queries": "Database/SQL",
}
CANDIDATE_PATTERNS = list(PATTERN_LABELS)

FETCH_UNTAGGED_SQL = text(
    """
    SELECT
        p.problem_id,
        p.title,
        COALESCE(
            to_jsonb(p) ->> 'description',
            to_jsonb(p) ->> 'problem_description',
            ''
        ) AS description
    FROM problems p
    WHERE NOT EXISTS (
        SELECT 1
        FROM problem_patterns pp
        JOIN patterns pat ON pat.pattern_id = pp.pattern_id
        WHERE pp.problem_id = p.problem_id
          AND lower(pat.pattern_name) <> 'uncategorized'
    )
    ORDER BY p.problem_id
    LIMIT :row_limit
    """
)

UPSERT_PATTERN_SQL = text(
    """
    INSERT INTO patterns (pattern_name)
    VALUES (:pattern_name)
    ON CONFLICT (pattern_name) DO UPDATE
        SET pattern_name = EXCLUDED.pattern_name
    RETURNING pattern_id
    """
)

INSERT_MAPPING_SQL = text(
    """
    INSERT INTO problem_patterns (problem_id, pattern_id)
    VALUES (:problem_id, :pattern_id)
    ON CONFLICT (problem_id, pattern_id) DO NOTHING
    """
)

DELETE_UNCATEGORIZED_SQL = text(
    """
    DELETE FROM problem_patterns pp
    USING patterns pat
    WHERE pp.pattern_id = pat.pattern_id
      AND pp.problem_id = :problem_id
      AND lower(pat.pattern_name) = 'uncategorized'
    """
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tag unclassified DSA problems with a zero-shot model."
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="SQLAlchemy PostgreSQL URL. Defaults to DATABASE_URL or local dsa_miner.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum problems to process. Use 0 for all untagged problems.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Number of problem texts sent to the model per inference batch.",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=MIN_CONFIDENCE,
        help="Confidence threshold from 0.35 to 1.0. Predictions below it are not saved.",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Inference device. Auto uses CUDA when PyTorch detects it.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run classification and print predictions without updating PostgreSQL.",
    )
    args = parser.parse_args()

    if args.limit < 0:
        parser.error("--limit must be 0 or greater")
    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")
    if not MIN_CONFIDENCE <= args.min_confidence <= 1.0:
        parser.error(
            f"--min-confidence must be between {MIN_CONFIDENCE:.2f} and 1.0"
        )
    return args


def chunks(items: Sequence[dict[str, Any]], size: int) -> Iterator[Sequence[dict[str, Any]]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def create_database_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def fetch_untagged_problems(engine: Engine, row_limit: int) -> list[dict[str, Any]]:
    # PostgreSQL interprets LIMIT NULL as no limit.
    limit_value = row_limit if row_limit > 0 else None
    with engine.connect() as connection:
        rows = connection.execute(
            FETCH_UNTAGGED_SQL,
            {"row_limit": limit_value},
        ).mappings()
        return [dict(row) for row in rows]


def build_problem_text(problem: dict[str, Any]) -> str:
    title = str(problem["title"]).strip()
    description = str(problem.get("description") or "").strip()
    if description:
        # Zero-shot inference is expensive; a bounded description is enough to
        # expose the core constraints without feeding an entire HTML page.
        return f"LeetCode problem title: {title}. Problem description: {description[:2000]}"
    return f"LeetCode algorithm problem title: {title}."


def load_classifier(model_name: str, requested_device: str):
    try:
        import torch
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError(
            "Missing ML dependencies. Install torch and transformers before running."
        ) from exc

    cuda_available = torch.cuda.is_available()
    if requested_device == "cuda" and not cuda_available:
        raise RuntimeError("--device cuda was requested, but PyTorch cannot detect a CUDA GPU.")

    use_cuda = requested_device == "cuda" or (
        requested_device == "auto" and cuda_available
    )
    pipeline_device = 0 if use_cuda else -1
    device_name = torch.cuda.get_device_name(0) if use_cuda else "CPU"
    print(f"Loading zero-shot model '{model_name}' on {device_name}...")

    classifier = pipeline(
        task="zero-shot-classification",
        model=model_name,
        device=pipeline_device,
    )
    print("Model loaded successfully.")
    return classifier


def classify_batch(classifier, problems: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    problem_texts = [build_problem_text(problem) for problem in problems]
    raw_results = classifier(
        problem_texts,
        candidate_labels=CANDIDATE_PATTERNS,
        hypothesis_template=(
            "The algorithmic technique used to solve this programming problem is {}."
        ),
        multi_label=False,
        truncation=True,
    )

    if isinstance(raw_results, dict):
        raw_results = [raw_results]

    predictions = []
    for problem, result in zip(problems, raw_results):
        classifier_label = result["labels"][0]
        predictions.append(
            {
                "problem_id": problem["problem_id"],
                "title": problem["title"],
                "pattern_name": PATTERN_LABELS[classifier_label],
                "confidence": float(result["scores"][0]),
            }
        )
    return predictions


def save_predictions(engine: Engine, predictions: Sequence[dict[str, Any]]) -> int:
    saved = 0
    with engine.begin() as connection:
        pattern_ids: dict[str, int] = {}
        for prediction in predictions:
            pattern_name = prediction["pattern_name"]
            if pattern_name not in pattern_ids:
                pattern_ids[pattern_name] = connection.execute(
                    UPSERT_PATTERN_SQL,
                    {"pattern_name": pattern_name},
                ).scalar_one()

            connection.execute(
                DELETE_UNCATEGORIZED_SQL,
                {"problem_id": prediction["problem_id"]},
            )
            connection.execute(
                INSERT_MAPPING_SQL,
                {
                    "problem_id": prediction["problem_id"],
                    "pattern_id": pattern_ids[pattern_name],
                },
            )
            saved += 1
    return saved


def main() -> None:
    args = parse_args()
    print("Connecting to PostgreSQL...")
    engine = create_database_engine(args.database_url)

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database connection successful.")

        problems = fetch_untagged_problems(engine, args.limit)
        print(f"Found {len(problems)} untagged problem(s).")
        print(f"Strict confidence threshold: {args.min_confidence:.0%}")
        if not problems:
            print("Nothing to tag. Database is already up to date.")
            return

        classifier = load_classifier(args.model, args.device)
        processed = 0
        tagged = 0
        skipped = 0

        for batch_number, problem_batch in enumerate(
            chunks(problems, args.batch_size),
            start=1,
        ):
            print(
                f"Classifying batch {batch_number} "
                f"({processed + 1}-{processed + len(problem_batch)} of {len(problems)})..."
            )
            predictions = classify_batch(classifier, problem_batch)
            accepted = []

            for prediction in predictions:
                confidence = prediction["confidence"]
                status = "TAG" if confidence >= args.min_confidence else "SKIP"
                skip_note = (
                    ""
                    if status == "TAG"
                    else " - below threshold; database unchanged"
                )
                print(
                    f"  [{status}] #{prediction['problem_id']} {prediction['title']} "
                    f"-> {prediction['pattern_name']} ({confidence:.1%}){skip_note}"
                )
                if confidence >= args.min_confidence:
                    accepted.append(prediction)
                else:
                    skipped += 1

            if accepted and not args.dry_run:
                saved = save_predictions(engine, accepted)
                tagged += saved
                print(f"Committed {saved} pattern assignment(s) from this batch.")
            elif accepted:
                tagged += len(accepted)
                print(f"Dry run: would save {len(accepted)} assignment(s).")

            processed += len(problem_batch)

        mode = "would be tagged" if args.dry_run else "tagged"
        print("Auto-tagging complete.")
        print(f"Processed: {processed} | {mode.title()}: {tagged} | Skipped: {skipped}")
    finally:
        engine.dispose()
        print("Database connection pool closed.")


if __name__ == "__main__":
    main()
