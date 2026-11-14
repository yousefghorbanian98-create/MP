"""گزارش محرمانهٔ ۸بخشی — قرارداد §۷ بستهٔ fitness-handoff (M24).

هر بخش الزامی است: هویت ← خواسته‌ها ← snapshot داده ← مقادیر مشتق‌شده ←
۱۳ محور (وضعیت+دلیل) ← زنجیرهٔ «داده و هدف ← قاعدهٔ نسخه‌دار ← شاهد/جمعیت/حدود ←
تصمیم/کنارگذاشته ← بازبین» ← نسخه‌ها ← بدنه/محدودیت‌ها/پایش.
داده‌های نامعلوم صراحتاً «unknown» ثبت می‌شوند (E01) — هرگز صفر/طبیعی.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NotFoundError
from db.models import Assessment14Domain, JacksonPollockMeasurement, Member, User
from modules.reporting.axes import axes_for_domains

RULE_VERSION = "rules-1.0 (PRD v0.1 gaps)"
SOURCES = "ACSM/NSCA (بازبینی‌نشدهٔ پروژه — گزارش M07)"
REPORT_VERSION = "confidential-report-1.0"


def _iso(d: date | datetime | None) -> str | None:
    return d.isoformat() if d else None


def build_confidential_report(db: Session, member_id: int) -> dict:
    member = db.get(Member, member_id)
    if member is None:
        raise NotFoundError("عضو یافت نشد")
    user = db.get(User, member.user_id)
    latest_assess = db.execute(
        select(Assessment14Domain).where(Assessment14Domain.member_id == member_id).order_by(Assessment14Domain.id.desc())
    ).scalars().first()
    latest_jp = db.execute(
        select(JacksonPollockMeasurement).where(JacksonPollockMeasurement.member_id == member_id).order_by(JacksonPollockMeasurement.id.desc())
    ).scalars().first()

    # ── بخش ۱: هویت (نسخهٔ محرمانه — نام واقعی مجاز) ──
    identity = {
        "full_name": user.full_name if user else "unknown",
        "phone": user.phone if user else "unknown",
        "athlete_id": f"A-{member.id:05d}",
        "record_id": f"P-{member.id:04d}",
        "gender": member.gender or "unknown",
        "birth_date": _iso(member.birth_date) or "unknown",
        "height_cm": member.height_cm if member.height_cm else "unknown",
        "report_generated_at": datetime.now(UTC).isoformat(),
        "report_version": REPORT_VERSION,
    }

    # ── بخش ۲: خواسته‌ها/اهداف با منشأ ──
    try:
        constraints = json.loads(member.constraints or "[]")
    except json.JSONDecodeError:
        constraints = []
    requests_goals = [
        {"item": "هدف اصلی", "value": member.goal or "unknown", "origin": "self_report"},
        {"item": "محدودیت‌ها/آسیب", "value": constraints or "unknown", "origin": "self_report"},
    ]

    # ── بخش ۳: snapshot کامل داده ──
    snapshot_rows: list[dict] = []
    snapshot_rows.append({
        "data": "قد", "raw": member.height_cm, "unit": "cm", "source": "member_profile",
        "date": _iso(member.birth_date) and "profile", "method": "unknown", "quality": "unknown",
    })
    if latest_jp:
        for site, mm in json.loads(latest_jp.skinfolds_mm).items():
            snapshot_rows.append({
                "data": f"چین {site}", "raw": mm, "unit": "mm", "source": "jp7_measurement",
                "date": _iso(latest_jp.measured_at), "method": latest_jp.method or "unknown",
                "quality": latest_jp.quality or "unknown",
            })
    else:
        snapshot_rows.append({"data": "پیکرسنجی", "raw": "unknown", "unit": "-", "source": "-", "date": "-", "method": "-", "quality": "not_collected"})
    if latest_assess:
        for s in sorted(latest_assess.scores, key=lambda x: x.domain):
            snapshot_rows.append({
                "data": f"امتیاز دامنه {s.domain}", "raw": s.score, "unit": "0..5",
                "source": "assessment_14domain", "date": _iso(latest_assess.created_at) if hasattr(latest_assess, "created_at") else "unknown",
                "method": "coach_assessment", "quality": "unknown",
            })
    unused = [
        {"data": "قرائت‌های خام چین (۷ نقطه)", "reason": "معادلهٔ J–P تا مرجع مستقل قفل است (D-012) — محاسبه نشد"},
    ]
    missing = ["وزن (kg)", "سابقهٔ آسیب تأییدشده", "دارو", "تست قدرت/استقامت"]

    # ── بخش ۴: مقادیر مشتق‌شده ──
    derived = [{
        "name": "درصد چربی بدن", "value": latest_jp.body_fat_pct if latest_jp else None,
        "method": latest_jp.equation_version if latest_jp else "not_collected",
        "inputs": "۷ چین خام + سن + جنسیت", "limits": "—",
        "uncertainty": "قفل — محاسبه انجام نشده (D-012)" if latest_jp else "داده موجود نیست",
    }]

    # ── بخش ۵: وضعیت ۱۳ محور ──
    domain_scores: dict[int, float] = {}
    if latest_assess:
        domain_scores = {s.domain: s.score for s in latest_assess.scores}
    axes = axes_for_domains(domain_scores)

    # ── بخش ۶: زنجیرهٔ تصمیم ──
    chain = [{
        "data_and_goal": f"هدف: {member.goal or 'unknown'} | محدودیت: {constraints}",
        "rule": f"{RULE_VERSION} — شروع حجم پایین مبتدی/متوسط",
        "evidence_population_limits": f"{SOURCES} — بزرگسال/سالمند سالم (D-016)",
        "decision": "برنامهٔ ۳-۴ جلسه‌ای فول‌بادی با گرم‌کردن/سردکردن",
        "rejected_alternative": "split پیشرفته (زمان/تجهیزات واقعی ندارد)",
        "review": "بازبینی ۲ هفته‌ای با KPI اجرای ست‌ها (M29)",
    }]

    # ── بخش ۷: نسخه‌ها ──
    versions = {
        "code": "MP M00–M24", "rules": RULE_VERSION, "sources": SOURCES,
        "report": REPORT_VERSION,
        "ai_model_used": None, "ai_note": "هیچ مدل مولدی در تصمیم‌ها استفاده نشده (E04)",
    }

    # ── بخش ۸: بدنه/محدودیت‌ها/پایش ──
    body_monitoring = {
        "program_body": "در پاسخ برنامه (snapshot نسخه‌دار) — خارج از این گزارش",
        "limits": ["دادهٔ ناقص: وزن/سابقهٔ آسیب", "J–P قفل (D-012)", "جمعیت فراتر از بزرگسال+سالمند پشت گیت (D-016)"],
        "monitoring": ["KPI اجرای ست‌ها", "درد (0-10)", "خواب/خستگی"], "review_interval": "2 weeks",
    }

    return {
        "section_1_identity": identity,
        "section_2_requests_goals": requests_goals,
        "section_3_data_snapshot": {"rows": snapshot_rows, "collected_but_unused": unused, "explicitly_missing": missing},
        "section_4_derived": derived,
        "section_5_axes_13": axes,
        "section_6_decision_chain": chain,
        "section_7_versions": versions,
        "section_8_body_limits_monitoring": body_monitoring,
    }


def render_html(report: dict) -> str:
    """HTML راست‌چین چاپ‌پذیر (D-020) — خروجی اصلی گزارش."""
    ident = report["section_1_identity"]
    rows = "".join(
        f"<tr><td>{r['data']}</td><td>{r['raw']}</td><td>{r['unit']}</td><td>{r['source']}</td>"
        f"<td>{r['date']}</td><td>{r['method']}</td><td>{r['quality']}</td></tr>"
        for r in report["section_3_data_snapshot"]["rows"]
    )
    axes_rows = "".join(
        f"<tr><td>{v['name_fa']}</td><td>{v['status']}</td><td>{v['reason']}</td></tr>"
        for v in report["section_5_axes_13"].values()
    )
    chain_rows = "".join(
        f"<li><b>داده/هدف:</b> {c['data_and_goal']} ← <b>قاعده:</b> {c['rule']} ← "
        f"<b>شاهد/جمعیت:</b> {c['evidence_population_limits']} ← <b>تصمیم:</b> {c['decision']} "
        f"(کنارگذاشته: {c['rejected_alternative']}) ← <b>بازبین:</b> {c['review']}</li>"
        for c in report["section_6_decision_chain"]
    )
    missing = "، ".join(report["section_3_data_snapshot"]["explicitly_missing"])
    return f"""<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<title>گزارش محرمانه — {ident['full_name']}</title>
