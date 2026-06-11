from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd


def local_name(tag: str) -> str:
    """Return XML local tag name without namespace."""
    return tag.rsplit("}", 1)[-1]


def find_first_child(parent: ET.Element, name: str) -> ET.Element | None:
    for child in parent:
        if local_name(child.tag) == name:
            return child
    return None


def parse_int(text: str | None) -> int | None:
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def texture_to_category(texture_value: int | None) -> str | None:
    """
    Map LIDC texture score to category:
    1-2 -> ground-glass (non-solid)
    3   -> part-solid
    4-5 -> solid
    """
    if texture_value is None:
        return None
    if texture_value in (1, 2):
        return "ground-glass"
    if texture_value == 3:
        return "part-solid"
    if texture_value in (4, 5):
        return "solid"
    return None


def extract_texture_rows_from_xml(xml_path: Path, patient_id: str) -> list[dict]:
    rows: list[dict] = []
    try:
        root = ET.parse(xml_path).getroot()
    except Exception:
        return rows

    reading_session_index = 0
    for elem in root.iter():
        if local_name(elem.tag) != "readingSession":
            continue

        reading_session_index += 1
        for nodule_elem in elem:
            if local_name(nodule_elem.tag) != "unblindedReadNodule":
                continue

            nodule_id_elem = find_first_child(nodule_elem, "noduleID")
            characteristics_elem = find_first_child(nodule_elem, "characteristics")
            texture_elem = (
                find_first_child(characteristics_elem, "texture")
                if characteristics_elem is not None
                else None
            )

            texture_value = parse_int(texture_elem.text if texture_elem is not None else None)
            texture_category = texture_to_category(texture_value)

            # Keep only nodules that have a texture value.
            if texture_value is None or texture_category is None:
                continue

            rows.append(
                {
                    "patient_id": patient_id,
                    "xml_path": str(xml_path),
                    "reading_session_index": reading_session_index,
                    "nodule_id": nodule_id_elem.text.strip() if nodule_id_elem is not None and nodule_id_elem.text else None,
                    "texture": texture_value,
                    "texture_category": texture_category,
                }
            )
    return rows


def build_patient_summary(
    patient_ids: list[str], details_df: pd.DataFrame
) -> pd.DataFrame:
    summary_rows: list[dict] = []

    for patient_id in patient_ids:
        patient_df = details_df[details_df["patient_id"] == patient_id]
        counts = patient_df["texture_category"].value_counts()
        dominant = counts.idxmax() if not counts.empty else None

        summary_rows.append(
            {
                "patient_id": patient_id,
                "num_texture_annotations": int(len(patient_df)),
                "ground_glass_count": int(counts.get("ground-glass", 0)),
                "part_solid_count": int(counts.get("part-solid", 0)),
                "solid_count": int(counts.get("solid", 0)),
                "dominant_texture_category": dominant,
            }
        )

    return pd.DataFrame(summary_rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract LIDC texture from XML for patient IDs in processed_lung_nodules.csv "
            "and map to ground-glass / part-solid / solid."
        )
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("processed_lung_nodules.csv"),
        help="CSV containing a patient_id column.",
    )
    parser.add_argument(
        "--lidc-root",
        type=Path,
        default=Path("code/data/LIDC-IDRI"),
        help="Root folder containing LIDC-IDRI-xxxx patient directories.",
    )
    parser.add_argument(
        "--out-details",
        type=Path,
        default=Path("code/src/data_analysis/output_lidc_csv/patient_texture_details.csv"),
        help="Output CSV with one row per texture annotation.",
    )
    parser.add_argument(
        "--out-summary",
        type=Path,
        default=Path("code/src/data_analysis/output_lidc_csv/patient_texture_summary.csv"),
        help="Output CSV with one row per patient.",
    )
    args = parser.parse_args()

    input_df = pd.read_csv(args.input_csv)
    if "patient_id" not in input_df.columns:
        raise ValueError(f"'patient_id' column not found in {args.input_csv}")

    patient_ids = (
        input_df["patient_id"]
        .dropna()
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .tolist()
    )

    detail_rows: list[dict] = []
    for patient_id in patient_ids:
        patient_dir = args.lidc_root / patient_id
        if not patient_dir.exists():
            continue

        for xml_path in patient_dir.rglob("*.xml"):
            detail_rows.extend(extract_texture_rows_from_xml(xml_path, patient_id))

    details_df = pd.DataFrame(
        detail_rows,
        columns=[
            "patient_id",
            "xml_path",
            "reading_session_index",
            "nodule_id",
            "texture",
            "texture_category",
        ],
    )

    summary_df = build_patient_summary(patient_ids, details_df)

    args.out_details.parent.mkdir(parents=True, exist_ok=True)
    args.out_summary.parent.mkdir(parents=True, exist_ok=True)
    details_df.to_csv(args.out_details, index=False)
    summary_df.to_csv(args.out_summary, index=False)

    print(f"Patients in input: {len(patient_ids)}")
    print(f"Texture annotations extracted: {len(details_df)}")
    print(f"Wrote details: {args.out_details}")
    print(f"Wrote summary: {args.out_summary}")


if __name__ == "__main__":
    main()
