import sys
import subprocess
import time
from pathlib import Path


# ============================================================
# PROJECT PATHS
# This file is located in: src/video/run_all_analysis.py
# ============================================================

VIDEO_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = VIDEO_DIR.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "video_out"


# ============================================================
# ANALYSIS PIPELINE
# Scripts run in the order listed below.
# ============================================================

PIPELINE_STEPS = [
    {
        "name": "Detailed visual-analysis JSON",
        "script": "analyze_video_json.py",
        "video_argument": True,
    },
    {
        "name": "Export CSV metrics from visual-analysis JSON",
        "script": "export_metrics_from_json.py",
        "video_argument": False,
    },
    {
        "name": "Session summary, cleaned CSV, and charts",
        "script": "analyze_session.py",
        "video_argument": False,
    },
    {
        "name": "Candidate blink detection",
        "script": "detect_blinks.py",
        "video_argument": False,
    },
    {
        "name": "Facial-signal report",
        "script": "analyze_facial_signals.py",
        "video_argument": False,
    },
    {
        "name": "Blink-review contact sheet",
        "script": "create_blink_review_sheet.py",
        "video_argument": False,
    },
]


# ============================================================
# STORE EXECUTION TIMES
# ============================================================

STEP_TIMINGS = []


# ============================================================
# RUN ONE ANALYSIS STEP
# ============================================================

def run_step(step, video_path, step_number, total_steps):

    script_path = VIDEO_DIR / step["script"]

    print("\n" + "=" * 70)
    print(f"STEP {step_number}/{total_steps}: {step['name']}")
    print("=" * 70)

    # Check that the script exists.
    if not script_path.is_file():
        print(f"ERROR: Script not found:\n{script_path}")
        return False

    # Use the Python interpreter from the active environment.
    command = [sys.executable, str(script_path)]

    # Pass the video path only to scripts configured to accept it.
    if step["video_argument"]:
        command.append(str(video_path))

    print(f"Script: {script_path.name}")
    print(f"Python: {sys.executable}")
    print("-" * 70)

    # Start measuring execution time.
    step_start_time = time.perf_counter()

    try:
        result = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            check=False,
        )

    except KeyboardInterrupt:
        elapsed = time.perf_counter() - step_start_time

        print("\nPipeline interrupted by user.")
        print(f"Time elapsed in current step: {elapsed:.2f} seconds")

        return False

    except OSError as error:
        elapsed = time.perf_counter() - step_start_time

        print(f"\nERROR: Could not start {script_path.name}")
        print(error)
        print(f"Time elapsed: {elapsed:.2f} seconds")

        return False

    # Calculate elapsed time after the script finishes.
    step_elapsed = time.perf_counter() - step_start_time

    # Store timing information.
    STEP_TIMINGS.append({
        "name": step["name"],
        "script": script_path.name,
        "seconds": step_elapsed,
        "success": result.returncode == 0,
    })

    print("\n" + "-" * 70)
    print(f"Execution time: {step_elapsed:.2f} seconds")

    # Stop the pipeline if a script fails.
    if result.returncode != 0:
        print(f"\nFAILED: {script_path.name}")
        print(f"Exit code: {result.returncode}")
        print("The remaining steps will not run.")

        return False

    print(f"COMPLETED: {step['name']}")

    return True


# ============================================================
# DISPLAY EXECUTION-TIME SUMMARY
# ============================================================

def display_timing_summary(total_elapsed):

    print("\n")
    print("=" * 80)
    print("VIDEO ANALYSIS - EXECUTION TIME SUMMARY")
    print("=" * 80)

    print(f"{'SCRIPT':<34} {'STATUS':<12} {'TIME (SECONDS)':>16}")
    print("-" * 80)

    for item in STEP_TIMINGS:
        status = "SUCCESS" if item["success"] else "FAILED"

        print(
            f"{item['script']:<34} "
            f"{status:<12} "
            f"{item['seconds']:>16.2f}"
        )

    print("-" * 80)
    print(f"{'TOTAL VIDEO PIPELINE TIME':<46}{total_elapsed:>16.2f}")

    print(f"\nTotal time in minutes: {total_elapsed / 60:.2f}")

    if STEP_TIMINGS:
        slowest_step = max(
            STEP_TIMINGS,
            key=lambda item: item["seconds"],
        )

        print("\nSLOWEST STEP")
        print(f"Script : {slowest_step['script']}")
        print(f"Task   : {slowest_step['name']}")
        print(f"Time   : {slowest_step['seconds']:.2f} seconds")

    print("=" * 80)


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    # Require one input video path.
    if len(sys.argv) != 2:
        print("\nUsage:")
        print(
            'python src\\video\\run_all_analysis.py '
            '"data\\raw\\presentation.mp4"'
        )
        print("\nReplace the example path with your actual video path.")
        sys.exit(1)

    # Resolve the input video path.
    video_path = Path(sys.argv[1])

    if not video_path.is_absolute():
        video_path = PROJECT_ROOT / video_path

    video_path = video_path.resolve()

    # Validate the input video.
    if not video_path.is_file():
        print("\nERROR: Input video not found:")
        print(video_path)
        sys.exit(1)

    # Create the main output directory if necessary.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Display pipeline information.
    print("\n" + "=" * 70)
    print("ASTRA HUNTERS - COMPLETE VIDEO ANALYSIS PIPELINE")
    print("=" * 70)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Video folder : {VIDEO_DIR}")
    print(f"Input video  : {video_path}")
    print(f"Output folder: {OUTPUT_DIR}")
    print(f"Total steps  : {len(PIPELINE_STEPS)}")

    # Start measuring the complete video pipeline.
    pipeline_start_time = time.perf_counter()

    # Run every analysis step in order.
    for index, step in enumerate(PIPELINE_STEPS, start=1):

        success = run_step(
            step=step,
            video_path=video_path,
            step_number=index,
            total_steps=len(PIPELINE_STEPS),
        )

        if not success:
            total_elapsed = time.perf_counter() - pipeline_start_time

            print("\n" + "=" * 70)
            print("PIPELINE STOPPED")
            print("Fix the error above and run the pipeline again.")
            print("=" * 70)

            display_timing_summary(total_elapsed)
            sys.exit(1)

    # All analysis steps completed successfully.
    total_elapsed = time.perf_counter() - pipeline_start_time

    print("\n" + "=" * 70)
    print("ALL ANALYSIS STEPS COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print(f"Input video: {video_path}")
    print(f"Output directory: {OUTPUT_DIR}")

    print("\nFiles and folders currently in the main output directory:")

    for path in sorted(OUTPUT_DIR.iterdir()):
        item_type = "DIR " if path.is_dir() else "FILE"
        print(f"  [{item_type}] {path.name}")

    # Display individual and total execution times.
    display_timing_summary(total_elapsed)

    print("\nPipeline finished.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()