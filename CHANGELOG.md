# Changelog

本项目遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [2.0.0] — 2026-09-28

> ⚠️ 这是一个 **major** 版本，包含四处不兼容变更。升级前请先读下面的 Migration。

### Breaking Changes

- **城市参数由 `city_id` 改为 `city_code`（国标行政区划代码）**

  ```python
  # 1.x
  compute({"city_id": "beijing", "monthly_gross": 15000})
  # 2.x
  compute({"city_code": 110000, "monthly_gross": 15000})
  ```

- **`city_code` 识别失败时不再抛 `ValueError`，改为回落到默认城市（北京）**
  并在 `warnings` 里加一条 `城市代码未识别` 提示。
  批量算薪场景下，一条脏数据不应该把整批任务打断。

- **`months` 的默认值由 `12` 改为 `1`**
  `compute()` 的默认语义现在是「算一个月的工资」。需要全年视图请显式传 `"months": 12`。
  注意这一项**不会报错**，只会让结果与 1.x 不同。

- **返回值 `monthly` / `yearly` 重命名为 `pay` / `annual`**

  ```python
  # 1.x
  r["monthly"]["net"]   # r["yearly"]["net"]
  # 2.x
  r["pay"]["net"]       # r["annual"]["net"]
  ```

### Added

- `get_city_by_code(code)`：按国标行政区划代码取城市配置。
- 每个城市配置新增 `code` 字段（北京 `110000`、上海 `310000`、深圳 `440300`、广州 `440100`、杭州 `330100`）。

### Migration

```python
# 1.x
r = compute({"city_id": "shanghai", "monthly_gross": 20000})
print(r["monthly"]["net"], r["yearly"]["net"])

# 2.x
r = compute({"city_code": 310000, "monthly_gross": 20000, "months": 12})
print(r["pay"]["net"], r["annual"]["net"])
```

> 迁移时请特别注意两点：**旧的 `city_id` 会被静默忽略**（不报错），
> 以及 **`months` 不传时的默认值变了**。这两项都不会抛异常，只会让数字悄悄不一样。

## [1.0.0] — 2026-03-12

### Added

- 首个正式版本，从内部工具中抽离。
- `compute(input)`：税前 → 五险一金 + 个税（累计预扣法）→ 到手。
- 内置 5 个城市的社保 / 医保 / 公积金基数上下限与缴存比例：北京、上海、深圳、广州、杭州。
- `get_city(city_id)` / `CITIES` / `CUSTOM_CITY`：城市政策表读写。
- `data_age_warning()`：政策数据超过 12 个月未核对时给出提示。
- 基数托底 / 基数封顶 / 政策数据版本三类 `warnings`。
- 「被藏起来的钱」：`hidden` 下的公积金字段，展示个人 + 单位合计。

[2.0.0]: https://github.com/Luckydajiupro/salary-engine/releases/tag/v2.0.0
[1.0.0]: https://github.com/Luckydajiupro/salary-engine/releases/tag/v1.0.0
