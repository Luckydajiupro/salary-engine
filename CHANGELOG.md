# Changelog

本项目遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [1.0.0] — 2026-03-12

### Added

- 首个正式版本，从内部工具中抽离。
- `compute(input)`：税前 → 五险一金 + 个税（累计预扣法）→ 到手。
- 内置 5 个城市的社保 / 医保 / 公积金基数上下限与缴存比例：北京、上海、深圳、广州、杭州。
- `get_city(city_id)` / `CITIES` / `CUSTOM_CITY`：城市政策表读写。
- `data_age_warning()`：政策数据超过 12 个月未核对时给出提示。
- 基数托底 / 基数封顶 / 政策数据版本三类 `warnings`。
- 「被藏起来的钱」：`hidden` 下的公积金字段，展示个人 + 单位合计。

[1.0.0]: https://github.com/salary-engine/salary-engine/releases/tag/v1.0.0
