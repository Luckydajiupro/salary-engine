"""算薪引擎：税前工资 → 五险一金 + 个税 → 到手。

与常见在线计算器的三点差异，也是本工具的价值所在：
 1. 社保基数与公积金基数分别按各自的上下限约束（两者往往不同）
 2. 当工资低于社保基数下限时，基数被「托底」，到手会显著低于预期 —— 显式告警
 3. 明示「被藏起来的钱」：公积金（个人 + 单位）与个人账户累积
"""

from . import cities, tax
from .tax import round2


def _num(value):
    """把任意输入转成有限数值，转不动就当 0（与历史版本行为一致）。"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number != number or number in (float("inf"), float("-inf")):
        return 0.0
    return number


def _clamp(value, minimum, maximum):
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def resolve_base(mode, manual, reference, limits):
    """解析实际采用的缴费基数。

    :param mode: 'actual' | 'min' | 'manual'
    :param manual: 手动指定的基数
    :param reference: 参照值（通常为税前月薪）
    :param limits: {"min": ..., "max": ...}
    """
    if reference <= 0:
        # 无收入时不产生缴费
        return {
            "value": 0,
            "raw": 0,
            "mode": mode,
            "clamped_low": False,
            "clamped_high": False,
        }

    if mode == "manual":
        raw = _num(manual)
    elif mode == "min":
        raw = limits["min"]
    else:
        raw = reference  # 'actual'：按实际工资

    return {
        "value": round2(_clamp(raw, limits["min"], limits["max"])),
        "raw": round2(raw),
        "mode": mode,
        "clamped_low": raw < limits["min"],
        "clamped_high": raw > limits["max"],
    }


def compute_monthly_deductions(inp, city):
    """计算每月社保与公积金（这些金额全年不变，个税另外按累计预扣法算）。"""
    gross = _num(inp.get("monthly_gross"))
    social = city["social"]
    fund = city["fund"]

    social_base = resolve_base(
        inp.get("social_base_mode") or "actual",
        inp.get("social_base_manual"),
        gross,
        {"min": social["base_min"], "max": social["base_max"]},
    )
    fund_base = resolve_base(
        inp.get("fund_base_mode") or "actual",
        inp.get("fund_base_manual"),
        gross,
        {"min": fund["base_min"], "max": fund["base_max"]},
    )

    # 缴存比例由用户自己填。不强制 5% 的下限（北京经营困难企业可申请降到 1%–4%），
    # 但上限收在 12% 法定上限，顺便防止手滑多敲一位（比如想填 12 却打成 120）。
    raw_rate = inp.get("fund_rate")
    if raw_rate is None or raw_rate == "":
        fund_rate = 0.12
    else:
        fund_rate = _clamp(_num(raw_rate), 0, 0.12)

    social_base_value = social_base["value"]

    # 医保基数可能与社保基数不同：深圳（医保上限 33,633 vs 养老 27,549）、
    # 广州（31,170 vs 27,549）由医保局单独公布。这些城市用 medical_base 声明。
    medical_base_info = None
    medical_base_value = social_base_value
    if city.get("medical_base"):
        medical_base_info = resolve_base(
            inp.get("social_base_mode") or "actual",
            inp.get("social_base_manual"),
            gross,
            {
                "min": city["medical_base"]["base_min"],
                "max": city["medical_base"]["base_max"],
            },
        )
        medical_base_value = medical_base_info["value"]

    pension = round2(social_base_value * social["rates"]["pension"])
    medical_rate = round2(medical_base_value * social["rates"]["medical"])
    # 固定项（如北京大额互助 3 元/月）只在确有社保缴费时计。
    # 否则无收入（基数为 0）时也会被扣，到手变成负数。
    fixed_medical = social.get("fixed", {}).get("medical", 0)
    medical_fixed = fixed_medical if social_base_value > 0 and fixed_medical else 0
    medical = round2(medical_rate + medical_fixed)
    unemployment = round2(social_base_value * social["rates"]["unemployment"])
    social_total = round2(pension + medical + unemployment)

    fund_personal = round2(fund_base["value"] * fund_rate)
    fund_company = fund_personal  # 单位与个人同比例

    breakdown = [
        {
            "key": "pension",
            "name": "养老保险",
            "rate": social["rates"]["pension"],
            "base": social_base_value,
            "amount": pension,
            "to_account": True,
        },
        {
            "key": "medical",
            "name": "医疗保险",
            "rate": social["rates"]["medical"],
            "base": medical_base_value,
            "amount": medical,
            "fixed": medical_fixed,
            "to_account": True,
        },
        {
            "key": "unemployment",
            "name": "失业保险",
            "rate": social["rates"]["unemployment"],
            "base": social_base_value,
            "amount": unemployment,
            "to_account": False,
        },
        {
            "key": "fund",
            "name": "住房公积金",
            "rate": fund_rate,
            "base": fund_base["value"],
            "amount": fund_personal,
            "to_account": True,
            "company_match": fund_company,
        },
    ]

    return {
        "gross": round2(gross),
        "payload": {
            "bases": {
                "social": social_base,
                "medical": medical_base_info,
                "fund": fund_base,
                "fund_rate": {
                    "value": fund_rate,
                    "min": fund["rate_min"],
                    "max": fund["rate_max"],
                },
            },
            "breakdown": breakdown,
            "pension": pension,
            "medical": medical,
            "unemployment": unemployment,
            "social_total": social_total,
            "fund_personal": fund_personal,
            "fund_company": fund_company,
            # 个税口径的「专项扣除」= 个人缴纳的三险一金
            "special_deduction": round2(social_total + fund_personal),
        },
    }


def compute(inp):
    """主入口。

    :param inp: dict，支持：
        city_id            城市 id（见 cities.py）
        city_override      自定义城市参数（覆盖 city_id）
        monthly_gross      税前月薪
        social_base_mode   'actual' | 'min' | 'manual'，默认 actual
        social_base_manual 手动基数
        fund_base_mode     'actual' | 'min' | 'manual'
        fund_base_manual   手动基数
        fund_rate          公积金个人缴存比例（0–0.12）
        monthly_additional 专项附加扣除合计（元/月）
        monthly_other      其他扣除（企业年金等，元/月）
        months             计算月数，默认 12
    :raises ValueError: 城市 id 无法识别
    """
    inp = inp or {}
    city = inp.get("city_override") or cities.get_city(inp.get("city_id"))
    if not city:
        raise ValueError("未知城市: %s" % inp.get("city_id"))

    deductions = compute_monthly_deductions(inp, city)
    payload = deductions["payload"]
    months = int(_num(inp.get("months")) or 12)
    monthly_additional = _num(inp.get("monthly_additional"))
    monthly_other = _num(inp.get("monthly_other"))

    # 全年个税：累计预扣法逐月计算
    tax_result = tax.compute_year(
        monthly_gross=deductions["gross"],
        months=months,
        monthly_social=payload["special_deduction"],
        monthly_additional=monthly_additional,
        monthly_other=monthly_other,
    )

    total_social_and_fund = round2(
        (payload["social_total"] + payload["fund_personal"]) * months
    )
    total_net = round2(
        deductions["gross"] * months - total_social_and_fund - tax_result["total_tax"]
    )

    # 被藏起来的钱：公积金个人 + 单位，全部进入个人公积金账户
    hidden_fund_monthly = round2(payload["fund_personal"] + payload["fund_company"])

    warnings = []
    if deductions["gross"] > 0 and payload["bases"]["social"]["clamped_low"]:
        warnings.append(
            {
                "level": "info",
                "title": "社保基数被下限托底",
                "text": (
                    "你的月薪 %s 元低于当地社保基数下限 %s 元，社保按下限 %s 元计算。"
                    "所以扣款占工资的比例会比想象中高。"
                    % (
                        deductions["gross"],
                        city["social"]["base_min"],
                        payload["bases"]["social"]["value"],
                    )
                ),
            }
        )
    if deductions["gross"] > 0 and payload["bases"]["social"]["clamped_high"]:
        warnings.append(
            {
                "level": "info",
                "title": "社保基数已封顶",
                "text": (
                    "你的月薪超过当地社保基数上限 %s 元，超出部分不再缴纳社保，"
                    "这部分工资不会被扣社保。" % city["social"]["base_max"]
                ),
            }
        )
    if deductions["gross"] > 0 and payload["bases"]["fund"]["clamped_high"]:
        warnings.append(
            {
                "level": "info",
                "title": "公积金基数已封顶",
                "text": "公积金按上限 %s 元计算。" % payload["bases"]["fund"]["value"],
            }
        )
    social_from = city["social"].get("effective_from")
    if social_from and social_from != "manual":
        warnings.append(
            {
                "level": "muted",
                "title": "政策数据版本",
                "text": (
                    "社保口径 %s 起执行，公积金口径 %s 起执行。"
                    "各地通常每年 7 月调整，请留意更新。"
                    % (social_from, city["fund"]["effective_from"])
                ),
            }
        )

    return {
        "city": city,
        "months": months,
        "monthly": {
            "gross": deductions["gross"],
            "breakdown": payload["breakdown"],
            "bases": payload["bases"],
            "social_total": payload["social_total"],
            "fund_personal": payload["fund_personal"],
            "fund_company": payload["fund_company"],
            "social_and_fund": round2(payload["social_total"] + payload["fund_personal"]),
            "special_deduction": payload["special_deduction"],
            "additional": monthly_additional,
            "other": monthly_other,
            "tax": round2(tax_result["total_tax"] / months),  # 月均个税
            "net": round2(total_net / months),  # 月均到手
        },
        "yearly": {
            "gross": tax_result["total_gross"],
            "social_and_fund": total_social_and_fund,
            "tax": tax_result["total_tax"],
            "net": total_net,
        },
        "hidden": {
            "fund_personal_monthly": payload["fund_personal"],
            "fund_company_monthly": payload["fund_company"],
            "fund_monthly": hidden_fund_monthly,
            "fund_yearly": round2(hidden_fund_monthly * months),
            "note": (
                "公积金个人缴纳与单位缴纳部分全部进入你的个人公积金账户，"
                "归你所有，租房/购房可提取。"
            ),
        },
        "tax_rows": tax_result["rows"],
        "warnings": warnings,
    }
