"""
Generate TOML metadata for all majors and sub-majors using HITsz JW data.

Features:
- Read major_mapping.json to determine FAH (plan_ID) for each major plan.
- Crawl course list for each FAH using HITsz JW API.
- Normalize course fields into readable English keys.
- Parse teaching hours into structured format.
- Write all courses under same FAH into a single TOML file.
- Auto-create directory structure:
    ./SCHOOL_MAJORS/{year}/本/MajorName[-Submajor].toml
"""

import json
from pathlib import Path

import requests
import toml

from config import COURSE_URL as JW_URL
from config import HEADERS_FORM as HEADERS
from config import PROXIES

# -------------------------------------------------------------------------------------------------
# 2. 字段英文映射
# -------------------------------------------------------------------------------------------------

FIELD_MAP = {
    "kcdm": "course_code",
    "xf": "credit",
    "khfsmc": "assessment_method",
    "kcmc": "course_name",
    "tjkkxnxq": "recommended_year_semester",
    "kzmc": "track",
    "kcxzmc": "course_nature",
    "kclbmc": "course_category",
    "kkyxmc": "offering_college",
}

# 学时字段
HOURS_MAP = {
    "zxs": ("xszxs", "total_hours"),
    "llxs": ("xsllxs", "theory"),
    "syxs": ("xssyxs", "lab"),
    "sjxs": ("2", "practice"),
    "xtxs": ("6", "exercise"),
    "sjxs2": ("8", "computer"),
    "fdxs": ("10", "tutoring"),
}


# -------------------------------------------------------------------------------------------------
# 3. 抓取课程数据
# -------------------------------------------------------------------------------------------------


def fetch_courses_by_fah(fah: str) -> list:
    """
    Crawl the JW API for a specific FAH (培养方案号).
    Return a list of raw course dicts.
    """
    payload = {
        "bglx": "",
        "multiple": "false",
        "sfcx": "",
        "pylx": "1",
        "pylb": "1",
        "fah": fah,
        "bgid": "",
        "kcmc": "",
        "yxdm": "",
        "xqdm": "",
        "kclbdm": "",
        "kcxzdm": "",
        "order1": "",
        "order2": "",
        "pageNum": 1,
        "pageSize": 999,
    }

    resp = requests.post(JW_URL, headers=HEADERS, data=payload, proxies=PROXIES)
    resp_json = resp.json()

    raw_list = resp_json.get("content", {}).get("list", [])
    clean_list = [{k: v for k, v in item.items() if v is not None} for item in raw_list]

    return clean_list


# -------------------------------------------------------------------------------------------------
# 4. 解析学时
# -------------------------------------------------------------------------------------------------


def parse_hours(raw_item: dict) -> dict:
    """
    Extract structured hours:
    - total_hours
    - [hours] table
    """
    result = {"hours": {}}

    # 总学时
    total_hours_key = HOURS_MAP["zxs"][0]
    if total_hours_key in raw_item:
        try:
            result["total_hours"] = int(raw_item[total_hours_key])
        except:
            result["total_hours"] = 0

    # 子学时
    xss = raw_item.get("xss", {})  # 可能不存在
    for code, (key, eng_name) in HOURS_MAP.items():
        if code == "zxs":
            continue

        # 直接字段 eg xssyxs
        if key in raw_item:
            try:
                result["hours"][eng_name] = int(raw_item[key])
            except:
                result["hours"][eng_name] = 0

        # xss dict eg {"2": "1周"}
        if isinstance(xss, dict) and key in xss:
            val = xss[key]
            if isinstance(val, str) and "周" in val:
                val = val.replace("周", "")
            try:
                result["hours"][eng_name] = int(val)
            except:
                pass

        # 默认填零
        if eng_name not in result["hours"]:
            result["hours"][eng_name] = 0

    return result


# -------------------------------------------------------------------------------------------------
# 5. 规范化单个课程
# -------------------------------------------------------------------------------------------------


def normalize_course(raw: dict) -> dict:
    """
    Convert raw JW item to normalized English-field dict.
    """
    course = {}

    # 基础字段
    for zh_key, en_key in FIELD_MAP.items():
        if zh_key in raw:
            course[en_key] = raw[zh_key]

    # 学时
    hours_block = parse_hours(raw)
    course.update(hours_block)

    return course


