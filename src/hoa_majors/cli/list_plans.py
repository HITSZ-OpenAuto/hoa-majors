import argparse
import tomllib
from pathlib import Path


def list_plans(data_dir: Path):
    root = data_dir / "SCHOOL_MAJORS"
    plans = {}

    for f in root.rglob("*.toml"):
        try:
            with open(f, "rb") as fb:
                data = tomllib.load(fb)
            info = data.get("info", {})
            plan_id = info.get("plan_ID")
            if plan_id:
                plans[plan_id] = {
                    "year": info.get("year", "N/A"),
                    "major_name": info.get("major_name", "N/A"),
                    "school": info.get("school_name", "N/A"),
                }
        except Exception as e:
            print(f"Error reading {f}: {e}")

    print(f"{'Plan ID':<35} | {'Year':<5} | {'Major Name'}")
    print("-" * 80)
    for pid, details in sorted(plans.items(), key=lambda x: (x[1]["year"], x[1]["major_name"])):
        print(f"{pid:<35} | {details['year']:<5} | {details['major_name']}")


def main():
    parser = argparse.ArgumentParser(description="List all training plans.")
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="Directory where data is stored."
    )
    args = parser.parse_args()

    list_plans(args.data_dir)


if __name__ == "__main__":
    main()
