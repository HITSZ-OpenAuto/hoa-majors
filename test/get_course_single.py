"""
Generate TOML metadata for all majors and sub-majors using HITsz JW data.

Features:
- Read school_majors_with_fah.json to determine FAH for each major plan.
- Crawl course list for each FAH using HITsz JW API.
- Normalize course fields into readable English keys.
- Parse teaching hours into structured format.
- Write all courses under same FAH into a single TOML file.
- Auto-create directory structure:
    ./SCHOOL_MAJORS/{year}/{type}/MajorName[-Submajor].toml
"""

from pathlib import Path

import requests
import toml

# -------------------------------------------------------------------------------------------------
# 1. 教务系统请求配置（你可能需要替换 Cookie）
# -------------------------------------------------------------------------------------------------

JW_URL = "https://jw.hitsz.edu.cn/Njpyfakc/queryList?sf_request_type=ajax"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "_qimei_uuid42=196031207051009c516abefb4710507b8457eedf87; _qimei_i_3=76ed518a9c5902dd9797fc310e8c7ae1a6e6f1f8410f0282e2dd7b092794243d676433943c89e29e8295; _qimei_h38=; tenantId=default; _qimei_i_1=54c552e1c132; _qimei_fingerprint=1418c5a93b1a523ba3a18392c8f2792d; JSESSIONID=8D2426E67B659D49B1DC2413F130837E; route=35e0bb97cd8b3ec63836645aa32ed39c",
    "RoleCode": "01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

PROXIES = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}


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


def generate_toml_for_fah(fah: str) -> dict:
    """
    Fetch, normalize, and return a TOML-ready dict:
    { "courses": [ {...}, {...} ] }
    """
    raw_courses = fetch_courses_by_fah(fah)
    normalized = [normalize_course(item) for item in raw_courses]
    return {"courses": normalized}


# -------------------------------------------------------------------------------------------------
# 7. 目录创建与文件写入
# -------------------------------------------------------------------------------------------------


def ensure_dir(path: Path):
    """Create directory recursively."""
    path.mkdir(parents=True, exist_ok=True)


def write_toml(path: Path, data: dict):
    """Write TOML dict to file."""
    with open(path, "w", encoding="utf-8") as f:
        toml.dump(data, f)


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

    root = Path("SCHOOL_MAJORS_new")

    fah = "315E2D2561DB87FCE0630B18F80AD786"

    major_toml_data = generate_toml_for_fah(fah)
    write_toml(root / f"{fah}.toml", major_toml_data)

    warn_fp.close()
    print("✔ All TOML files generated successfully.")


# -------------------------------------------------------------------------------------------------
# Entry
# -------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
