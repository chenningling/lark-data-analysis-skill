#!/usr/bin/env python3
"""Profile Excel/CSV inputs for the lark-data-analysis-report skill."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    pd = None


def read_tables(path: Path) -> list[tuple[str, Any]]:
    suffix = path.suffix.lower()
    if pd is None:
        if suffix in {".csv", ".tsv"}:
            delimiter = "\t" if suffix == ".tsv" else ","
            with path.open(newline="", encoding="utf-8-sig") as f:
                return [(path.stem, list(csv.DictReader(f, delimiter=delimiter)))]
        raise SystemExit(
            "Excel profiling requires pandas/openpyxl in this Python environment. "
            "Use the workspace Excel runtime, install those packages, or convert the sheet to CSV first."
        )
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        sheets = pd.read_excel(path, sheet_name=None)
        return [(str(name), df) for name, df in sheets.items()]
    if suffix == ".csv":
        return [(path.stem, pd.read_csv(path))]
    if suffix == ".tsv":
        return [(path.stem, pd.read_csv(path, sep="\t"))]
    raise ValueError(f"Unsupported file type: {path}")


def dtype_label(series: Any) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "number"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    return "text"


def series_profile(series: Any) -> dict[str, Any]:
    non_null = series.dropna()
    result: dict[str, Any] = {
        "字段名": str(series.name),
        "推断类型": dtype_label(series),
        "总行数": int(len(series)),
        "缺失数": int(series.isna().sum()),
        "缺失率": round(float(series.isna().mean()), 4) if len(series) else 0,
        "唯一值数": int(non_null.nunique(dropna=True)),
        "样例值": ", ".join(map(str, non_null.astype(str).head(3).tolist())),
    }
    if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
        desc = non_null.describe()
        result.update(
            {
                "最小值": None if non_null.empty else float(desc["min"]),
                "最大值": None if non_null.empty else float(desc["max"]),
                "平均值": None if non_null.empty else float(desc["mean"]),
                "中位数": None if non_null.empty else float(non_null.median()),
            }
        )
    return result


def csv_column_profile(name: str, values: list[str | None]) -> dict[str, Any]:
    normalized = [v.strip() if isinstance(v, str) else v for v in values]
    non_null = [v for v in normalized if v not in (None, "")]
    numeric_values: list[float] = []
    numeric = True
    for value in non_null:
        try:
            numeric_values.append(float(str(value).replace(",", "")))
        except ValueError:
            numeric = False
            break

    result: dict[str, Any] = {
        "字段名": name,
        "推断类型": "number" if numeric and non_null else "text",
        "总行数": len(values),
        "缺失数": len(values) - len(non_null),
        "缺失率": round((len(values) - len(non_null)) / len(values), 4) if values else 0,
        "唯一值数": len(set(non_null)),
        "样例值": ", ".join(map(str, non_null[:3])),
    }
    if numeric and numeric_values:
        sorted_values = sorted(numeric_values)
        midpoint = len(sorted_values) // 2
        median = (
            sorted_values[midpoint]
            if len(sorted_values) % 2
            else (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2
        )
        result.update(
            {
                "最小值": min(numeric_values),
                "最大值": max(numeric_values),
                "平均值": sum(numeric_values) / len(numeric_values),
                "中位数": median,
            }
        )
    return result


def profile_file(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    fields: list[dict[str, Any]] = []
    samples: dict[str, Any] = {}
    for sheet_name, table in read_tables(path):
        table_key = f"{path.name}::{sheet_name}"
        if pd is None:
            rows = table
            columns = list(rows[0].keys()) if rows else []
            catalog.append(
                {
                    "来源文件": path.name,
                    "工作表": sheet_name,
                    "行数": len(rows),
                    "字段数": len(columns),
                    "字段列表": ", ".join(map(str, columns)),
                }
            )
            samples[table_key] = rows[:5]
            for column in columns:
                item = csv_column_profile(column, [row.get(column) for row in rows])
                item.update({"来源文件": path.name, "工作表": sheet_name})
                fields.append(item)
            continue

        df = table
        catalog.append(
            {
                "来源文件": path.name,
                "工作表": sheet_name,
                "行数": int(df.shape[0]),
                "字段数": int(df.shape[1]),
                "字段列表": ", ".join(map(str, df.columns.tolist())),
            }
        )
        sample_rows = df.head(5).where(pd.notna(df), None).to_dict(orient="records")
        samples[table_key] = json_safe(sample_rows)
        for column in df.columns:
            item = series_profile(df[column])
            item.update({"来源文件": path.name, "工作表": sheet_name})
            fields.append(item)
    return catalog, fields, samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile Excel/CSV files for Lark analysis deposits.")
    parser.add_argument("files", nargs="+", help="Excel/CSV/TSV files to profile")
    parser.add_argument("--out-dir", default="analysis_profile", help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_catalog: list[dict[str, Any]] = []
    all_fields: list[dict[str, Any]] = []
    all_samples: dict[str, Any] = {}
    for file_arg in args.files:
        catalog, fields, samples = profile_file(Path(file_arg).expanduser().resolve())
        all_catalog.extend(catalog)
        all_fields.extend(fields)
        all_samples.update(samples)

    write_csv(out_dir / "00_input_catalog.csv", all_catalog)
    write_csv(out_dir / "01_field_quality_profile.csv", all_fields)
    (out_dir / "sample_rows.json").write_text(
        json.dumps(all_samples, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "input_tables": len(all_catalog),
        "profile_files": [
            str(out_dir / "00_input_catalog.csv"),
            str(out_dir / "01_field_quality_profile.csv"),
            str(out_dir / "sample_rows.json"),
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if pd is not None:
        if pd.isna(value):
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
    return value


if __name__ == "__main__":
    main()