<style>
body{{font-family:Vazirmatn,Tahoma,sans-serif;background:#0B0F14;color:#F3F6F8;margin:24px;line-height:1.9}}
h1,h2{{color:#34D399}} table{{width:100%;border-collapse:collapse;margin:12px 0}}
th,td{{border:1px solid #1F2937;padding:8px 10px;font-size:13px;text-align:right}}
th{{background:#111827}} .warn{{color:#F87171}} .ok{{color:#38BDF8}}
@media print{{body{{background:#fff;color:#000}} th,td{{border-color:#999}}}}
</style></head><body>
<h1>گزارش محرمانهٔ برنامهٔ تمرین — {ident['full_name']}</h1>
<p class="ok">شناسهٔ ورزشکار: {ident['athlete_id']} | پرونده: {ident['record_id']} | زمان: {ident['report_generated_at']} | نسخه: {ident['report_version']}</p>

<h2>۱. هویت و مشخصات</h2>
<p>نام: <b>{ident['full_name']}</b> | تلفن: {ident['phone']} | جنسیت: {ident['gender']} | تولد: {ident['birth_date']} | قد: {ident['height_cm']}</p>

<h2>۲. خواسته‌ها، اهداف و نیازها</h2>
<ul>{''.join(f"<li>{r['item']}: {r['value']} <i>({r['origin']})</i></li>" for r in report['section_2_requests_goals'])}</ul>

<h2>۳. snapshot کامل داده</h2>
<table><tr><th>داده</th><th>خام</th><th>واحد</th><th>منبع</th><th>تاریخ</th><th>روش</th><th>کیفیت</th></tr>{rows}</table>
<p>جمع‌آوری‌شده ولی استفاده‌نشده: {report['section_3_data_snapshot']['collected_but_unused'][0]['reason']}</p>
<p class="warn">صراحتاً مفقود: {missing}</p>

<h2>۴. مقادیر مشتق‌شده</h2>
<ul><li>درصد چربی: {report['section_4_derived'][0]['value'] or 'قفل — محاسبه نشده'} — {report['section_4_derived'][0]['uncertainty']}</li></ul>

<h2>۵. وضعیت ۱۳ محور</h2>
<table><tr><th>محور</th><th>وضعیت</th><th>دلیل</th></tr>{axes_rows}</table>

<h2>۶. زنجیرهٔ داده ← قاعده ← شاهد ← تصمیم</h2>
<ul>{chain_rows}</ul>

<h2>۷. نسخه‌ها</h2>
<p>کد: {report['section_7_versions']['code']} | قواعد: {report['section_7_versions']['rules']} | منابع: {report['section_7_versions']['sources']} | مدل هوش مصنوعی: {report['section_7_versions']['ai_note']}</p>

<h2>۸. بدنه، محدودیت‌ها و پایش</h2>
<p>محدودیت‌ها: {'؛ '.join(report['section_8_body_limits_monitoring']['limits'])}</p>
<p>پایش: {'، '.join(report['section_8_body_limits_monitoring']['monitoring'])} — بازبینی: {report['section_8_body_limits_monitoring']['review_interval']}</p>
</body></html>"""
