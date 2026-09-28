"""城市社保 / 公积金配置表。

数据核对时间：2026-09

⚠️ 三个最容易算错的地方，改这个文件时务必注意：

 1. 社保缴费基数与公积金缴存基数是【两套独立的上下限】，不可混用。
    例：深圳社保养老上限 27,549，公积金基数上限 48,471，差近一倍。

 2. 部分城市的【医保基数与养老基数也不同】。
    例：深圳医保上限 33,633 vs 养老上限 27,549；广州医保 31,170 vs 养老 27,549。
    这类城市用 medical_base 单独声明。

 3. 各地「年度」起止时间不一致，公布时间也有先后：
    - 北京/上海：2026-07-01 起，但通知到 8 月才发布，会追溯执行并补缴差额
    - 广东（深圳/广州）养老保险：2025-07 起，2026 年度尚未公布新标准，暂沿用
    - 杭州（浙江）：2026-07-01 起
    - 深圳/广州医保：2026-01-01 起（自然年）

⚠️ 基数上下限每年 7 月前后调整。请每年 7–9 月核对一次官方通告，
   更新数值的同时更新 effective_from 和 verified_at。
"""

CITIES = [
    {
        "id": "beijing",
        "code": 110000,
        "name": "北京",
        "verified_at": "2026-09",
        "social": {
            "effective_from": "2026-07",
            "base_min": 7270,
            "base_max": 36348,
            "rates": {
                "pension": 0.08,  # 养老 8%
                "medical": 0.02,  # 医疗 2%（另有大额互助固定金额）
                "unemployment": 0.005,  # 失业 0.5%
            },
            "fixed": {"medical": 3},  # 大额互助 3 元/月
        },
        "fund": {
            "effective_from": "2026-07",
            "base_min": 2540,
            "base_max": 36348,
            "rate_min": 0.05,
            "rate_max": 0.12,
        },
        "note": (
            "养老/失业/工伤/医保统一基数 7,270–36,348。医保个人另缴 3 元/月大额互助。"
            "公积金比例由单位在 5%–12% 内自定，顶格 12% 时月缴存上限 8,724 元。"
        ),
        "sources": [
            "北京市人社局等《关于 2026 年度各项社会保险缴费工资基数上下限的通告》",
            "京房公积金管委会办〔2026〕6 号",
        ],
    },
    {
        "id": "shanghai",
        "code": 310000,
        "name": "上海",
        "verified_at": "2026-09",
        "social": {
            "effective_from": "2026-07",
            "base_min": 7546,
            "base_max": 37731,
            "rates": {"pension": 0.08, "medical": 0.02, "unemployment": 0.005},
            "fixed": {},
        },
        "fund": {
            "effective_from": "2026-07",
            "base_min": 2740,
            "base_max": 37731,
            "rate_min": 0.05,
            "rate_max": 0.12,
        },
        "note": (
            "全国社保基数上限最高的城市之一（37,731）。公积金分「基础 5%–7%（强制）+ "
            "补充 1%–5%（自愿）」，叠加后单边最高 12%，此处按合并区间处理。"
        ),
        "sources": [
            "上海市 2026 年度社会保险缴费基数通告",
            "沪公积金管委会〔2026〕3 号",
        ],
    },
    {
        "id": "shenzhen",
        "code": 440300,
        "name": "深圳",
        "verified_at": "2026-09",
        "social": {
            "effective_from": "2025-07",
            "base_min": 4775,
            "base_max": 27549,
            "rates": {"pension": 0.08, "medical": 0.02, "unemployment": 0.002},
            "fixed": {},
        },
        "medical_base": {
            "effective_from": "2026-01",
            "base_min": 6727,
            "base_max": 33633,
        },
        "fund": {
            "effective_from": "2026-07",
            "base_min": 2520,
            "base_max": 48471,
            "rate_min": 0.05,
            "rate_max": 0.12,
        },
        "note": (
            "⚠️ 三个基数各不相同：养老 4,775–27,549（2025-07 起，2026 年度广东尚未公布新标准，"
            "暂沿用）；医保一档 6,727–33,633（2026 自然年）；公积金 2,520–48,471（全国上限最高）。"
            "医保二档个人比例为 0.5%，本工具按一档计算。"
        ),
        "sources": [
            "广东省企业职工基本养老保险缴费基数通告",
            "深圳市 2026 年度职工医保缴费基数通告",
            "深圳市住房公积金管理中心 2026 年度缴存基数通知",
        ],
    },
    {
        "id": "guangzhou",
        "code": 440100,
        "name": "广州",
        "verified_at": "2026-09",
        "social": {
            "effective_from": "2025-07",
            "base_min": 5510,
            "base_max": 27549,
            "rates": {"pension": 0.08, "medical": 0.02, "unemployment": 0.002},
            "fixed": {},
        },
        "medical_base": {
            "effective_from": "2026-01",
            "base_min": 6234,
            "base_max": 31170,
        },
        "fund": {
            "effective_from": "2026-07",
            "base_min": 2680,
            "base_max": 41697,
            "rate_min": 0.05,
            "rate_max": 0.12,
        },
        "note": (
            "⚠️ 养老 5,510–27,549（2025-07 起，暂沿用）与医保 6,234–31,170（2026 自然年）基数不同。"
            "公积金下限自 2026-09-01 起由 2,500 上调为 2,680。"
        ),
        "sources": [
            "粤人社发〔2025〕32 号",
            "广州市 2026 年度职工医保缴费基数通告",
            "广州住房公积金管理中心 2026 年度缴存调整通知",
        ],
    },
    {
        "id": "hangzhou",
        "code": 330100,
        "name": "杭州",
        "verified_at": "2026-09",
        "social": {
            "effective_from": "2026-07",
            "base_min": 5346,
            "base_max": 26730,
            "rates": {"pension": 0.08, "medical": 0.02, "unemployment": 0.005},
            "fixed": {},
        },
        "fund": {
            "effective_from": "2026-07",
            "base_min": 2660,
            "base_max": 42151,
            "rate_min": 0.05,
            "rate_max": 0.12,
        },
        "note": (
            "社保按浙江省 2026 年度全省统一标准（2026-07-01 起，此前为 4,986–25,299）。"
            "公积金下限为杭州市区最低工资，桐庐/淳安/建德为 2,430。"
        ),
        "sources": [
            "浙江省 2026 年度社会保险缴费基数通知",
            "杭州住房公积金管理中心 2026 年度调整通知",
        ],
    },

    # 新增城市时：从当地人社局 / 医保局 / 公积金管理中心官方通告取数。
    # 社保基数、医保基数（如与社保不同）、公积金基数分别记录，各自标注 effective_from。
    # 查不到官方来源就不要加，宁可让用户走「自定义」手动填。
]

