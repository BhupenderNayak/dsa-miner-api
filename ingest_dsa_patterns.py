import argparse
import re
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


EXPECTED_COLUMNS = {
    "id": "leetcode_id",
    "question id": "leetcode_id",
    "title": "title",
    "problem": "title",
    "problem title": "title",
    "difficulty": "difficulty",
    "acceptance": "acceptance_rate",
    "acceptance rate": "acceptance_rate",
    "frequency": "frequency_count",
    "frequency count": "frequency_count",
    "leetcode question link": "url",
    "link": "url",
    "url": "url",
    "topics": "topics",
    "topic tags": "topics",
    "patterns": "topics",
}

TOPIC_TO_PATTERN = {
    "array": "Array",
    "string": "String",
    "hash table": "Hash Table",
    "two pointers": "Two Pointers",
    "sliding window": "Sliding Window",
    "binary search": "Binary Search",
    "dynamic programming": "Dynamic Programming",
    "depth-first search": "DFS",
    "breadth-first search": "BFS",
    "graph": "Graph",
    "tree": "Tree",
    "binary tree": "Tree",
    "heap (priority queue)": "Heap / Priority Queue",
    "priority queue": "Heap / Priority Queue",
    "stack": "Stack",
    "queue": "Queue",
    "linked list": "Linked List",
    "trie": "Trie",
    "backtracking": "Backtracking",
    "greedy": "Greedy",
    "sort": "Sorting",
    "sorting": "Sorting",
    "matrix": "Matrix",
    "bit manipulation": "Bit Manipulation",
    "union find": "Union Find",
    "topological sort": "Topological Sort",
    "prefix sum": "Prefix Sum",
}


def normalize_column_name(column: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(column).strip().lower())
    return EXPECTED_COLUMNS.get(cleaned, cleaned.replace(" ", "_"))


def normalize_difficulty(value: object) -> Optional[str]:
    if pd.isna(value):
        return None
    text = str(value).strip().title()
    return text if text in {"Easy", "Medium", "Hard"} else None


def parse_numeric(value: object, default: float = 0.0) -> float:
    if pd.isna(value):
        return default
    text = str(value).strip().replace("%", "").replace(",", "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def parse_acceptance_rate(value: object) -> Optional[float]:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    number = parse_numeric(text, default=-1.0)
    if number < 0:
        return None
    if "%" in text or number > 1:
        number = number / 100.0
    return round(number, 4)


def slug_from_url(url: object) -> Optional[str]:
    if pd.isna(url):
        return None
    match = re.search(r"leetcode\.com/problems/([^/\s]+)/?", str(url))
    return match.group(1) if match else None


def clean_title(value: object) -> Optional[str]:
    if pd.isna(value):
        return None
    title = re.sub(r"\s+", " ", str(value).strip())
    return title or None


def infer_company_and_timeframe(csv_path: Path) -> tuple[str, str]:
    stem = csv_path.stem.strip()
    parent = csv_path.parent.name.strip()

    named_timeframes = {
        "1. thirty days": "thirty_days",
        "2. three months": "three_months",
        "3. six months": "six_months",
        "4. more than six months": "more_than_six_months",
        "5. all": "all_time",
    }

    lowered_stem = stem.lower()
    if lowered_stem in named_timeframes:
        return parent, named_timeframes[lowered_stem]

    match = re.match(r"(?P<company>.+)_(?P<timeframe>alltime|6months|1year|2year)$", stem, re.I)
    if match:
        company = match.group("company").replace("_", " ").title()
        timeframe = {
            "alltime": "all_time",
            "6months": "six_months",
            "1year": "one_year",
            "2year": "two_years",
        }[match.group("timeframe").lower()]
        return company, timeframe

    return parent if parent else "Unknown", "all_time"


def normalize_pattern(topic: str) -> str:
    topic_clean = re.sub(r"\s+", " ", topic.strip())
    return TOPIC_TO_PATTERN.get(topic_clean.lower(), topic_clean.title())


def split_patterns(value: object) -> list[str]:
    if pd.isna(value):
        return ["Uncategorized"]
    parts = re.split(r"[,;|]", str(value))
    patterns = sorted({normalize_pattern(part) for part in parts if part.strip()})
    return patterns or ["Uncategorized"]


def discover_csv_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(input_path.rglob("*.csv"))


def load_and_clean_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [normalize_column_name(column) for column in df.columns]

    for required_column in ["leetcode_id", "title", "difficulty", "acceptance_rate", "frequency_count", "url", "topics"]:
        if required_column not in df.columns:
            df[required_column] = None

    company, timeframe = infer_company_and_timeframe(csv_path)
    df["company_name"] = company
    df["timeframe"] = timeframe
    df["source_file"] = str(csv_path)

    df["title"] = df["title"].apply(clean_title)
    df = df.dropna(subset=["title"]).copy()
    df["leetcode_id"] = pd.to_numeric(df["leetcode_id"], errors="coerce").astype("Int64")
    df["difficulty"] = df["difficulty"].apply(normalize_difficulty)
    df["acceptance_rate"] = df["acceptance_rate"].apply(parse_acceptance_rate)
    df["frequency_count"] = df["frequency_count"].apply(parse_numeric)
    df["url"] = df["url"].fillna("").astype(str).str.strip()
    df["slug"] = df["url"].apply(slug_from_url)
    df["patterns"] = df["topics"].apply(split_patterns)
    return df


def get_connection(args: argparse.Namespace):
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError("Missing dependency: install psycopg2-binary before running ingestion.") from exc

    return psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=args.database,
        user=args.user,
        password=args.password,
    )


