
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# --------------------------------------------------
# 1. PROJECT PATHS AND SETTINGS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"/"video_out"

REQUIRED_COLUMNS = [
    "timestamp_seconds",
    "face_detected",
    "pose_detected",
    "hand_count",
]

NUMERIC_COLUMNS = [
    "timestamp_seconds",
    "top_blendshape_score",
    "shoulder_tilt_normalized",
    "torso_offset_normalized",
    "hand_count",
    "left_wrist_x",
    "left_wrist_y",
    "right_wrist_x",
    "right_wrist_y",
]

# Provisional review threshold for unusually large wrist movements.
# This is a heuristic, not a scientifically validated error boundary.
WRIST_JUMP_THRESHOLD = 0.25
MAX_CONSECUTIVE_GAP_SECONDS = 0.5


# --------------------------------------------------
# 2. FIND THE LATEST ORIGINAL RECORDING
# --------------------------------------------------

def find_latest_csv():
    """Find the newest original recording, excluding generated CSVs."""

    files = [
        path
        for path in OUTPUT_DIR.glob("presentation_metrics_*.csv")
        if not path.stem.endswith("_cleaned")
    ]

    if not files:
        return None

    return max(files, key=lambda path: path.stat().st_mtime)


# --------------------------------------------------
# 3. LOAD AND VALIDATE DATA
# --------------------------------------------------

def load_data(csv_path):
    df = pd.read_csv(csv_path)

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("The CSV file has no data rows.")

    # Convert measurement columns to numeric values.
    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    # Convert detection columns to Boolean values.
    for column in ["face_detected", "pose_detected"]:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({
                "true": True,
                "false": False,
                "1": True,
                "0": False,
            })
        )

    original_rows = len(df)

    # Remove rows without valid timestamps.
    df = df.dropna(
        subset=["timestamp_seconds"]
    ).copy()

    removed_rows = original_rows - len(df)

    # Sort chronologically.
    df = df.sort_values(
        "timestamp_seconds"
    ).reset_index(drop=True)

    if df.empty:
        raise ValueError(
            "No rows remain after timestamp validation."
        )

    # Duplicate timestamps can make consecutive movement ambiguous.
    if df["timestamp_seconds"].duplicated().any():
        raise ValueError(
            "Duplicate timestamps detected. "
            "Please inspect the original recording CSV."
        )

    # Elapsed time starts at zero.
    df["elapsed_seconds"] = (
        df["timestamp_seconds"]
        - df["timestamp_seconds"].iloc[0]
    )

    return df, removed_rows


# --------------------------------------------------
# 4. CALCULATE MOVEMENT METRICS
# --------------------------------------------------

def add_movement_metrics(df):
    df = df.copy()

    for side in ["left", "right"]:
        x_col = f"{side}_wrist_x"
        y_col = f"{side}_wrist_y"

        movement_col = f"{side}_wrist_displacement"
        flag_col = f"{side}_wrist_jump_flag"

        # Handle files without wrist-coordinate columns.
        if x_col not in df.columns or y_col not in df.columns:
            df[movement_col] = np.nan
            df[flag_col] = False
            continue

        valid = (
            df[x_col].notna()
            & df[y_col].notna()
            & df[x_col].between(0, 1)
            & df[y_col].between(0, 1)
        )

        x = df[x_col].where(valid)
        y = df[y_col].where(valid)

        dx = x.diff()
        dy = y.diff()

        dt = df["timestamp_seconds"].diff()

        displacement = np.sqrt(
            dx.pow(2) + dy.pow(2)
        )

        # Only compare consecutive valid samples separated by
        # a positive time interval no greater than 0.5 seconds.
        usable = (
            valid
            & valid.shift(1, fill_value=False)
            & dt.gt(0)
            & dt.le(MAX_CONSECUTIVE_GAP_SECONDS)
        )

        df[movement_col] = displacement.where(usable)

        # Flag, but do not automatically remove, large movements.
        df[flag_col] = (
            df[movement_col] > WRIST_JUMP_THRESHOLD
        ).fillna(False)

    # Calculate frame-to-frame changes in posture measurements.
    for column in [
        "shoulder_tilt_normalized",
        "torso_offset_normalized",
    ]:
        if column in df.columns:
            df[f"{column}_change"] = (
                df[column].diff().abs()
            )

    return df


# --------------------------------------------------
# 5. SUMMARY STATISTICS
# --------------------------------------------------

