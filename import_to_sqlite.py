#!/usr/bin/env python3
"""
Fast MariaDB .sql.gz -> SQLite importer.

Strategy: Instead of parsing SQL text, we use regex to extract CREATE TABLE
blocks (converted to SQLite DDL) and then use executescript() for INSERT
blocks with minimal text fixups. This avoids character-by-character parsing.
"""

import gzip
import sqlite3
import re
import os
import sys
import time

INPUT_FILE  = "PROD-26-03-19.sql.gz"
OUTPUT_FILE = "PROD.db"


def clean_ddl(sql):
    """Convert MariaDB CREATE TABLE to SQLite-compatible DDL."""
    lines = sql.split("\n")
    out = []
    skip_gen_col = None

    for raw in lines:
        s = raw.strip()

        # Skip generated columns
        if "GENERATED ALWAYS AS" in s:
            m = re.match(r"`(\w+)`", s)
            if m:
                skip_gen_col = m.group(1)
            continue

        # Skip KEY/INDEX lines
        if re.match(r"(UNIQUE\s+)?KEY\s+`", s):
            continue

        # Skip key on generated column
        if skip_gen_col and f"KEY `{skip_gen_col}`" in s:
            continue

        line = raw
        # Type conversions
        line = re.sub(r"\bint\(\d+\)", "INTEGER", line, flags=re.I)
        line = re.sub(r"\btinyint\(\d+\)", "INTEGER", line, flags=re.I)
        line = re.sub(r"\bbigint\(\d+\)", "INTEGER", line, flags=re.I)
        line = re.sub(r"\bmediumtext\b", "TEXT", line, flags=re.I)
        line = re.sub(r"\blongtext\b", "TEXT", line, flags=re.I)
        line = re.sub(r"\bvarchar\(\d+\)", "TEXT", line, flags=re.I)
        line = re.sub(r"\bchar\(\d+\)", "TEXT", line, flags=re.I)
        line = re.sub(r"\btimestamp\b", "TEXT", line, flags=re.I)
        line = re.sub(r"\bdatetime\b", "TEXT", line, flags=re.I)
        line = re.sub(r"\bdouble\b", "REAL", line, flags=re.I)
        line = re.sub(r"\bfloat\b", "REAL", line, flags=re.I)
        line = re.sub(r"\s*AUTO_INCREMENT", "", line)
        line = re.sub(r"\s*CHARACTER\s+SET\s+\S+", "", line)
        line = re.sub(r"\s*COLLATE\s+\S+", "", line)
        line = line.replace("current_timestamp()", "CURRENT_TIMESTAMP")

        # Closing line: strip ENGINE, CHARSET, etc.
        if s.startswith(")"):
            line = re.sub(r"\)\s*(ENGINE|AUTO_INCREMENT|DEFAULT\s+CHARSET|COLLATE|ROW_FORMAT)\b[^;]*", ")", line)

        out.append(line)

    result = "\n".join(out)
    # Remove trailing commas before )
    result = re.sub(r",\s*\n\s*\)", "\n)", result)
    return result, skip_gen_col


