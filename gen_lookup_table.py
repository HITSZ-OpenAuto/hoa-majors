import json
from pathlib import Path

import tomllib


def extract_course_codes():
    """从 SCHOOL_MAJORS_new 目录下的所有 toml 文件中提取 course_code"""
    course_codes = set()

    school_majors_path = Path("SCHOOL_MAJORS")

    # 遍历所有 toml 文件
    for toml_file in school_majors_path.rglob("*.toml"):
        try:
            with open(toml_file, "rb") as f:
                data = tomllib.load(f)

            # 提取所有课程的 course_code
            if "courses" in data:
                for course in data["courses"]:
                    if "course_code" in course:
                        course_codes.add(course["course_code"])
        except Exception as e:
            print(f"处理文件 {toml_file} 时出错: {e}")

    return course_codes


def main():
    # 提取所有 course_code
    course_codes = extract_course_codes()

    # 排序
    sorted_codes = sorted(course_codes)

    # 生成输出字典，格式参考 test_data.json
    output = {}
    for code in sorted_codes:
        output[code] = {"ID": code}

    # 保存到 JSON 文件
    output_file = "lookup_table_template.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"共提取 {len(sorted_codes)} 个唯一课程代码，已保存到 {output_file}")


if __name__ == "__main__":
    main()
