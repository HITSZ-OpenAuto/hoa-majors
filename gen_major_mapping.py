"""
生成每个年级大类-专业的映射关系

流程：
1. 通过 getFah 接口获取所有培养方案，提取 {fah, zydm, zymc, njdm} 信息
2. 筛选出大类专业（通常是以 L 结尾或特定格式的专业代码）
3. 对于每个大类专业，调用 querydlzyd 接口查询其下的分流专业
4. 生成 年级 -> 大类 -> [专业列表] 的映射关系
"""

import json
import time

import requests

# 获取方案号所用 Headers
HEADERS_FORM = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "_qimei_uuid42=196031207051009c516abefb4710507b8457eedf87; _qimei_i_3=76ed518a9c5902dd9797fc310e8c7ae1a6e6f1f8410f0282e2dd7b092794243d676433943c89e29e8295; _qimei_h38=; tenantId=default; _qimei_i_1=54c552e1c132; _qimei_fingerprint=1418c5a93b1a523ba3a18392c8f2792d; route=35e0bb97cd8b3ec63836645aa32ed39c; JSESSIONID=C8E9345C924642480761F47FA6EBA66A",
    "RoleCode": "01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

# 获取大类专业列表所用 Headers
HEADERS_JSON = {
    "Content-Type": "application/json",
    "Cookie": "_qimei_uuid42=196031207051009c516abefb4710507b8457eedf87; _qimei_i_3=76ed518a9c5902dd9797fc310e8c7ae1a6e6f1f8410f0282e2dd7b092794243d676433943c89e29e8295; _qimei_h38=; tenantId=default; _qimei_i_1=54c552e1c132; _qimei_fingerprint=1418c5a93b1a523ba3a18392c8f2792d; route=35e0bb97cd8b3ec63836645aa32ed39c; JSESSIONID=C8E9345C924642480761F47FA6EBA66A",
    "RoleCode": "01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

PROXIES = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}

# API URLs
FAH_URL = "https://jw.hitsz.edu.cn/faxq/query?sf_request_type=ajax"
MAJOR_LIST_URL = "https://jw.hitsz.edu.cn/xjgl/dlfzysq/querydlzyd?sf_request_type=ajax"


def get_fah_list(njdm: str) -> list[dict]:
    """
    获取指定年级的培养方案列表

    Args:
        njdm: 年级代码，如 "2023"

    Returns:
        包含 {fah, zydm, zymc, yxmc} 的字典列表
    """
    data = {
        "sf_request_type": "ajax",
        "key": "",
        "xkdm": "",
        "yxdm": "",
        "zydm": "",
        "zyfxdm": "",
        "bbh": "",
        "ywdm": "",
        "falx": "3",
        "njdm": njdm,
        "cxby": "",
        "pylb": "1",
        "order1": "",
        "order2": "",
        "falxdm": "",  # 空着可获取更多专业
        "kzsjqx": "0",
        "py_xssfcxzj_zx": "1",
        "py_xssfcxzj_fx": "1",
        "sfdl": "",
        "pageNum": "1",
        "pageSize": "500",
    }

    resp = requests.post(FAH_URL, headers=HEADERS_FORM, data=data, proxies=PROXIES)
    resp_json = resp.json()

    raw_list = resp_json.get("content", {}).get("list", [])

    # 提取需要的字段
    result = []
    for item in raw_list:
        # 只保留主修方案（falxdm=1）
        if item.get("falxdm") != "1":
            continue

        result.append(
            {
                "fah": item.get("fah"),  # 方案号
                "zydm": item.get("zydm"),  # 专业代码
                "zymc": item.get("zymc"),  # 专业名称
                "yxmc": item.get("yxmc"),  # 院系名称
                # "yxdm": item.get("yxdm"),
                # "njdm": item.get("njdm"),
                # "famc": item.get("famc"),
            }
        )

    return result


def get_major_list_by_dalei(
    yzydm: str, xn: str = "2024-2025", xq: str = "2"
) -> list[dict]:
    """
    根据大类专业代码查询其下的分流专业列表

    Args:
        yzydm: 原专业代码（大类代码），如 "23L02"
        xn: 学年，如 "2024-2025"
        xq: 学期，如 "2"

    Returns:
        分流专业列表，每个元素包含 {ZYDM, XSZYDM, ZYMC} 等信息
    """
    data = {
        "kglx": "0",  # 开关类型
        "xn": xn,
        "xq": xq,
        "yzydm": yzydm,
    }

    try:
        resp = requests.post(
            MAJOR_LIST_URL, headers=HEADERS_JSON, json=data, proxies=PROXIES, timeout=10
        )
        resp_json = resp.json()

        # 过滤每个元素，只保留值不为 None 的字段
        result = []
        for item in resp_json:
            filtered_item = {k: v for k, v in item.items() if v is not None}
            result.append(filtered_item)

        return result
    except Exception as e:
        print(f"查询大类 {yzydm} 的专业列表失败: {e}")
        return []


