# salary-engine

中国工资到手计算引擎。把**税前月薪**算成**到手**：五险一金 + 个人所得税（累计预扣法）。

纯 Python，零第三方依赖。

> 测算结果仅供参考，以实际缴纳与税务申报为准。

---

## 安装

```bash
pip install salary-engine
```

## 快速开始

```python
from salary_engine import compute

r = compute({
    "city_code": 110000,
    "monthly_gross": 15000,
    "months": 12,
})

r["pay"]["net"]              # 月均到手
r["annual"]["net"]           # 全年到手
r["annual"]["tax"]           # 全年个税
r["pay"]["breakdown"]        # 五险一金明细（逐项）
r["hidden"]["fund_monthly"]  # 公积金（个人 + 单位，都归你）
r["warnings"]                # 基数托底 / 封顶等提示
```

---

## `compute(input)`

### 参数

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `city_code` | int | — | 国标行政区划代码。见下方「内置城市」 |
| `city_override` | dict | — | 直接传入城市配置对象，优先于 `city_code` |
| `monthly_gross` | float | — | 税前月薪 |
| `social_base_mode` | str | `'actual'` | 社保基数口径：`'actual'` 按实际工资 / `'min'` 按下限 / `'manual'` 手动指定 |
| `social_base_manual` | float | 0 | `social_base_mode='manual'` 时的基数 |
| `fund_base_mode` | str | `'actual'` | 公积金基数口径，取值同上 |
| `fund_base_manual` | float | 0 | `fund_base_mode='manual'` 时的基数 |
| `fund_rate` | float | `0.12` | 公积金个人缴存比例，取值 0–0.12 |
| `monthly_additional` | float | 0 | 专项附加扣除合计（元/月） |
| `monthly_other` | float | 0 | 其他扣除（企业年金等，元/月） |
| `months` | int | **1** | 计算月数 |

> **`months` 不是简单的乘法系数。** 工资薪金走**累计预扣法**：年初按 3% 预扣，
> 累计应纳税所得额越过 36,000 后跳档，年底扣得最多。
> 所以 `compute({... "months": 12})["pay"]["tax"]` 是**月均个税**，
> 跟只算 1 个月的个税**不是同一个数**。
> 例：北京月薪 15,000 时，第 1 个月个税 198.66，全年 5,426.40，月均 452.20 ——
> 拿 452.20 当"1 个月的个税"会差一倍多。
> **默认只算 1 个月**；要全年视图请显式传 `"months": 12`。

### 返回值

| 字段 | 说明 |
| --- | --- |
| `city` | 实际使用的城市配置对象 |
| `months` | 实际使用的计算月数 |
| `pay` | 月度视图：`gross` / `breakdown` / `bases` / `social_total` / `fund_personal` / `fund_company` / `special_deduction` / `tax`（月均）/ `net`（月均） |
| `annual` | 年度视图：`gross` / `social_and_fund` / `tax` / `net` |
| `hidden` | 「被藏起来的钱」：`fund_personal_monthly` / `fund_company_monthly` / `fund_monthly` / `fund_yearly` |
| `tax_rows` | 逐月个税明细（累计法） |
| `warnings` | 提示列表：社保基数托底、基数封顶、政策数据版本 |

---

## 内置城市

| `city_code` | 城市 |
| --- | --- |
| `110000` | 北京 |
| `310000` | 上海 |
| `440300` | 深圳 |
| `440100` | 广州 |
| `330100` | 杭州 |
| `0` | 自定义（配合 `city_override` 使用） |

每个城市的数据都带三个溯源字段：

| 字段 | 含义 |
| --- | --- |
| `effective_from` | 该口径从哪个月开始生效 |
| `verified_at` | 这份数据是哪个月核对的 |
| `sources` | 政策依据（通告名或文号） |

`get_city_by_code(code)` 按行政区划代码取城市配置，`data_age_warning()` 可检查数据是否已超过 12 个月未核对。

---

## 它和常见在线计算器的三点不同

1. **社保基数与公积金基数是两套独立上下限**。深圳社保养老上限 27,549，公积金上限 48,471，差近一倍。
2. **工资低于社保基数下限时会被「托底」**，扣款占比显著高于预期，引擎会显式告警。
3. **明示「被藏起来的钱」**：公积金由个人和单位各缴一半，全部进入你的账户。

---

## 已知限制

- 只内置 5 个城市；其余城市请用 `city_code=0` 配合 `city_override` 手动填。
- 深圳医保按**一档（2%）**计算。
- 大病医疗只能在年度汇算清缴时扣除，不参与月度预扣。
- 公积金利息与提取规则未建模。

---

## License

MIT
