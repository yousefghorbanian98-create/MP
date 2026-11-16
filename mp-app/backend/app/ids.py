"""M60/R18 — تایپ شناسه با سقف، برای *بدنهٔ* درخواست.

# یافتهٔ DAST (پس از بستن مسیرها)

middleware `app/id_guard.py` فقط بخش‌های عددیِ **مسیر** را می‌گیرد. DAST نشان
داد همان کلاس خطا از **بدنه** هم می‌آید:

    POST /api/v1/payments            {"member_id": 10**30}
    POST /api/v1/assessments         {"member_id": 10**30}
    POST /api/v1/chat/conversations  {"member_id": 10**30}
    POST /api/v1/classes/cancel      {"member_id": 10**30}

pydantic `int` خالی این‌ها را می‌پذیرد، سرویس به SQLite می‌رسد و
`OverflowError` ← ۵۰۰. راه درست در سطح اسکیما: `Id`/`OptId` با `ge=1` و
`le=MAX_SAFE_ID` — همان سقفِ `app/deps.PathId` و `app/id_guard.MAX_SAFE_ID`،
تا هر سه لایه یک عدد بگویند و نشود یکی را عوض کرد و بقیه را فراموش کرد.

# چرا فقط `*_id`

مهاجرت خودکار انجام شد (نه دستی): هر فیلد `*_id` در `modules/*/schemas.py`
که `int` خالی بود. فیلدهایی که از قبل `Field(ge=1)` داشتند دست نخوردند (سقف
بالا ندارند ولی `ge` رفتار پایداری دارد و تغییرشان ریسک بی‌فایده بود —
به‌عنوان بدهی در گزارش ثبت شد).
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

MAX_SAFE_ID = 9_007_199_254_740_991

# ge=1: شناسهٔ صفر/منفی معنایی ندارد (نه رکوردی، نه FK معتبر)
Id = Annotated[int, Field(ge=1, le=MAX_SAFE_ID)]
OptId = Annotated[int | None, Field(ge=1, le=MAX_SAFE_ID)]
