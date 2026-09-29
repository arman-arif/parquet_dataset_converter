"""Convert every .parquet file in ./data to .csv in ./output.

Streams each file in batches, so memory use stays low even for huge files.

Requires: pip install pyarrow pandas
"""
from pathlib import Path

import pyarrow.parquet as pq

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

BATCH_SIZE = 100_000


def convert(src: Path, dst: Path) -> None:
    parquet = pq.ParquetFile(src)
    rows = 0
    with open(dst, "w", newline="", encoding="utf-8") as out:
        for i, batch in enumerate(parquet.iter_batches(batch_size=BATCH_SIZE)):
            batch.to_pandas().to_csv(out, index=False, header=(i == 0))
            rows += batch.num_rows
    print(f"  wrote {rows} rows")


def main() -> None:
    files = sorted(DATA_DIR.glob("*.parquet"))
    if not files:
        raise SystemExit(f"No .parquet files found in {DATA_DIR}")

    OUTPUT_DIR.mkdir(exist_ok=True)

    for src in files:
        dst = OUTPUT_DIR / f"{src.stem}.csv"
        print(f"Converting {src.name} -> {dst.relative_to(BASE_DIR)}")
        convert(src, dst)

    print("Done.")


if __name__ == "__main__":
    main()
