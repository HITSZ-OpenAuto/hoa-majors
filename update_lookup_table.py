"""
用于更新 lookup_table_template.py 的程序。
只添加新的课程代码，不覆盖已有的条目。
"""

from pathlib import Path

import tomllib

from lookup_table_template import LOOKUP_TABLE_TEMPLATE

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

    # 获取现有模板中已有的课程代码
    existing_courses = {course for course, _ in LOOKUP_TABLE_TEMPLATE.keys()}

    # 找出新增的课程代码
    new_courses = all_courses - existing_courses

    if not new_courses:
        print("没有新增的课程代码，无需更新。")
        return

    print(f"发现 {len(new_courses)} 个新课程代码：")
    for code in sorted(new_courses):
        print(f"  - {code}")

    # 复制现有模板并添加新条目
    updated_template: dict[tuple[str, str], str] = dict(LOOKUP_TABLE_TEMPLATE)

    for code in new_courses:
        # 新条目默认值为课程代码本身
        updated_template[(code, "")] = code

    # 按课程代码排序后生成 Python 代码
    sorted_items = sorted(updated_template.items(), key=lambda x: x[0][0])

    output_file = "lookup_table_template.py"
    lines = [HEADER_COMMENT + "LOOKUP_TABLE_TEMPLATE: dict[tuple[str, str], str] = {"]
    for (course, plan), repo_id in sorted_items:
        lines.append(f'    ("{course}", "{plan}"): "{repo_id}",')
    lines.append("}")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n已更新 {output_file}")
    print(
        f"原有 {len(existing_courses)} 条记录，新增 {len(new_courses)} 条，共 {len(updated_template)} 条"
    )


if __name__ == "__main__":
    main()
