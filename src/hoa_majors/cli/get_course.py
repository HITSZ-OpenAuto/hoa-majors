import argparse
import tomllib
from pathlib import Path


def get_course_info(plan_id: str, course_code: str, data_dir: Path):
    root = data_dir / "SCHOOL_MAJORS"
    found_plan = False
    found_course = False

    for f in root.rglob("*.toml"):
        try:
            with open(f, "rb") as fb:
                data = tomllib.load(fb)
            if data.get("info", {}).get("plan_ID") == plan_id:
                found_plan = True
                for course in data.get("courses", []):
                    if course.get("course_code") == course_code:
                        found_course = True
                        print(f"\nCourse Information for {course_code} in Plan {plan_id}:")
                        print("=" * 60)
                        # Print core fields
                        for key, value in course.items():
                            if key != "hours":
                                print(f"{key.replace('_', ' ').title():<25}: {value}")

                        # Print hours sub-table if it exists
                        if "hours" in course:
                            print("-" * 60)
                            print("Hours Breakdown:")
                            for h_key, h_val in course["hours"].items():
                                print(f"  {h_key.title():<23}: {h_val}")
                        print("=" * 60)
                        break
                if found_course:
                    break
        except Exception:
            continue

    if not found_plan:
        print(f"No training plan found with ID: {plan_id}")
    elif not found_course:
        print(f"Course {course_code} not found in plan {plan_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Get detailed information for a specific course in a plan."
    )
    parser.add_argument("plan_id", help="The Plan ID.")
    parser.add_argument("course_code", help="The Course Code.")
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="Directory where data is stored."
    )
    args = parser.parse_args()

    get_course_info(args.plan_id, args.course_code, args.data_dir)


if __name__ == "__main__":
    main()
