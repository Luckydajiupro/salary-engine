"""个人所得税引擎：工资薪金所得「累计预扣法」。

依据：
 - 《中华人民共和国个人所得税法》及其实施条例
 - 《个人所得税扣缴申报管理办法（试行）》（国家税务总局公告 2018 年第 61 号）
 - 国发〔2023〕13 号（专项附加扣除标准提高，2023-01-01 起执行）

核心公式：
  累计预扣预缴应纳税所得额
    = 累计收入 − 累计免税收入 − 累计减除费用（5000/月）
      − 累计专项扣除（个人三险一金） − 累计专项附加扣除 − 累计其他扣除

  本期应预扣预缴税额
    = (累计应纳税所得额 × 预扣率 − 速算扣除数) − 累计减免税额 − 累计已预扣预缴税额
"""

import math

# 基本减除费用（起征点），元/月
THRESHOLD = 5000

# 个人所得税预扣率表一（居民个人工资、薪金所得预扣预缴适用）
# upper：本级「累计预扣预缴应纳税所得额」上限（含）
BRACKETS = [
    {"upper": 36000, "rate": 0.03, "deduct": 0},
    {"upper": 144000, "rate": 0.10, "deduct": 2520},
    {"upper": 300000, "rate": 0.20, "deduct": 16920},
    {"upper": 420000, "rate": 0.25, "deduct": 31920},
    {"upper": 660000, "rate": 0.30, "deduct": 52920},
    {"upper": 960000, "rate": 0.35, "deduct": 85920},
    {"upper": float("inf"), "rate": 0.45, "deduct": 181920},
]

# 专项附加扣除标准（元/月），国发〔2023〕13 号后执行
SPECIAL_ADDITIONAL = {
    # 每孩每月，父母可一方 100% 或各 50%
    "infant_care": {"name": "3 岁以下婴幼儿照护", "per_unit": 2000, "unit": "孩"},
    "child_education": {"name": "子女教育", "per_unit": 2000, "unit": "孩"},
    # 学历（学位）继续教育，最长 48 个月
    "continuing_education": {"name": "继续教育（学历）", "per_unit": 400, "unit": "人"},
    # 职业资格继续教育：取得证书当年一次性 3600（在年度里处理）
    "housing_loan": {"name": "住房贷款利息", "per_unit": 1000, "unit": "户"},
    "housing_rent": {"name": "住房租金", "per_unit": 0, "unit": "户"},  # 分三档
    # 独生子女 3000/月；非独生分摊，每人不超过 1500/月
    "elderly_care": {"name": "赡养老人", "per_unit": 3000, "unit": "人"},
}

# 住房租金三档定额扣除（元/月）
RENT_LEVELS = {
    "tier1": {"name": "直辖市/省会/计划单列市等", "amount": 1500},
    "tier2": {"name": "市辖区户籍人口 > 100 万的城市", "amount": 1100},
    "tier3": {"name": "市辖区户籍人口 ≤ 100 万的城市", "amount": 800},
}

# 职业资格继续教育：取得证书当年一次性扣除
PROFESSIONAL_QUALIFICATION_ANNUAL = 3600

# 大病医疗：医保目录内自付超 15000 元的部分，年度限额 80000，据实扣除
MEDICAL_SERIOUS_THRESHOLD = 15000
MEDICAL_SERIOUS_CAP = 80000


def round2(n):
    """金额一律保留 2 位小数（分）。

    注意：Python 内置 round() 是「银行家舍入」，round(0.5) == 0，
    与业务上常用、也与本库历史版本用的「四舍五入」不一致，
    所以要自己用 floor(x + 0.5) 实现。
    加 1e-9 抵消二进制浮点误差：0.145 * 100 == 14.499999999999998，
    直接取整会被错误地舍成 0.14。
    """
    return math.floor((n + 1e-9) * 100 + 0.5) / 100


def bracket_of(cumulative_taxable):
    for bracket in BRACKETS:
        if cumulative_taxable <= bracket["upper"]:
            return bracket
    return BRACKETS[-1]


def cumulative_tax(cumulative_taxable):
    """根据「累计预扣预缴应纳税所得额」求累计应预扣预缴税额（已扣减速算扣除数）。"""
    if cumulative_taxable <= 0:
        return 0
    bracket = bracket_of(cumulative_taxable)
    # 这里必须 round2：直接把浮点结果暴露给调用方，
    # 会得到 1080.1000000000004 这类值
    return round2(cumulative_taxable * bracket["rate"] - bracket["deduct"])


