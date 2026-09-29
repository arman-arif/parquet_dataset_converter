"""Convert every .parquet file in ./data to .xlsx in ./output.

Requires: pip install pandas pyarrow xlsxwriter
"""
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Excel's hard row limit per sheet
EXCEL_MAX_ROWS = 1_048_576


def convert(src: Path, dst: Path) -> None:
    df = pd.read_parquet(src)

    # Excel can't store timezone-aware datetimes
    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)

    if len(df) >= EXCEL_MAX_ROWS:
        print(f"  warning: {len(df)} rows exceed Excel limit; splitting across sheets")
        step = EXCEL_MAX_ROWS - 1  # leave room for header
        with pd.ExcelWriter(dst, engine="xlsxwriter") as writer:
            for i, start in enumerate(range(0, len(df), step), 1):
                df.iloc[start:start + step].to_excel(writer, sheet_name=f"Sheet{i}", index=False)
    else:
        df.to_excel(dst, index=False, engine="xlsxwriter")


def main() -> None:
    files = sorted(DATA_DIR.glob("*.parquet"))
    if not files:
        raise SystemExit(f"No .parquet files found in {DATA_DIR}")

    OUTPUT_DIR.mkdir(exist_ok=True)

    for src in files:
        dst = OUTPUT_DIR / f"{src.stem}.xlsx"
        print(f"Converting {src.name} -> {dst.relative_to(BASE_DIR)}")
        convert(src, dst)

    print("Done.")


if __name__ == "__main__":
    main()