def generate_major_mapping(grades: list[str] | None = None) -> dict:
    """
    生成年级-大类-专业的映射关系

    Args:
        grades: 要查询的年级列表，如 ["2023", "2024", "2025"]

    Returns:
        {
            "2023": {
                "23L09": {
                    "name": "化学",
                    "plan_ID": "036B010A7B622A58E0630C18F80A99CD",
                    "school_name": "理学院",
                    "majors": [
                        {
                        "name": "化学",
                        "major_ID": "080201",
                        "plan_ID": "398E8C14E5DB1A2EE0630B18F80A86E6"
                        }
                    ]
                },
                ...
            },
            ...
        }
    """
    if grades is None:
        grades = ["2025"]

    result = {}

    for grade in grades:
        print(f"\n========== 处理年级: {grade} ==========")
        result[grade] = {}

        # 获取该年级的培养方案
        fah_list = get_fah_list(grade)
        print(f"获取到 {len(fah_list)} 个培养方案")

        no_dalei_list = []

        while fah_list is not None and len(fah_list) != 0:
            print(
                f"当前培养方案数量: {len(fah_list)}, 无大类专业数量: {len(no_dalei_list)}"
            )
            fah_first = fah_list[0]
            print(f"正在处理培养方案: {fah_first['zydm']}")
            majors = get_major_list_by_dalei(fah_first["zydm"])
            time.sleep(0.3)  # 避免请求过快被封
            # 如果没有分流专业
            if len(majors) == 0:
                no_dalei_list.append(fah_first)
            else:
                result[grade][fah_first["zydm"]] = {
                    "name": fah_first["zymc"],
                    "plan_ID": fah_first["fah"],
                    "school_name": fah_first["yxmc"],
                    "majors": [],
                }
                for major in majors:
                    major_item = None
                    # 查找并移除匹配的 fah
                    matched_fah = next(
                        (fah for fah in fah_list if fah["zydm"] == major["ZYDM"]), None
                    )
                    if matched_fah is not None:
                        major_item = {
                            "name": major["ZYMC"],
                            "major_ID": major["ZYDM"],
                            "plan_ID": matched_fah["fah"],
                        }
                        fah_list.remove(matched_fah)
                    matched_fah = next(
                        (fah for fah in no_dalei_list if fah["zydm"] == major["ZYDM"]),
                        None,
                    )
                    if matched_fah is not None:
                        major_item = {
                            "name": major["ZYMC"],
                            "major_ID": major["ZYDM"],
                            "plan_ID": matched_fah["fah"],
                        }
                        no_dalei_list.remove(matched_fah)
                    if major_item is not None:
                        result[grade][fah_first["zydm"]]["majors"].append(major_item)
            fah_list = fah_list[1:]

        for no_dalei in no_dalei_list:
            result[grade][no_dalei["zydm"]] = {
                "name": no_dalei["zymc"],
                "plan_ID": no_dalei["fah"],
                "school_name": no_dalei["yxmc"],
                "majors": [],
            }

    return result


def save_mapping(mapping: dict, filename: str = "major_mapping.json"):
    """保存映射关系到 JSON 文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"\n映射关系已保存到 {filename}")


def print_mapping_summary(mapping: dict):
    """打印映射关系摘要"""
    print("\n" + "=" * 60)
    print("映射关系摘要")
    print("=" * 60)

    for grade, dalei_dict in mapping.items():
        print(f"\n【{grade}级】共 {len(dalei_dict)} 个大类")
        for major_ID, info in dalei_dict.items():
            major_count = len(info.get("majors", []))
            print(f"  [{major_ID}] {info['name']}: {major_count} 个专业")
            for major in info.get("majors", []):
                print(f"      - [{major.get('major_ID')}] {major.get('name')}")


if __name__ == "__main__":
    # 可以指定要查询的年级
    # grades = ["2023", "2024", "2025"]
    grades = ["2025"]  # 测试时先查一个年级
    # grades = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]

    # 生成映射关系
    mapping = generate_major_mapping(grades)

    # 打印摘要
    print_mapping_summary(mapping)

    # 保存到文件
    save_mapping(mapping, "major_mapping.json")
