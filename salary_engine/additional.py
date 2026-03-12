"""专项附加扣除计算。

存的是「原始参数」（孩数、是否租房等），而不是算好的金额，
这样设置页可以原样回显，用户改一项不用重填其他项。

依据：国发〔2023〕13 号（2023-01-01 起执行的标准）
"""

from . import tax

SPECIAL = tax.SPECIAL_ADDITIONAL
RENT_LEVELS = tax.RENT_LEVELS


def _num(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number != number or number in (float("inf"), float("-inf")):
        return 0.0
    return number


def default_additional():
    return {
        "infant_care": 0,  # 3 岁以下婴幼儿照护：孩数
        "child_education": 0,  # 子女教育：孩数
        "continuing_education": False,  # 学历（学位）继续教育：400/月
        "housing_loan": False,  # 住房贷款利息：1000/月
        "housing_rent": "",  # 住房租金：'tier1' | 'tier2' | 'tier3' | ''
        "elderly_care": 0,  # 赡养老人：0–3000/月
        "medical_serious": 0,  # 大病医疗：年度金额（只在年度汇算清缴时扣）
    }


def monthly_total(additional):
    """每月可享受的专项附加扣除合计（不含大病医疗）。"""
    additional = additional or {}
    has_rent = bool(additional.get("housing_rent")) and additional.get(
        "housing_rent"
    ) in RENT_LEVELS

    total = 0.0
    total += _num(additional.get("infant_care")) * SPECIAL["infant_care"]["per_unit"]
    total += _num(additional.get("child_education")) * SPECIAL["child_education"][
        "per_unit"
    ]
    if additional.get("continuing_education"):
        total += SPECIAL["continuing_education"]["per_unit"]
    # 住房贷款利息与住房租金不可同时享受。冲突时只计租金（validate 会同时报错），
    # 宁可少算也不要给出一个多算了的数字。
    if additional.get("housing_loan") and not has_rent:
        total += SPECIAL["housing_loan"]["per_unit"]
    if has_rent:
        total += RENT_LEVELS[additional["housing_rent"]]["amount"]
    total += _num(additional.get("elderly_care"))
    return tax.round2(total)


def validate(additional):
    """校验输入是否合规，返回错误信息列表（空表示合法）。"""
    additional = additional or {}
    errors = []
    if additional.get("housing_loan") and additional.get("housing_rent"):
        errors.append("住房贷款利息与住房租金只能二选一，不能同时享受")
    if _num(additional.get("elderly_care")) > 3000:
        errors.append("赡养老人每月扣除上限 3,000 元；非独生子女分摊时每人不超过 1,500 元")
    if _num(additional.get("elderly_care")) < 0:
        errors.append("赡养老人扣除额不能为负")
    return errors


def describe(additional):
    """拆解成明细行，供界面展示。"""
    additional = additional or {}
    rows = []

    if _num(additional.get("infant_care")) > 0:
        rows.append(
            {
                "key": "infant_care",
                "name": "3 岁以下婴幼儿照护",
                "detail": "%d 个孩子" % _num(additional["infant_care"]),
                "amount": _num(additional["infant_care"])
                * SPECIAL["infant_care"]["per_unit"],
            }
        )
    if _num(additional.get("child_education")) > 0:
        rows.append(
            {
                "key": "child_education",
                "name": "子女教育",
                "detail": "%d 个孩子" % _num(additional["child_education"]),
                "amount": _num(additional["child_education"])
                * SPECIAL["child_education"]["per_unit"],
            }
        )
    if additional.get("continuing_education"):
        rows.append(
            {
                "key": "continuing_education",
                "name": "继续教育（学历）",
                "detail": "最长 48 个月",
                "amount": SPECIAL["continuing_education"]["per_unit"],
            }
        )
    if additional.get("housing_loan"):
        rows.append(
            {
                "key": "housing_loan",
                "name": "住房贷款利息",
                "detail": "最长 240 个月",
                "amount": SPECIAL["housing_loan"]["per_unit"],
            }
        )
    rent = additional.get("housing_rent")
    if rent and rent in RENT_LEVELS:
        rows.append(
            {
                "key": "housing_rent",
                "name": "住房租金",
                "detail": RENT_LEVELS[rent]["name"],
                "amount": RENT_LEVELS[rent]["amount"],
            }
        )
    if _num(additional.get("elderly_care")) > 0:
        rows.append(
            {
                "key": "elderly_care",
                "name": "赡养老人",
                "detail": "",
                "amount": _num(additional["elderly_care"]),
            }
        )
    return rows


def medical_serious_deduction(annual_self_paid):
    """大病医疗：医保目录内自付超 1.5 万元的部分，年度限额 8 万元，据实扣除。

    注意：这一项【只能在年度汇算清缴时扣】，不参与每月预扣。
    """
    paid = _num(annual_self_paid)
    if paid <= tax.MEDICAL_SERIOUS_THRESHOLD:
        return {"deduction": 0, "refundable": 0}
    deduction = min(
        paid - tax.MEDICAL_SERIOUS_THRESHOLD, tax.MEDICAL_SERIOUS_CAP
    )
    return {"deduction": tax.round2(deduction), "refundable": tax.round2(deduction)}


def rent_options():
    """租金档次选项（供界面下拉）。"""
    return [
        {"value": "", "label": "不申报"},
        {"value": "tier1", "label": "1,500 元/月 · " + RENT_LEVELS["tier1"]["name"]},
        {"value": "tier2", "label": "1,100 元/月 · 市辖区户籍人口 > 100 万"},
        {"value": "tier3", "label": "800 元/月 · 市辖区户籍人口 ≤ 100 万"},
    ]