# 已知但尚未核实官方数据的城市，仅用于在 UI 上给出提示（不参与计算）
UNVERIFIED_CITIES = ["成都", "南京", "武汉", "西安", "苏州", "重庆", "长沙", "天津"]

# 自定义城市模板：所有参数手动填写
CUSTOM_CITY = {
    "id": "custom",
    "code": 0,
    "name": "自定义",
    "verified_at": "manual",
    "social": {
        "effective_from": "manual",
        "base_min": 0,
        "base_max": 999999,
        "rates": {"pension": 0.08, "medical": 0.02, "unemployment": 0.005},
        "fixed": {},
    },
    "fund": {
        "effective_from": "manual",
        "base_min": 0,
        "base_max": 999999,
        "rate_min": 0.05,
        "rate_max": 0.12,
    },
    "note": "手动填写所在城市的基数上下限与各项比例。",
    "sources": [],
}


def get_city(city_id):
    """按字符串 id 取城市配置，找不到返回 None。"""
    if city_id == "custom":
        return CUSTOM_CITY
    for city in CITIES:
        if city["id"] == city_id:
            return city
    return None


def get_city_by_code(code):
    """按【国标行政区划代码】取城市配置，找不到返回 None。

    相比字符串 id，行政区划代码更稳定，也不容易拼错。

    :param code: 行政区划代码，如 110000（北京）、310000（上海）
    """
    try:
        number = int(code)
    except (TypeError, ValueError):
        return None
    if number == 0:
        return CUSTOM_CITY
    for city in CITIES:
        if city.get("code") == number:
            return city
    return None


def data_age_warning(now_month=None):
    """是否存在任何城市的政策数据已经陈旧（距核对时间超过 12 个月）。

    返回 list[dict]，为空表示都不陈旧。
    """
    stale = []
    if now_month and len(str(now_month)) == 7 and str(now_month)[4] == "-":
        ny, nm = int(now_month[:4]), int(now_month[5:7])
    else:
        import datetime

        today = datetime.date.today()
        ny, nm = today.year, today.month

    for city in CITIES:
        verified = city.get("verified_at")
        if not verified or verified == "manual":
            continue
        vy, vm = int(verified[:4]), int(verified[5:7])
        age_months = ny * 12 + nm - (vy * 12 + vm)
        if age_months >= 12:
            stale.append(
                {"city": city["name"], "verified_at": verified, "age_months": age_months}
            )
    return stale