def detection_percentage(series):
    valid = series.dropna()

    if valid.empty:
        return None

    return 100 * valid.astype(bool).mean()


def format_percentage(value):
    if value is None:
        return "Unavailable"

    return f"{value:.2f}%"


def describe_measurement(df, column, label):
    if column not in df.columns:
        return [f"{label}: column unavailable"]

    values = df[column].dropna()

    if values.empty:
        return [f"{label}: no valid measurements"]

    lines = [
        f"{label}:",
        f"  Valid samples: {len(values)}",
        f"  Mean: {values.mean():.5f}",
        f"  Median: {values.median():.5f}",
    ]

    if len(values) > 1:
        lines.append(
            f"  Standard deviation: {values.std():.5f}"
        )
    else:
        lines.append(
            "  Standard deviation: unavailable (one sample)"
        )

    lines.extend([
        f"  Minimum: {values.min():.5f}",
        f"  Maximum: {values.max():.5f}",
    ])

    return lines


def create_summary(df, csv_path, removed_rows):
    row_count = len(df)

    if row_count > 1:
        duration = (
            df["timestamp_seconds"].iloc[-1]
            - df["timestamp_seconds"].iloc[0]
        )
    else:
        duration = 0.0

    face_pct = detection_percentage(
        df["face_detected"]
    )

    pose_pct = detection_percentage(
        df["pose_detected"]
    )

    hand_values = df["hand_count"].dropna()

    if hand_values.empty:
        average_hands = None
        max_hands = None
    else:
        average_hands = hand_values.mean()
        max_hands = int(hand_values.max())

    lines = [
        "PRESENTATION VIDEO MOVEMENT ANALYSIS",
        "=" * 42,
        "",
        f"Input file: {csv_path.name}",
        f"Rows analyzed: {row_count}",
        f"Rows removed for invalid timestamps: {removed_rows}",
        f"Recorded duration: {duration:.2f} seconds",
        "",
        "DETECTION COVERAGE",
        "-" * 25,
        f"Face detected: {format_percentage(face_pct)}",
        f"Body pose detected: {format_percentage(pose_pct)}",
    ]

    if average_hands is not None:
        lines.extend([
            f"Average detected hands per frame: {average_hands:.2f}",
            f"Maximum detected hands in a frame: {max_hands}",
        ])
    else:
        lines.append("Hand count: no valid measurements")

    lines.extend([
        "",
        "MOVEMENT MEASUREMENTS",
        "-" * 25,
    ])

    lines.extend(
        describe_measurement(
            df,
            "shoulder_tilt_normalized",
            "Shoulder vertical difference (normalized)",
        )
    )

    lines.extend(
        describe_measurement(
            df,
            "torso_offset_normalized",
            "Torso horizontal offset (normalized)",
        )
    )

    for side in ["left", "right"]:
        lines.extend(
            describe_measurement(
                df,
                f"{side}_wrist_displacement",
                f"{side.capitalize()} wrist frame-to-frame displacement",
            )
        )

    # Report the most frequent top-ranked blendshape.
    if "top_blendshape" in df.columns:
        categories = (
            df["top_blendshape"]
            .dropna()
            .astype(str)
            .replace("", np.nan)
            .dropna()
        )

        if not categories.empty:
            counts = categories.value_counts()

            lines.extend([
                "",
                "MOST FREQUENT TOP BLENDSHAPE",
                "-" * 25,
                f"Category: {counts.index[0]}",
                f"Rows in which it ranked first: {counts.iloc[0]}",
            ])

    # Report samples that need manual review.
    lines.extend([
        "",
        "MOVEMENT DATA QUALITY",
        "-" * 25,
    ])

    for side in ["left", "right"]:
        movement_col = f"{side}_wrist_displacement"
        flag_col = f"{side}_wrist_jump_flag"

        if movement_col not in df.columns:
            continue

        valid_count = int(
            df[movement_col].notna().sum()
        )

        flagged_count = int(
            df[flag_col].sum()
        )

        if valid_count > 0:
            flagged_pct = (
                100 * flagged_count / valid_count
            )
        else:
            flagged_pct = 0.0

        lines.extend([
            f"{side.capitalize()} wrist valid movement samples: "
            f"{valid_count}",
            f"  Large-jump flags: {flagged_count}",
            f"  Flagged percentage: {flagged_pct:.2f}%",
        ])

    lines.extend([
        "",
        "DATA QUALITY NOTES",
        "-" * 25,
        "Detection percentages describe model availability, not performance.",
        "Wrist displacement is normalized image-coordinate change per",
        "consecutive valid sample, not physical distance.",
        f"Large-jump review threshold: {WRIST_JUMP_THRESHOLD:.2f}.",
        "Flags identify samples for inspection; they do not prove errors.",
        "Shoulder and torso statistics describe observed geometry,",
        "not presentation quality or confidence.",
        "This session is exploratory and is not a validated assessment.",
    ])

    return "\n".join(lines)


