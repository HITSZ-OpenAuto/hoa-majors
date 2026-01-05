# hoa-majors

## 项目简介

本项目用于从 **哈尔滨工业大学（深圳）教务系统** 抓取各年级、各专业的培养方案课程数据，并将其规范化后保存为 TOML 格式文件，便于后续查询与分析。

---

## 目录结构

```text
├── get_courses.py          # 抓取课程数据并生成 TOML 文件
├── gen_major_mapping.py    # 生成年级-大类-专业映射关系
├── gen_lookup_table.py     # 从 TOML 文件提取课程代码，生成查找表模板
├── find_address.py         # 根据课程代码查找其所在文件
├── find_same.py            # 检测同名课程但课程代码不同的冲突
├── getFah.py               # 查询培养方案号（FAH）的测试脚本
├── get_major_list.py       # 查询大类专业列表的测试脚本
├── major_mapping.json      # 年级-大类-专业映射数据
├── lookup_table_template.json  # 课程代码查找表模板
├── course_code_conflicts.txt   # 课程代码冲突检测结果
├── warning.txt             # 运行警告日志
├── SCHOOL_MAJORS/          # 生成的专业课程 TOML 文件目录
│   ├── 2019/本/
│   ├── 2020/本/
│   ├── ...
│   └── 2025/本/
└── test/                   # 测试脚本
```

---

## 使用流程

### 1. 生成专业映射关系

运行 `gen_major_mapping.py` 生成 `major_mapping.json`：

```sh
python gen_major_mapping.py
```

该脚本会：

- 调用教务系统 API 获取各年级培养方案
- 查询每个大类下的分流专业
- 输出年级 → 大类 → 专业的映射关系

### 2. 抓取课程数据

运行 `get_courses.py` 抓取课程并生成 TOML 文件：

```sh
python get_courses.py
```

该脚本会：

- 读取 `major_mapping.json`
- 对每个培养方案号（FAH）调用教务 API 抓取课程列表
- 规范化课程字段为英文键
- 保存到 `SCHOOL_MAJORS/{year}/本/{专业名}.toml`

### 3. 生成课程代码查找表

运行 `gen_lookup_table.py`：

```sh
python gen_lookup_table.py
```

从所有 TOML 文件中提取唯一课程代码，保存到 `lookup_table_template.json`。

### 4. 检测课程代码冲突

运行 `find_same.py`：

```sh
python find_same.py
```

检测同名课程但课程代码不同的情况，结果输出到 `course_code_conflicts.txt`。

### 5. 查找课程所在文件

运行 `find_address.py`：

```sh
python find_address.py
```

输入课程代码，查找该课程出现在哪些专业的 TOML 文件中。

---

## 配置说明

### Cookie 配置

各脚本中的 `HEADERS` 包含 Cookie，需要替换为有效的登录 Cookie：

```python
HEADERS = {
    "Cookie": "你的Cookie",
    ...
}
```

### 代理配置

默认使用本地代理 `127.0.0.1:7897`，可根据需要修改 `PROXIES`：

```python
PROXIES = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
```

---

## 输出格式

生成的 TOML 文件格式示例：

```toml
[[courses]]
course_code = "COMP1003"
course_name = "C语言程序设计I"
credit = 3.0
total_hours = 48
assessment_method = "考试"
recommended_year_semester = "1-1"
course_nature = "必修"
course_category = "专业基础课"
offering_college = "计算机科学与技术学院"

[courses.hours]
theory = 32
lab = 16
practice = 0
exercise = 0
computer = 0
tutoring = 0
```

---

## 依赖

```sh
pip install requests toml
```

---

## 其他备用 API

https://jw.hitsz.edu.cn/xjgl/xjxxgl/xsxxdate/queryZyFxList

学籍管理-学籍信息管理-学生信息date-专业方向列表

https://jw.hitsz.edu.cn/xjgl/dlfzysq/toViewDlfzysq/zyfl

大类分专业申请-toView大类分专业申请-专业分流

## 注意事项

- 请确保 Cookie 有效，否则 API 请求会失败
- 建议在请求间添加适当延迟，避免被封禁
- 警告信息会同时输出到控制台和 `warning.txt`
