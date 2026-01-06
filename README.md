# hoa-majors

## 项目简介

本项目用于从 **哈尔滨工业大学（深圳）教务系统** 抓取各年级、各专业的培养方案课程数据，并将其规范化后保存为 TOML 格式文件，便于后续查询与分析。

---

## 目录结构

```text
├── gen_major_mapping.py    # 生成年级-大类-专业映射关系
├── get_courses.py          # 抓取课程数据并生成 TOML 文件
├── gen_lookup_table.py     # 从 TOML 文件提取课程代码，生成查找表模板
├── update_lookup_table.py  # 更新查找表（仅添加新课程，不覆盖已有条目）
├── find_address.py         # 根据课程代码查找其所在文件
├── find_same.py            # 检测同名课程但课程代码不同的冲突
├── config.py               # 统一配置管理（Cookie、代理等）
├── major_mapping.json      # 年级-大类-专业映射数据
├── lookup_table_template.py    # 课程代码查找表模板
├── course_code_conflicts.txt   # 课程代码冲突检测结果
├── warning.txt             # 运行警告日志
├── pyproject.toml          # 项目配置文件
├── .env.example            # 环境变量模板
├── .gitignore              # Git 忽略配置
├── SCHOOL_MAJORS/          # 生成的专业课程 TOML 文件目录
│   ├── 2019/本/
│   ├── 2020/本/
│   ├── ...
│   └── 2025/本/
└── test/                   # 测试脚本
│   ├── get_major_correspondence.py # 获取单个大类的分流专业列表
│   ├── get_course_single.py        # 获取单课程信息并生成 TOML 文件
│   └── getFah.py                   # 获取培养方案信息
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

从所有 TOML 文件中提取唯一课程代码，保存到 `lookup_table_template.py`。

### 4. 更新课程代码查找表

运行 `update_lookup_table.py`：

```sh
python update_lookup_table.py
```

增量更新查找表，仅添加新的课程代码，不会覆盖已有的条目。

### 5. 检测课程代码冲突

运行 `find_same.py`：

```sh
python find_same.py
```

检测同名课程但课程代码不同的情况，结果输出到 `course_code_conflicts.txt`。

### 6. 查找课程所在文件

运行 `find_address.py`：

```sh
python find_address.py
```

输入课程代码，查找该课程出现在哪些专业的 TOML 文件中。

---

## 配置说明

### 环境配置

本项目使用 `.env` 文件管理敏感配置（如 Cookie）。首次使用请按以下步骤配置：

1. 复制 `.env.example` 为 `.env`：

   ```sh
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入你的实际配置：

   ```ini
   # 登录教务系统后，从浏览器开发者工具中获取 Cookie
   # F12 -> Network -> 任意请求 -> Headers -> Cookie
   JW_COOKIE="你的Cookie值"

   # 代理配置（可选，如果不需要代理可以留空）
   HTTP_PROXY="http://127.0.0.1:7897"
   HTTPS_PROXY="http://127.0.0.1:7897"
   ```

> **注意**: `.env` 文件包含敏感信息，已在 `.gitignore` 中配置忽略，请勿提交到 Git 仓库。

### 获取 Cookie 的方法

1. 打开浏览器，登录 [HITSZ 教务系统](https://jw.hitsz.edu.cn/)
2. 按 F12 打开开发者工具
3. 切换到 Network（网络）标签
4. 刷新页面或进行任意操作
5. 点击任意请求，在 Headers（请求头）中找到 `Cookie` 字段
6. 复制完整的 Cookie 值到 `.env` 文件

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

## 安装依赖

### 方式一：使用 pip（推荐）

```sh
pip install -e .
```

### 方式二：手动安装

```sh
pip install requests toml python-dotenv
```

---

## 其他备用 API

<https://jw.hitsz.edu.cn/xjgl/xjxxgl/xsxxdate/queryZyFxList>

学籍管理-学籍信息管理-学生信息date-专业方向列表

<https://jw.hitsz.edu.cn/xjgl/dlfzysq/toViewDlfzysq/zyfl>

大类分专业申请-toView大类分专业申请-专业分流

## 注意事项

- 请确保 Cookie 有效，否则 API 请求会失败
- 建议在请求间添加适当延迟，避免被封禁
- 警告信息会同时输出到控制台和 `warning.txt`