def fetch_id_map(cursor, table: str, id_column: str, name_column: str) -> dict[str, int]:
    cursor.execute(f"SELECT {id_column}, {name_column} FROM {table}")
    return {name: row_id for row_id, name in cursor.fetchall()}


def ingest_dataframe(conn, df: pd.DataFrame) -> None:
    try:
        from psycopg2.extras import execute_values
    except ImportError as exc:
        raise RuntimeError("Missing dependency: install psycopg2-binary before running ingestion.") from exc

    with conn.cursor() as cur:
        companies = sorted(df["company_name"].dropna().unique())
        execute_values(
            cur,
            "INSERT INTO companies (company_name) VALUES %s ON CONFLICT (company_name) DO NOTHING",
            [(company,) for company in companies],
        )

        problem_rows = [
            (
                None if pd.isna(row.leetcode_id) else int(row.leetcode_id),
                row.title,
                row.slug,
                row.difficulty,
                row.acceptance_rate,
                row.url or None,
            )
            for row in df.itertuples(index=False)
        ]
        execute_values(
            cur,
            """
            INSERT INTO problems (leetcode_id, title, slug, difficulty, acceptance_rate, url)
            VALUES %s
            ON CONFLICT (title) DO UPDATE SET
                leetcode_id = COALESCE(EXCLUDED.leetcode_id, problems.leetcode_id),
                slug = COALESCE(EXCLUDED.slug, problems.slug),
                difficulty = COALESCE(EXCLUDED.difficulty, problems.difficulty),
                acceptance_rate = COALESCE(EXCLUDED.acceptance_rate, problems.acceptance_rate),
                url = COALESCE(EXCLUDED.url, problems.url)
            """,
            problem_rows,
        )

        all_patterns = sorted({pattern for patterns in df["patterns"] for pattern in patterns})
        execute_values(
            cur,
            "INSERT INTO patterns (pattern_name) VALUES %s ON CONFLICT (pattern_name) DO NOTHING",
            [(pattern,) for pattern in all_patterns],
        )

        company_ids = fetch_id_map(cur, "companies", "company_id", "company_name")
        problem_ids = fetch_id_map(cur, "problems", "problem_id", "title")
        pattern_ids = fetch_id_map(cur, "patterns", "pattern_id", "pattern_name")

        frequency_rows = [
            (
                company_ids[row.company_name],
                problem_ids[row.title],
                row.timeframe,
                row.frequency_count,
                row.source_file,
            )
            for row in df.itertuples(index=False)
        ]
        execute_values(
            cur,
            """
            INSERT INTO company_problem_frequencies
                (company_id, problem_id, timeframe, frequency_count, source_file)
            VALUES %s
            ON CONFLICT (company_id, problem_id, timeframe) DO UPDATE SET
                frequency_count = EXCLUDED.frequency_count,
                source_file = EXCLUDED.source_file,
                last_seen_at = NOW()
            """,
            frequency_rows,
        )

        problem_pattern_rows = sorted({
            (problem_ids[row.title], pattern_ids[pattern])
            for row in df.itertuples(index=False)
            for pattern in row.patterns
        })
        execute_values(
            cur,
            """
            INSERT INTO problem_patterns (problem_id, pattern_id)
            VALUES %s
            ON CONFLICT DO NOTHING
            """,
            problem_pattern_rows,
        )

    conn.commit()


def ingest_files(conn, csv_files: Iterable[Path]) -> None:
    total_rows = 0
    for csv_file in csv_files:
        print(f"Reading: {csv_file}")
        df = load_and_clean_csv(csv_file)
        if df.empty:
            print(f"Skipped empty file after cleaning: {csv_file}")
            continue
        ingest_dataframe(conn, df)
        total_rows += len(df)
        print(f"Ingested {len(df)} cleaned rows from {csv_file.name}")
    print(f"DSA pattern ingestion complete. Total cleaned rows ingested: {total_rows}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest company-wise LeetCode CSV data into PostgreSQL.")
    parser.add_argument("--input-path", required=True, help="CSV file or directory containing CSV files.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default=5432, type=int)
    parser.add_argument("--database", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_path)
    csv_files = discover_csv_files(input_path)
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found under {input_path}")

    print(f"Found {len(csv_files)} CSV file(s). Connecting to PostgreSQL...")
    conn = get_connection(args)
    try:
        print("Connected successfully.")
        ingest_files(conn, csv_files)
    finally:
        conn.close()
        print("Connection closed.")
    print("Ingestion successful.")


if __name__ == "__main__":
    main()
