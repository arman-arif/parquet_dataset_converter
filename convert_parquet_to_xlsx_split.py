"""Convert every .parquet file in ./data to multiple .xlsx files in ./output.

Each parquet file becomes <name>_part001.xlsx, <name>_part002.xlsx, ...
with at most ROWS_PER_FILE rows each (one sheet per file).

Requires: pip install pandas pyarrow xlsxwriter
"""
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output/splits"

# Must stay below Excel's hard limit of 1,048,576 rows (minus 1 for the header)
ROWS_PER_FILE = 1_000_000
BATCH_SIZE = 100_000


def write_part(frames: list, dst: Path) -> int:
    df = pd.concat(frames, ignore_index=True)

    # Excel can't store timezone-aware datetimes
    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)

    df.to_excel(dst, index=False, engine="xlsxwriter")
    return len(df)


def convert(src: Path) -> None:
    parquet = pq.ParquetFile(src)
    frames, buffered, part = [], 0, 0

    def flush() -> None:
        nonlocal frames, buffered, part
        part += 1
        dst = OUTPUT_DIR / f"{src.stem}_part{part:03d}.xlsx"
        rows = write_part(frames, dst)
        print(f"  wrote {dst.relative_to(BASE_DIR)} ({rows} rows)")
        frames, buffered = [], 0

    for batch in parquet.iter_batches(batch_size=BATCH_SIZE):
        frames.append(batch.to_pandas())
        buffered += batch.num_rows
        if buffered >= ROWS_PER_FILE:
            flush()

    if frames:
        flush()


def main() -> None:
    files = sorted(DATA_DIR.glob("*.parquet"))
    if not files:
        raise SystemExit(f"No .parquet files found in {DATA_DIR}")

    OUTPUT_DIR.mkdir(exist_ok=True)

    for src in files:
        print(f"Converting {src.name}")
        convert(src)

    print("Done.")


if __name__ == "__main__":
    main()
