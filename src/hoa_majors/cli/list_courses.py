import argparse
import tomllib
from pathlib import Path


def list_courses(plan_id: str, data_dir: Path):
    root = data_dir / "SCHOOL_MAJORS"
    found = False

    for f in root.rglob("*.toml"):
        try:
            with open(f, "rb") as fb:
                data = tomllib.load(fb)
            if data.get("info", {}).get("plan_ID") == plan_id:
                found = True
                print(f"Plan: {data['info'].get('major_name')} ({data['info'].get('year')})")
                print(f"{'Course Code':<12} | {'Course Name'}")
                print("-" * 50)
                for course in data.get("courses", []):
                    code = course.get("course_code", "N/A")
                    name = course.get("course_name", "N/A")
                    print(f"{code:<12} | {name}")
                break
        except Exception:
            continue

    if not found:
        print(f"No training plan found with ID: {plan_id}")


def main():
    parser = argparse.ArgumentParser(description="List all courses for a specific training plan.")
    parser.add_argument("plan_id", help="The Plan ID to query.")
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="Directory where data is stored."
    )
    args = parser.parse_args()

    list_courses(args.plan_id, args.data_dir)


if __name__ == "__main__":
    main()
