from pathlib import Path

import tomllib

# 文件头部注释模板
HEADER_COMMENT = '''"""
课程代码查找表模板

数据结构:
    LOOKUP_TABLE_TEMPLATE: dict[tuple[str, str], str]
    
    键 (Key): tuple[str, str]
        - 第一个元素: 课程代码 (course_code)，如 "COMP1003"
        - 第二个元素: 培养方案号 (plan_id/fah)，用于区分不同专业的同名课程
          - 空字符串 "" 表示该课程在所有培养方案中通用
          - 非空字符串表示特定专业的培养方案号
    
    值 (Value): str
        - 对应的 OpenAuto 仓库 ID (repo_id)
        - 通常与课程代码相同，但部分课程可能有自定义映射

用途:
    将教务系统中的课程代码映射到 HITSZ-OpenAuto 仓库中的仓库 ID。
    同一课程代码在不同专业培养方案中可能对应不同的仓库。

示例:
    ("22MX44001", "F6FC6081F78A6454E0530C18F80AAFE6"): "22MX44001"
        - 课程代码 22MX44001 在培养方案 F6FC... 下对应仓库 22MX44001
    ("22MX44001", "ADAF2CFE5CC953A3E0530B18F80A5512"): "22MX44002"
        - 同一课程代码在另一培养方案下对应不同仓库 22MX44002
    ("COMP1003", ""): "COMP1003"
        - 通用课程，所有情况下都对应同一个仓库

维护说明:
    - 此文件由 gen_lookup_table.py 生成，由 update_lookup_table.py 更新
    - 注释部分在重新生成时会保留
"""

'''


def extract_courses():
    """从 SCHOOL_MAJORS 目录下的所有 toml 文件中提取所有不重复的课程代码"""
    all_courses = set()

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
                        all_courses.add(course["course_code"])

        except Exception as e:
            print(f"处理文件 {toml_file} 时出错: {e}")

    return all_courses


def main():
    # 提取所有不重复的课程代码
    all_courses = extract_courses()

    # 生成输出字典，格式为 {(course_code, ""): repo_id}
    # 键为元组 (课程代码, "")，值为仓库 ID（默认为课程代码本身）
    output: dict[tuple[str, str], str] = {}

    for code in sorted(all_courses):
        # 键为 (课程代码, "")，值默认为课程代码本身
        output[(code, "")] = code

    # 生成 Python 代码并保存到 .py 文件
    output_file = "lookup_table_template.py"
    lines = [HEADER_COMMENT + "LOOKUP_TABLE_TEMPLATE: dict[tuple[str, str], str] = {"]
    for (course, plan), repo_id in output.items():
        lines.append(f'    ("{course}", "{plan}"): "{repo_id}",')
    lines.append("}")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"共提取 {len(all_courses)} 条不重复的课程记录")
    print(f"已保存到 {output_file}")


if __name__ == "__main__":
    main()