def main():
    t0 = time.time()

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    conn = sqlite3.connect(OUTPUT_FILE)
    conn.execute("PRAGMA journal_mode = OFF")
    conn.execute("PRAGMA synchronous  = OFF")
    conn.execute("PRAGMA cache_size   = -256000")  # 256MB cache
    cur = conn.cursor()

    # Phase 1: Extract and execute all CREATE TABLE statements
    print("Phase 1: Creating tables...")
    create_buf = []
    in_create = False
    table_order = []
    gen_col_tables = {}  # table -> col_index to skip

    with gzip.open(INPUT_FILE, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if s.startswith("CREATE TABLE"):
                in_create = True
                create_buf = [line]
                continue
            if in_create:
                create_buf.append(line)
                if s.startswith(")"):
                    in_create = False
                    raw = "".join(create_buf)
                    m = re.search(r"`([^`]+)`", raw)
                    tname = m.group(1) if m else "unknown"

                    ddl, gen_col = clean_ddl(raw)

                    if gen_col:
                        # Figure out column index of generated col
                        idx = 0
                        for cl in create_buf:
                            cs = cl.strip()
                            if cs.startswith("`"):
                                if "GENERATED ALWAYS AS" in cs:
                                    gen_col_tables[tname] = idx
                                    break
                                idx += 1

                    try:
                        cur.execute(f"DROP TABLE IF EXISTS [{tname}]")
                        cur.execute(ddl)
                        table_order.append(tname)
                        print(f"  {tname}" + (f" (skip gen col idx {gen_col_tables[tname]})" if tname in gen_col_tables else ""))
                    except Exception as e:
                        print(f"  ERROR {tname}: {e}")
                        print(f"  DDL: {ddl[:300]}")
                    create_buf = []

    conn.commit()
    print(f"  {len(table_order)} tables created.\n")

    # Phase 2: Process INSERT statements
    # For tables WITHOUT generated columns: feed lines straight to executescript
    # with minimal fixup. For tables WITH generated columns (articles): parse tuples.
    print("Phase 2: Importing data...")

    pending_table = None
    insert_count = 0
    row_count = {}
    line_num = 0

    conn.execute("BEGIN")

    with gzip.open(INPUT_FILE, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_num += 1
            s = line.strip()

            if not s or s.startswith("--") or s.startswith("/*") or s.startswith("*"):
                continue
            if s.startswith("LOCK ") or s.startswith("UNLOCK ") or s.startswith("SET "):
                continue
            if s.startswith("CREATE TABLE") or s.startswith("DROP TABLE"):
                # Skip DDL on second pass
                if s.startswith("CREATE TABLE"):
                    # Skip until closing )
                    for skip_line in f:
                        if skip_line.strip().startswith(")"):
                            break
                continue

            # INSERT INTO header
            if s.startswith("INSERT INTO"):
                m = re.match(r"INSERT\s+INTO\s+`?([^`\s]+)`?\s+VALUES\s*$", s, re.I)
                if m:
                    pending_table = m.group(1)
                    continue
                m2 = re.match(r"INSERT\s+INTO\s+`?([^`\s]+)`?\s+VALUES\s*(\(.+)", s, re.I)
                if m2:
                    pending_table = m2.group(1)
                    s = m2.group(2).strip()
                    # Fall through to process
                else:
                    continue

            # Data lines
            if pending_table is not None:
                tbl = pending_table
                is_last = s.endswith(";")

                val = s.rstrip(",;").strip()
                if not val:
                    if is_last:
                        pending_table = None
                    continue

                skip_idx = gen_col_tables.get(tbl)

                if skip_idx is not None:
                    # Need to drop the generated column from values
                    # Parse the tuple manually (only articles table)
                    try:
                        # Use a trick: wrap in a SELECT and let Python parse
                        # Actually, let's just find the column boundaries
                        inner = val[1:-1] if val.startswith("(") and val.endswith(")") else val

                        # Quick parse: split by finding top-level commas
                        cols = []
                        depth = 0
                        in_str = False
                        escape_next = False
                        start = 0

                        for ci, ch in enumerate(inner):
                            if escape_next:
                                escape_next = False
                                continue
                            if ch == "\\" and in_str:
                                escape_next = True
                                continue
                            if ch == "'" and not escape_next:
                                in_str = not in_str
                                continue
                            if not in_str:
                                if ch == "(":
                                    depth += 1
                                elif ch == ")":
                                    depth -= 1
                                elif ch == "," and depth == 0:
                                    cols.append(inner[start:ci])
                                    start = ci + 1

                        cols.append(inner[start:])

                        if len(cols) > skip_idx:
                            cols.pop(skip_idx)

                        rebuilt = "(" + ",".join(cols) + ")"

                        # Fix MySQL escapes for SQLite: \' -> ''
                        # This is the fast path - just replace \' with ''
                        rebuilt = rebuilt.replace("\\'", "''")

                        sql = f"INSERT INTO [{tbl}] VALUES {rebuilt};"
                        cur.execute(sql)
                        row_count[tbl] = row_count.get(tbl, 0) + 1
                    except Exception as e:
                        if row_count.get(tbl, 0) < 3:
                            print(f"  WARN {tbl} L{line_num}: {str(e)[:100]}")

                else:
                    # No generated column - fast path: just fix escapes
                    fixed = val.replace("\\'", "''")
                    sql = f"INSERT INTO [{tbl}] VALUES {fixed};"
                    try:
                        cur.execute(sql)
                        row_count[tbl] = row_count.get(tbl, 0) + 1
                    except Exception as e:
                        if row_count.get(tbl, 0) < 3:
                            print(f"  WARN {tbl} L{line_num}: {str(e)[:100]}")

                insert_count += 1
                if insert_count % 5000 == 0:
                    conn.commit()
                    conn.execute("BEGIN")
                    elapsed = time.time() - t0
                    total = sum(row_count.values())
                    print(f"  {insert_count:>8,} rows | {elapsed:.0f}s | line {line_num:,}")

                if is_last:
                    pending_table = None

    conn.commit()

    # Report
    elapsed = time.time() - t0
    print(f"\n{'='*50}")
    print(f"Import completed in {elapsed:.1f}s")
    print(f"{'='*50}")
    print(f"\n{'Table':<20} {'Rows':>12}")
    print(f"{'-'*20} {'-'*12}")

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for (t,) in cur.fetchall():
        c = cur.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"{t:<20} {c:>12,}")

    conn.close()
    sz = os.path.getsize(OUTPUT_FILE)
    print(f"\nDatabase: {OUTPUT_FILE} ({sz / (1024**2):.0f} MB)")
    print("Done.")


if __name__ == "__main__":
    main()
