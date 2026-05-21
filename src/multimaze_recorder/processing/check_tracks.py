"""Check tracking completeness and rename *_Checked folders to *_Tracked."""

from pathlib import Path
import argparse
import os


def check_and_rename(data_folder: Path) -> None:
    for experiment in data_folder.iterdir():
        if experiment.is_dir() and ("_Checked" in experiment.name or "_Tracked" in experiment.name):
            all_corridors_tracked = True
            for arena in experiment.iterdir():
                if arena.is_dir():
                    for corridor in arena.iterdir():
                        if corridor.is_dir():
                            slp_files_ball = list(corridor.glob("*_tracked_ball.slp"))
                            h5_files_ball = list(corridor.glob("*_tracked_ball*.h5"))
                            slp_files_fly = list(corridor.glob("*_tracked_fly.slp"))
                            h5_files_fly = list(corridor.glob("*_tracked_fly*.h5"))
                            if not (slp_files_ball and h5_files_ball and slp_files_fly and h5_files_fly):
                                all_corridors_tracked = False
                                print(
                                    f"Corridor {corridor.name} of arena {arena.name} in "
                                    f"experiment {experiment.name} is missing tracking files."
                                )
                                break
                    if not all_corridors_tracked:
                        break
            if all_corridors_tracked:
                if "_Checked" in experiment.name:
                    print(f"Experiment {experiment.name} is fully processed. Renaming...")
                    new_name = experiment.name.replace("_Checked", "_Tracked")
                    experiment.rename(data_folder / new_name)
                elif "_Tracked" in experiment.name:
                    print(f"Experiment {experiment.name} is fully processed.")


def main():
    parser = argparse.ArgumentParser(
        description="Check tracking files and rename *_Checked → *_Tracked when complete"
    )
    parser.add_argument(
        "--data-folder", "-d",
        default=os.environ.get("MMRECORDER_LOCAL_PATH", str(Path.home() / "Videos")),
        help="Root folder containing experiment directories",
    )
    args = parser.parse_args()
    check_and_rename(Path(args.data_folder))


if __name__ == "__main__":
    main()
