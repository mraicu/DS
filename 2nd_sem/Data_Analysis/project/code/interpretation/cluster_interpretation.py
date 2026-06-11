import argparse

import pandas as pd

DEFAULT_CHEXPERT_DISEASE_COLS = [
    "Enlarged Cardiomediastinum",
    "Cardiomegaly",
    "Lung Opacity",
    "Lung Lesion",
    "Edema",
    "Consolidation",
    "Pneumonia",
    "Atelectasis",
    "Pneumothorax",
    "Pleural Effusion",
    "Pleural Other",
    "Support Devices",
]


def _validate_inputs(df: pd.DataFrame, disease_cols, cluster_col: str):
    if cluster_col not in df.columns:
        raise ValueError(f"'{cluster_col}' column is missing from dataframe.")

    missing = [col for col in disease_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing disease columns: {missing}")


def summarize_clusters(
    df: pd.DataFrame,
    disease_cols,
    cluster_col: str = "cluster",
    positive_threshold: float = 0.5,
    include_noise: bool = False,
):
    """
    Summarize disease prevalence inside each cluster.

    Returns one row per cluster-disease pair with:
    - cluster size
    - disease count inside the cluster
    - disease prevalence inside the cluster
    - global disease prevalence
    - lift = cluster prevalence / global prevalence
    """
    _validate_inputs(df, disease_cols, cluster_col)

    work = df.copy()
    if not include_noise:
        work = work[work[cluster_col] != -1].copy()

    if work.empty:
        return pd.DataFrame(
            columns=[
                cluster_col,
                "cluster_size",
                "disease",
                "disease_count",
                "cluster_prevalence",
                "global_prevalence",
                "lift",
            ]
        )

    binary = (work[disease_cols] >= positive_threshold).astype(int)
    cluster_sizes = work.groupby(cluster_col).size().rename("cluster_size")
    global_prevalence = binary.mean().rename("global_prevalence")

    rows = []
    for cluster_value, cluster_idx in work.groupby(cluster_col).groups.items():
        cluster_binary = binary.loc[cluster_idx]
        cluster_size = len(cluster_binary)
        disease_counts = cluster_binary.sum()
        cluster_prevalence = cluster_binary.mean()

        for disease in disease_cols:
            global_prev = float(global_prevalence[disease])
            cluster_prev = float(cluster_prevalence[disease])
            lift = cluster_prev / global_prev if global_prev > 0 else None
            rows.append(
                {
                    cluster_col: cluster_value,
                    "cluster_size": int(cluster_size),
                    "disease": disease,
                    "disease_count": int(disease_counts[disease]),
                    "cluster_prevalence": cluster_prev,
                    "global_prevalence": global_prev,
                    "lift": lift,
                }
            )

    summary = pd.DataFrame(rows)
    return summary.sort_values(
        by=[cluster_col, "cluster_prevalence", "disease_count"],
        ascending=[True, False, False],
    ).reset_index(drop=True)


def find_disease_clusters(
    df: pd.DataFrame,
    disease_cols,
    disease_name: str,
    cluster_col: str = "cluster",
    positive_threshold: float = 0.5,
    include_noise: bool = False,
):
    """
    For one disease, show which clusters contain it and how concentrated it is.

    Returns one row per cluster with:
    - cluster size
    - number of positive cases of the disease
    - prevalence of the disease inside the cluster
    - share of all disease cases captured by that cluster
    - lift versus global disease prevalence
    """
    _validate_inputs(df, disease_cols, cluster_col)

    if disease_name not in disease_cols:
        raise ValueError(
            f"'{disease_name}' is not in disease_cols. Available: {list(disease_cols)}"
        )

    work = df.copy()
    if not include_noise:
        work = work[work[cluster_col] != -1].copy()

    disease_positive = (work[disease_name] >= positive_threshold).astype(int)
    total_positive = int(disease_positive.sum())
    global_prevalence = float(disease_positive.mean()) if len(work) else 0.0

    rows = []
    for cluster_value, cluster_df in work.groupby(cluster_col):
        cluster_positive = int((cluster_df[disease_name] >= positive_threshold).sum())
        cluster_size = int(len(cluster_df))
        cluster_prevalence = cluster_positive / cluster_size if cluster_size else 0.0
        share_of_disease_cases = (
            cluster_positive / total_positive if total_positive > 0 else 0.0
        )
        lift = (
            cluster_prevalence / global_prevalence if global_prevalence > 0 else None
        )

        rows.append(
            {
                cluster_col: cluster_value,
                "cluster_size": cluster_size,
                "disease": disease_name,
                "positive_cases": cluster_positive,
                "cluster_prevalence": cluster_prevalence,
                "share_of_disease_cases": share_of_disease_cases,
                "global_prevalence": global_prevalence,
                "lift": lift,
            }
        )

    result = pd.DataFrame(rows)
    return result.sort_values(
        by=["cluster_prevalence", "positive_cases"],
        ascending=[False, False],
    ).reset_index(drop=True)


def top_diseases_per_cluster(
    df: pd.DataFrame,
    disease_cols,
    top_n: int = 5,
    cluster_col: str = "cluster",
    positive_threshold: float = 0.5,
    include_noise: bool = False,
    sort_by: str = "lift",
):
    """
    Return the most characteristic diseases for each cluster.

    sort_by:
    - 'lift' highlights diseases overrepresented in the cluster
    - 'cluster_prevalence' highlights the most common diseases in the cluster
    """
    summary = summarize_clusters(
        df=df,
        disease_cols=disease_cols,
        cluster_col=cluster_col,
        positive_threshold=positive_threshold,
        include_noise=include_noise,
    )

    if sort_by not in {"lift", "cluster_prevalence"}:
        raise ValueError("sort_by must be 'lift' or 'cluster_prevalence'.")

    ranked = summary.sort_values(
        by=[cluster_col, sort_by, "disease_count"],
        ascending=[True, False, False],
    )

    return (
        ranked.groupby(cluster_col, group_keys=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def cluster_disease_matrix(
    df: pd.DataFrame,
    disease_cols,
    cluster_col: str = "cluster",
    positive_threshold: float = 0.5,
    include_noise: bool = False,
    value: str = "cluster_prevalence",
):
    """
    Build a matrix for interpretation or heatmaps.

    value:
    - 'cluster_prevalence'
    - 'lift'
    - 'disease_count'
    """
    summary = summarize_clusters(
        df=df,
        disease_cols=disease_cols,
        cluster_col=cluster_col,
        positive_threshold=positive_threshold,
        include_noise=include_noise,
    )

    if value not in {"cluster_prevalence", "lift", "disease_count"}:
        raise ValueError(
            "value must be 'cluster_prevalence', 'lift', or 'disease_count'."
        )

    return summary.pivot(
        index=cluster_col,
        columns="disease",
        values=value,
    )


def _parse_disease_cols(disease_cols_arg, csv_columns, cluster_col):
    if disease_cols_arg:
        disease_cols = [col.strip() for col in disease_cols_arg if col.strip()]
    else:
        if all(col in csv_columns for col in DEFAULT_CHEXPERT_DISEASE_COLS):
            disease_cols = DEFAULT_CHEXPERT_DISEASE_COLS
        else:
            disease_cols = [
                col
                for col in csv_columns
                if col != cluster_col
                and col != "Age"
                and not col.startswith("img_feat_")
                and not col.startswith("Sex_")
            ]

    return disease_cols


def build_parser():
    parser = argparse.ArgumentParser(
        description="Interpret disease clusters from a clustered CSV."
    )
    parser.add_argument(
        "--csv",
        default="spectral_clustered_d2.csv",
        help=(
            "Path to a CSV file that contains a cluster column. "
            "Default: best_clustered_df.csv"
        ),
    )
    parser.add_argument(
        "--cluster-col",
        default="cluster",
        help="Name of the cluster column. Default: cluster",
    )
    parser.add_argument(
        "--disease-cols",
        nargs="+",
        help=(
            "Disease columns to analyze. If omitted, the script infers all non-image "
            "columns except the cluster column."
        ),
    )
    parser.add_argument(
        "--disease",
        help="Specific disease to query. Required for mode=disease.",
    )
    parser.add_argument(
        "--mode",
        choices=["disease", "top", "matrix", "summary"],
        default="top",
        help="Which output to print. Default: top",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of diseases per cluster for mode=top. Default: 5",
    )
    parser.add_argument(
        "--sort-by",
        choices=["lift", "cluster_prevalence"],
        default="lift",
        help="Ranking metric for mode=top. Default: lift",
    )
    parser.add_argument(
        "--matrix-value",
        choices=["cluster_prevalence", "lift", "disease_count"],
        default="cluster_prevalence",
        help="Matrix values for mode=matrix. Default: cluster_prevalence",
    )
    parser.add_argument(
        "--positive-threshold",
        type=float,
        default=0.5,
        help="Threshold used to mark a disease as present. Default: 0.5",
    )
    parser.add_argument(
        "--include-noise",
        action="store_true",
        help="Include HDBSCAN noise points where cluster = -1.",
    )
    parser.add_argument(
        "--round",
        dest="round_digits",
        type=int,
        default=4,
        help="Decimal places for printed numeric output. Default: 4",
    )
    parser.add_argument(
        "--output",
        help="Optional path to save the result as CSV.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    df = pd.read_csv(args.csv)

    if args.cluster_col not in df.columns:
        raw_nih_hint = "Finding Labels" in df.columns and "Image Index" in df.columns
        message = (
            f"'{args.cluster_col}' column is missing from '{args.csv}'. "
            "This script expects a clustered CSV produced after running your clustering step."
        )
        if raw_nih_hint:
            message += (
                " The current default file looks like the raw NIH metadata file, not the "
                "clustered output. Save `best_clustered_df` (or another clustered dataframe) "
                "to CSV and use that file instead."
            )
        raise ValueError(message)

    disease_cols = _parse_disease_cols(args.disease_cols, df.columns, args.cluster_col)

    if args.mode == "disease":
        if not args.disease:
            parser.error("--disease is required when --mode disease is used.")
        result = find_disease_clusters(
            df=df,
            disease_cols=disease_cols,
            disease_name=args.disease,
            cluster_col=args.cluster_col,
            positive_threshold=args.positive_threshold,
            include_noise=args.include_noise,
        )
    elif args.mode == "top":
        result = top_diseases_per_cluster(
            df=df,
            disease_cols=disease_cols,
            top_n=args.top_n,
            cluster_col=args.cluster_col,
            positive_threshold=args.positive_threshold,
            include_noise=args.include_noise,
            sort_by=args.sort_by,
        )
    elif args.mode == "matrix":
        result = cluster_disease_matrix(
            df=df,
            disease_cols=disease_cols,
            cluster_col=args.cluster_col,
            positive_threshold=args.positive_threshold,
            include_noise=args.include_noise,
            value=args.matrix_value,
        )
    else:
        result = summarize_clusters(
            df=df,
            disease_cols=disease_cols,
            cluster_col=args.cluster_col,
            positive_threshold=args.positive_threshold,
            include_noise=args.include_noise,
        )

    print(result.round(args.round_digits).to_string())

    if args.output:
        result.to_csv(args.output, index=True if args.mode == "matrix" else False)


if __name__ == "__main__":
    main()
