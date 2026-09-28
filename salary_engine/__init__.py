"""salary-engine —— 中国工资到手计算引擎。

把税前月薪翻译成「到手」：五险一金 + 个人所得税（累计预扣法）。

    from salary_engine import compute

    r = compute({"city_code": 110000, "monthly_gross": 15000})
    r["pay"]["net"]       # 月均到手
    r["annual"]["net"]    # 全年到手
"""

from . import tax, additional
from .cities import (
    CITIES,
    CUSTOM_CITY,
    UNVERIFIED_CITIES,
    data_age_warning,
    get_city,
    get_city_by_code,
)
from .salary import compute, compute_monthly_deductions, resolve_base

__version__ = "2.0.0"

__all__ = [
    "compute",
    "resolve_base",
    "compute_monthly_deductions",
    "CITIES",
    "CUSTOM_CITY",
    "UNVERIFIED_CITIES",
    "get_city",
    "get_city_by_code",
    "data_age_warning",
    "tax",
    "additional",
    "__version__",
]
