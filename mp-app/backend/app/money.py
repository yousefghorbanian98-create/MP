"""نوع مشترک مبلغ ریالی (F‑09).

- `StrictInt`: رشته («1000»)، اعشار (1000.0) و bool (True) پذیرفته نمی‌شوند.
- سقف `MAX_SAFE_RIAL = 2**53 - 1`: بالاتر از آن، float و JSON دقت را از دست می‌دهند.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, StrictInt

MAX_SAFE_RIAL = 2**53 - 1

Rial = Annotated[StrictInt, Field(le=MAX_SAFE_RIAL, description="مبلغ به ریال (عدد صحیح)")]