# --------------------------------------------------
# 6. CREATE CHARTS
# --------------------------------------------------

def save_charts(df, output_dir, session_name):
    chart_path = (
        output_dir / f"{session_name}_analysis.png"
    )

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(11, 12),
    )

    time_values = df["elapsed_seconds"]

    # Chart 1: detection availability.
    axes[0].plot(
        time_values,
        df["face_detected"].astype(float),
        label="Face detected",
    )

    axes[0].plot(
        time_values,
        df["pose_detected"].astype(float),
        label="Pose detected",
    )

    axes[0].set_ylim(-0.1, 1.1)
    axes[0].set_ylabel("Detection (0 or 1)")
    axes[0].set_title(
        "Detection Availability Over Time"
    )
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Chart 2: posture-related geometry.
    posture_columns = [
        "shoulder_tilt_normalized",
        "torso_offset_normalized",
    ]

    for column in posture_columns:
        if column in df.columns:
            axes[1].plot(
                time_values,
                df[column],
                label=column.replace(
                    "_normalized", ""
                ),
            )

    axes[1].set_ylabel(
        "Normalized image coordinate"
    )
    axes[1].set_title(
        "Shoulder and Torso Measurements"
    )
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Chart 3: wrist movement, with flagged samples highlighted.
    for side in ["left", "right"]:
        movement_col = f"{side}_wrist_displacement"
        flag_col = f"{side}_wrist_jump_flag"

        if movement_col not in df.columns:
            continue

        axes[2].plot(
            time_values,
            df[movement_col],
            label=f"{side.capitalize()} wrist",
            alpha=0.8,
        )

        flagged = df[flag_col]

        if flagged.any():
            axes[2].scatter(
                time_values[flagged],
                df.loc[flagged, movement_col],
                label=f"{side.capitalize()} wrist: review",
                marker="x",
                s=35,
            )

    axes[2].axhline(
        WRIST_JUMP_THRESHOLD,
        linestyle="--",
        label="Review threshold",
    )

    axes[2].set_xlabel(
        "Elapsed time (seconds)"
    )
    axes[2].set_ylabel(
        "Normalized displacement"
    )
    axes[2].set_title(
        "Frame-to-Frame Wrist Movement"
    )
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)

    return chart_path


# --------------------------------------------------
# 7. MAIN
# --------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = find_latest_csv()

    if csv_path is None:
        print(
            "No original presentation_metrics CSV file was found."
        )
        print(f"Expected folder: {OUTPUT_DIR}")
        print(
            "Run combined_pipeline.py first to create a recording."
        )
        sys.exit(1)

    print(f"Analyzing original recording: {csv_path.name}")

    try:
        df, removed_rows = load_data(csv_path)

        df = add_movement_metrics(df)

        if df.empty:
            raise ValueError(
                "No rows remain after timestamp validation."
            )

        session_name = csv_path.stem

        cleaned_path = (
            OUTPUT_DIR
            / f"{session_name}_cleaned.csv"
        )

        report_path = (
            OUTPUT_DIR
            / f"{session_name}_summary.txt"
        )

        df.to_csv(
            cleaned_path,
            index=False,
        )

        summary = create_summary(
            df,
            csv_path,
            removed_rows,
        )

        report_path.write_text(
            summary,
            encoding="utf-8",
        )

        chart_path = save_charts(
            df,
            OUTPUT_DIR,
            session_name,
        )

        print("\n" + summary)

        print("\nOUTPUT FILES")
        print("-" * 25)
        print(f"Cleaned measurements: {cleaned_path}")
        print(f"Summary report:       {report_path}")
        print(f"Charts:               {chart_path}")

    except (ValueError, OSError, pd.errors.ParserError) as error:
        print(f"Analysis failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