def period_tax(cumulative_taxable, prev_withheld):
    """计算某一期的预扣预缴税额。

    返回 {"cum_tax": ..., "tax": ..., "bracket": ...}
    """
    cum_tax = round2(cumulative_tax(cumulative_taxable))
    tax = round2(cum_tax - prev_withheld)
    # 理论上不会为负（累计法单调不减）；出现负值说明输入异常，按 0 处理
    if tax < 0:
        tax = 0
    return {
        "cum_tax": cum_tax,
        "tax": tax,
        "bracket": bracket_of(0 if cumulative_taxable <= 0 else cumulative_taxable),
    }


def compute_monthly(
    monthly_gross,
    monthly_social=0,
    monthly_additional=0,
    monthly_other=0,
    other_prepaid_tax=0,
):
    """按累计预扣法逐月计算个税。

    :param monthly_gross: 每月税前工资（序列，长度 = 计算月数）
    :param monthly_social: 每月专项扣除（个人三险一金合计）
    :param monthly_additional: 每月专项附加扣除合计
    :param monthly_other: 每月其他扣除（企业年金、商业健康险等）
    :param other_prepaid_tax: 年内已预缴税额（年中换工作等场景）
    :return: 每月明细 list[dict]
    """
    grosses = list(monthly_gross or [])
    rows = []
    cum_income = 0.0
    cum_social = 0.0
    cum_additional = 0.0
    cum_other = 0.0
    prev_withheld = other_prepaid_tax or 0

    for index, gross in enumerate(grosses):
        month = index + 1
        cum_income += gross
        cum_social += monthly_social
        cum_additional += monthly_additional
        cum_other += monthly_other

        cum_threshold = THRESHOLD * month
        cum_taxable = cum_income - cum_threshold - cum_social - cum_additional - cum_other
        result = period_tax(cum_taxable, prev_withheld)
        prev_withheld = result["cum_tax"]

        rows.append(
            {
                "month": month,
                "gross": round2(gross),
                "cum_income": round2(cum_income),
                "cum_taxable": round2(cum_taxable if cum_taxable > 0 else 0),
                "tax": result["tax"],
                "cum_tax": result["cum_tax"],
                "rate": result["bracket"]["rate"],
                "net": round2(gross - monthly_social - result["tax"]),
            }
        )
    return rows


def compute_year(
    monthly_gross=0,
    months=12,
    monthly_social=0,
    monthly_additional=0,
    monthly_other=0,
    other_prepaid_tax=0,
):
    """全年汇总（月薪固定场景的便捷封装）。"""
    months = int(months)
    rows = compute_monthly(
        monthly_gross=[monthly_gross] * months,
        monthly_social=monthly_social,
        monthly_additional=monthly_additional,
        monthly_other=monthly_other,
        other_prepaid_tax=other_prepaid_tax,
    )
    total_tax = 0
    for row in rows:
        total_tax += row["tax"]
    return {
        "rows": rows,
        "total_tax": round2(total_tax),
        "total_gross": round2(monthly_gross * months),
    }


# 年终奖个税：可选择「单独计税」或「并入综合所得」
#
# 单独计税（财政部 税务总局公告 2023 年第 30 号，延续至 2027-12-31）：
#   应纳税额 = 全年一次性奖金 × 适用税率 − 速算扣除数
#   适用税率按「奖金 ÷ 12」查按月换算后的综合所得税率表确定
BONUS_BRACKETS = [
    {"upper": 3000, "rate": 0.03, "deduct": 0},
    {"upper": 12000, "rate": 0.10, "deduct": 210},
    {"upper": 25000, "rate": 0.20, "deduct": 1410},
    {"upper": 35000, "rate": 0.25, "deduct": 2660},
    {"upper": 55000, "rate": 0.30, "deduct": 4410},
    {"upper": 80000, "rate": 0.35, "deduct": 7160},
    {"upper": float("inf"), "rate": 0.45, "deduct": 15160},
]


def bonus_bracket_of(monthly_average):
    for bracket in BONUS_BRACKETS:
        if monthly_average <= bracket["upper"]:
            return bracket
    return BONUS_BRACKETS[-1]


def bonus_tax_separate(bonus):
    """年终奖单独计税。"""
    if bonus <= 0:
        return {"tax": 0, "rate": 0, "deduct": 0, "monthly_average": 0, "net": 0}
    average = bonus / 12
    bracket = bonus_bracket_of(average)
    tax = round2(bonus * bracket["rate"] - bracket["deduct"])
    if tax < 0:
        tax = 0
    return {
        "tax": tax,
        "rate": bracket["rate"],
        "deduct": bracket["deduct"],
        "monthly_average": round2(average),
        "net": round2(bonus - tax),
    }
