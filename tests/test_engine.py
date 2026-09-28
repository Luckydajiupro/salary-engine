"""salary-engine 单元测试。

    python -m unittest discover -s tests -v

期望值多为手工推算，不是从引擎输出抄的。
改引擎后如果这些数字变了，先确认是引擎错了，还是手算的前提变了。
"""

import unittest

from salary_engine import compute, get_city_by_code, tax
from salary_engine.cities import CITIES


def run(gross, city_code=110000, months=12, **extra):
    payload = {"city_code": city_code, "monthly_gross": gross, "months": months}
    payload.update(extra)
    return compute(payload)


class CitiesTest(unittest.TestCase):
    def test_builtin_city_count(self):
        self.assertEqual(len(CITIES), 5)

    def test_lookup_by_code(self):
        self.assertEqual(get_city_by_code(110000)["name"], "北京")
        self.assertEqual(get_city_by_code(310000)["name"], "上海")
        self.assertEqual(get_city_by_code(440300)["name"], "深圳")
        self.assertEqual(get_city_by_code(440100)["name"], "广州")
        self.assertEqual(get_city_by_code(330100)["name"], "杭州")

    def test_unknown_code_returns_none(self):
        self.assertIsNone(get_city_by_code(999999))

    def test_beijing_limits(self):
        self.assertEqual(get_city_by_code(110000)["social"]["base_min"], 7270)
        self.assertEqual(get_city_by_code(110000)["social"]["base_max"], 36348)

    def test_shanghai_limits(self):
        self.assertEqual(get_city_by_code(310000)["social"]["base_max"], 37731)

    def test_shenzhen_three_independent_bases(self):
        shenzhen = get_city_by_code(440300)
        self.assertEqual(shenzhen["social"]["base_max"], 27549)
        self.assertEqual(shenzhen["medical_base"]["base_max"], 33633)
        self.assertEqual(shenzhen["fund"]["base_max"], 48471)

    def test_guangzhou_medical_base(self):
        self.assertEqual(get_city_by_code(440100)["medical_base"]["base_max"], 31170)


class ComputeTest(unittest.TestCase):
    def test_defaults_to_one_month(self):
        result = run(15000, months=None)
        self.assertEqual(result["months"], 1)
        self.assertEqual(len(result["tax_rows"]), 1)
        self.assertEqual(result["pay"]["net"], 11423.34)
        self.assertEqual(result["pay"]["tax"], 198.66)

    def test_beijing_15000_full_year(self):
        result = run(15000)
        self.assertEqual(result["months"], 12)
        self.assertEqual(result["pay"]["gross"], 15000)
        self.assertEqual(result["pay"]["net"], 11169.8)
        self.assertEqual(result["pay"]["tax"], 452.2)
        self.assertEqual(result["annual"]["net"], 134037.6)
        self.assertEqual(result["annual"]["tax"], 5426.4)
        self.assertEqual(result["tax_rows"][0]["tax"], 198.66)
        self.assertEqual(len(result["tax_rows"]), 12)
        self.assertEqual(result["city"]["id"], "beijing")

    def test_social_base_floor(self):
        result = run(4000)
        self.assertEqual(result["pay"]["net"], 2753.65)
        self.assertTrue(result["pay"]["bases"]["social"]["clamped_low"])
        titles = [w["title"] for w in result["warnings"]]
        self.assertIn("社保基数被下限托底", titles)

    def test_zero_income_has_no_deduction(self):
        self.assertEqual(run(0)["pay"]["net"], 0)

    def test_shenzhen(self):
        self.assertEqual(run(30000, city_code=440300)["pay"]["net"], 21242.78)

    def test_hidden_fund(self):
        self.assertEqual(run(15000)["hidden"]["fund_monthly"], 3600)


class FallbackTest(unittest.TestCase):
    """2.0 起 city_code 识别失败不再抛错，而是回落默认城市。"""

    def test_unknown_code_falls_back_without_raising(self):
        result = run(15000, city_code=999999)
        self.assertEqual(result["city"]["id"], "beijing")
        titles = [w["title"] for w in result["warnings"]]
        self.assertIn("城市代码未识别", titles)

    def test_legacy_city_id_is_silently_ignored(self):
        result = compute({"city_id": "shanghai", "monthly_gross": 20000, "months": 12})
        self.assertEqual(result["city"]["id"], "beijing")
        titles = [w["title"] for w in result["warnings"]]
        self.assertIn("城市代码未识别", titles)


class TaxBracketTest(unittest.TestCase):
    def test_brackets(self):
        brackets = tax.BRACKETS
        self.assertEqual(brackets[4]["upper"], 660000)
        self.assertEqual(brackets[4]["rate"], 0.3)
        self.assertEqual(brackets[4]["deduct"], 52920)
        self.assertEqual(brackets[0]["rate"], 0.03)

    def test_round2_uses_business_rounding(self):
        # 0.145 * 100 == 14.499999999999998，必须靠 1e-9 补偿才不会被误舍成 0.14
        self.assertEqual(tax.round2(0.145), 0.15)


if __name__ == "__main__":
    unittest.main()
