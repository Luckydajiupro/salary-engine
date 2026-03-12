"""salary-engine 单元测试。

    python -m unittest discover -s tests -v

期望值多为手工推算，不是从引擎输出抄的。
改引擎后如果这些数字变了，先确认是引擎错了，还是手算的前提变了。
"""

import unittest

from salary_engine import compute, get_city, tax
from salary_engine.cities import CITIES


def run(gross, city_id="beijing", months=12, **extra):
    payload = {"city_id": city_id, "monthly_gross": gross, "months": months}
    payload.update(extra)
    return compute(payload)


class CitiesTest(unittest.TestCase):
    def test_builtin_city_count(self):
        self.assertEqual(len(CITIES), 5)

    def test_beijing_limits(self):
        self.assertEqual(get_city("beijing")["social"]["base_min"], 7270)
        self.assertEqual(get_city("beijing")["social"]["base_max"], 36348)

    def test_shanghai_limits(self):
        self.assertEqual(get_city("shanghai")["social"]["base_max"], 37731)

    def test_shenzhen_three_independent_bases(self):
        shenzhen = get_city("shenzhen")
        self.assertEqual(shenzhen["social"]["base_max"], 27549)
        self.assertEqual(shenzhen["medical_base"]["base_max"], 33633)
        self.assertEqual(shenzhen["fund"]["base_max"], 48471)

    def test_guangzhou_medical_base(self):
        self.assertEqual(get_city("guangzhou")["medical_base"]["base_max"], 31170)

    def test_unknown_city_returns_none(self):
        self.assertIsNone(get_city("nowhere"))

    def test_custom_city(self):
        self.assertEqual(get_city("custom")["name"], "自定义")


class ComputeTest(unittest.TestCase):
    def test_beijing_15000(self):
        result = run(15000)
        self.assertEqual(result["monthly"]["gross"], 15000)
        self.assertEqual(result["monthly"]["net"], 11169.8)
        self.assertEqual(result["yearly"]["net"], 134037.6)
        self.assertEqual(result["yearly"]["tax"], 5426.4)
        self.assertEqual(result["monthly"]["tax"], 452.2)
        self.assertEqual(result["tax_rows"][0]["tax"], 198.66)
        self.assertEqual(len(result["tax_rows"]), 12)
        self.assertEqual(result["city"]["id"], "beijing")

    def test_social_base_floor(self):
        result = run(4000)
        self.assertEqual(result["monthly"]["net"], 2753.65)
        self.assertTrue(result["monthly"]["bases"]["social"]["clamped_low"])
        self.assertEqual(result["warnings"][0]["title"], "社保基数被下限托底")

    def test_zero_income_has_no_deduction(self):
        self.assertEqual(run(0)["monthly"]["net"], 0)

    def test_months_is_not_a_simple_multiplier(self):
        one = run(15000, months=1)
        self.assertEqual(len(one["tax_rows"]), 1)
        self.assertEqual(one["tax_rows"][0]["tax"], 198.66)
        # 12 个月的「月均个税」是 452.20，跟单月 198.66 不是一个数
        self.assertEqual(one["monthly"]["tax"], 198.66)
        self.assertEqual(run(15000)["monthly"]["tax"], 452.2)

    def test_shenzhen(self):
        self.assertEqual(run(30000, city_id="shenzhen")["monthly"]["net"], 21242.78)

    def test_unknown_city_raises(self):
        with self.assertRaises(ValueError):
            run(10000, city_id="nowhere")

    def test_hidden_fund(self):
        result = run(15000)
        self.assertEqual(result["hidden"]["fund_monthly"], 3600)


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