# -------------------------------------------------------------------------------------------------
# 6. 为一个 FAH 生成 TOML 内容
# -------------------------------------------------------------------------------------------------


def generate_toml_for_fah(fah: str, info: dict | None = None) -> dict:
    """
    Fetch, normalize, and return a TOML-ready dict:
    { "info": {...}, "courses": [ {...}, {...} ] }
    """
    raw_courses = fetch_courses_by_fah(fah)
    normalized = [normalize_course(item) for item in raw_courses]

    result = {}
    if info:
        result["info"] = info
    result["courses"] = normalized
    return result


# -------------------------------------------------------------------------------------------------
# 7. 目录创建与文件写入
# -------------------------------------------------------------------------------------------------


def ensure_dir(path: Path):
    """Create directory recursively."""
    path.mkdir(parents=True, exist_ok=True)


def write_toml(path: Path, data: dict):
    """Write TOML dict to file, ensuring info comes before courses."""
    with open(path, "w", encoding="utf-8") as f:
        # 先写 info 部分
        if "info" in data:
            f.write("[info]\n")
            for key, value in data["info"].items():
                if isinstance(value, str):
                    f.write(f'{key} = "{value}"\n')
                else:
                    f.write(f"{key} = {value}\n")
            f.write("\n")

        # 再写 courses 部分
        if "courses" in data:
            toml.dump({"courses": data["courses"]}, f)


# -------------------------------------------------------------------------------------------------
# 8. 主流程：生成所有目录与 TOML
# -------------------------------------------------------------------------------------------------


def main():
    # 打开 warning 文件
    warn_fp = open("warning.txt", "w", encoding="utf-8")

    def warning(msg: str):
        """同时输出到屏幕与 warning.txt"""
        print(msg)
        warn_fp.write(msg + "\n")

    # 加载 major_mapping.json
    with open("major_mapping.json", encoding="utf-8") as f:
        majors = json.load(f)

    root = Path("SCHOOL_MAJORS")

    for year, majors_dict in majors.items():
        # 创建目录 (固定为 "本")
        base_dir = root / year / "本"
        ensure_dir(base_dir)

        for major_code, major_info in majors_dict.items():
            major_name = major_info.get("name")
            fah = major_info.get("plan_ID")

            if not major_name:
                warning(f"⚠ 专业代码 {major_code} 无名称，跳过")
                continue

            # ------------------------------
            # 若大类有 FAH → 生成大类 TOML
            # ------------------------------
            if fah:
                try:
                    # 构建大类 info
                    major_info_block = {
                        "year": year,
                        "major_code": major_code,
                        "major_name": major_name,
                        "school_name": major_info.get("school_name", ""),
                        "plan_ID": fah,
                    }
                    major_toml_data = generate_toml_for_fah(fah, major_info_block)
                    write_toml(base_dir / f"{fah}.toml", major_toml_data)
                except Exception as e:
                    warning(f"⚠ 生成大类 {major_name} TOML 失败：{e}")
            else:
                warning(f"⚠ 大类无FAH，跳过大类 TOML：{year}-{major_name}-{major_code}")

            # ------------------------------
            # 子专业处理
            # ------------------------------
            sub_majors = major_info.get("majors", [])
            for sub in sub_majors:
                sub_code = sub.get("major_ID")
                sub_name = sub.get("name")
                sub_fah = sub.get("plan_ID")

                if not sub_name:
                    warning(f"⚠ 子专业无名称，跳过：{year}-{major_name}")
                    continue

                if not sub_fah:
                    warning(f"⚠ 跳过子专业（无FAH）：{year}-{major_name}-{sub_name}")
                    continue

                try:
                    # 构建子专业 info
                    sub_info_block = {
                        "year": year,
                        "parent_major_code": major_code,
                        "parent_major_name": major_name,
                        "major_code": sub_code,
                        "major_name": sub_name,
                        "school_name": major_info.get("school_name", ""),
                        "plan_ID": sub_fah,
                    }
                    sub_toml = generate_toml_for_fah(sub_fah, sub_info_block)
                    write_toml(
                        base_dir / f"{sub_fah}.toml",
                        sub_toml,
                    )
                except Exception as e:
                    warning(f"⚠ 生成子类 {sub_name} TOML 失败：{e}")

    warn_fp.close()
    print("✔ All TOML files generated successfully.")


# -------------------------------------------------------------------------------------------------
# Entry
# -------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
