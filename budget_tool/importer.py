from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

REQUIRED_CANONICAL_COLUMNS = ["date", "amount", "description"]
CANONICAL_COLUMNS = ["date", "amount", "description", "account", "tx_id"]


class ImportError(ValueError):
    """Raised when import configuration is invalid."""


def _compute_tx_id(date: str, amount: float, description: str, account: str) -> str:
    raw = f"{date}|{amount:.2f}|{description.strip().lower()}|{account.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_transactions(csv_path: str | Path, import_config: dict) -> pd.DataFrame:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    columns = import_config.get("columns", {})
    date_format = import_config.get("date_format")
    delimiter = import_config.get("delimiter", ",")
    decimal = import_config.get("decimal", ".")

    for col in REQUIRED_CANONICAL_COLUMNS:
        if col not in columns:
            raise ImportError(f"Missing required mapping in config.columns: '{col}'")

    df = pd.read_csv(csv_path, delimiter=delimiter, decimal=decimal)

    mapped = pd.DataFrame()
    for canonical in REQUIRED_CANONICAL_COLUMNS + ["account"]:
        source = columns.get(canonical)
        if source is None:
            if canonical == "account":
                mapped[canonical] = ""
            continue
        if source not in df.columns:
            raise ImportError(f"Mapped source column '{source}' for '{canonical}' not found in CSV")
        mapped[canonical] = df[source]

    mapped["description"] = mapped["description"].astype(str).str.strip()
    mapped["account"] = mapped.get("account", "").fillna("").astype(str).str.strip()
    mapped["amount"] = pd.to_numeric(mapped["amount"], errors="coerce")
    if mapped["amount"].isna().any():
        bad = mapped[mapped["amount"].isna()]
        raise ImportError(f"Invalid amounts found in rows: {bad.index.tolist()[:5]}")

    dt = pd.to_datetime(mapped["date"], format=date_format, errors="coerce")
    if dt.isna().any():
        bad = mapped[dt.isna()]
        raise ImportError(f"Invalid dates found in rows: {bad.index.tolist()[:5]}")

    mapped["date"] = dt.dt.strftime("%Y-%m-%d")

    mapped["tx_id"] = mapped.apply(
        lambda row: _compute_tx_id(
            date=row["date"],
            amount=float(row["amount"]),
            description=row["description"],
            account=row["account"],
        ),
        axis=1,
    )

    mapped = mapped[CANONICAL_COLUMNS].copy()
    return mapped


def save_parquet(df: pd.DataFrame, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    return output_path
