"""برچسب‌زنی محوری ۱۴گانه + برچسب فارسی + وضعیت review (M33-c3).

قواعد دترمینیستیک از فیلدهای ساخت‌یافتهٔ منبع → بردار وزنی ۰..۱ روی ۱۴ محور (max-merge، نه جمع).
هر قاعده id + شرح دارد و با `--dump-rules` به‌صورت JSON برای rule-evidence خارج می‌شود (S6).

کاربرد:
    python scripts/tag_axis_coverage.py             # برچسب‌زنی همهٔ ردیف‌های catalog در DB
    python scripts/tag_axis_coverage.py --dump-rules  # فقط خروجی رجیستری قواعد
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.base import get_session_factory  # noqa: E402
from db.models.content import CatalogExercise  # noqa: E402

# ۱۴ محور — شناسه‌های پایدار (هم‌ارز DomainScore.domain در db/models/assessment.py)
AXES_FA: dict[int, str] = {
    1: "تحرک و انعطاف",
    2: "تعادل و پایداری",
    3: "قدرت عملکردی",
    4: "استقامت قلبی",
    5: "استقامت عضلانی",
    6: "تعادل عضلانی و وضعیت بدنی",
    7: "پایداری مرکز",
    8: "هماهنگی و مهارت حرکتی",
    9: "مکانیک بدن و بلند کردن بار",
    10: "قدرت گرفتن و مهارت دست",
    11: "تنفس و کنترل فشار",
    12: "بازیابی و مدیریت بار",
    13: "پیشگیری آسیب و آگاهی بدن",
    14: "مهارت‌های پایهٔ زندگی ورزشی",
}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    weights: dict[str, float]


def _muscles(row: dict) -> set[str]:
    raw = row.get("primary_muscles") or row.get("primaryMuscles") or []
    return {m.lower() for m in raw}


def _match(row: dict) -> list[Rule]:
    """قاعده‌های منطبق بر این ردیف — رجیستری شفاف (S6: هر ادعا ← یک rule_id)."""
    category = (row.get("category") or "").lower()
    mechanic = (row.get("mechanic") or "").lower()
    force = (row.get("force") or "").lower()
    equipment = (row.get("equipment") or "").lower()
    level = (row.get("level") or "").lower()
    name = (row.get("name") or "").lower()
    muscles = _muscles(row)
    rules: list[Rule] = []

    # --- دسته‌بندی ---
    cat_rules = {
        "strength": Rule("cat-strength", "دستهٔ قدرتی ← قدرت عملکردی + استقامت عضلانی", {"3": 0.7, "5": 0.5}),
        "powerlifting": Rule("cat-powerlift", "پاورلیفتینگ ← قدرت/مکانیک بلند کردن/گرفتن", {"3": 0.9, "9": 0.7, "10": 0.4}),
        "olympic weightlifting": Rule("cat-oly", "وزنه‌برداری المپیک ← قدرت/هماهنگی/مکانیک/تعادل", {"3": 0.8, "8": 0.7, "9": 0.8, "2": 0.4}),
        "strongman": Rule("cat-strongman", "استرانگ‌من ← قدرت/مکانیک/گرفتن/استقامت عضلانی", {"3": 0.9, "9": 0.9, "10": 0.7, "5": 0.5}),
        "cardio": Rule("cat-cardio", "کاردیو ← استقامت قلبی + بازیابی", {"4": 0.9, "5": 0.4, "12": 0.2}),
        "stretching": Rule("cat-stretch", "کششی ← تحرک/انعطاف + تعادل عضلانی + آگاهی بدن", {"1": 0.9, "6": 0.4, "13": 0.3}),
        "plyometrics": Rule("cat-plyo", "پلایومتریک ← قدرت/هماهنگی/تعادل/کاردیو", {"3": 0.5, "8": 0.6, "2": 0.5, "4": 0.3}),
    }
    if category in cat_rules:
        rules.append(cat_rules[category])

    # --- مکانیک/نیرو ---
    if mechanic == "compound":
        rules.append(Rule("mech-compound", "حرکت ترکیبی ← پایداری مرکز + مکانیک بدن", {"7": 0.4, "9": 0.3}))
    if mechanic == "isolation":
        rules.append(Rule("mech-isolation", "ایزوله ← تعادل عضلانی", {"6": 0.3}))
    if force == "static":
        rules.append(Rule("force-static", "ایزومتریک ← استقامت عضلانی/مرکز/کنترل تنفس", {"5": 0.5, "7": 0.4, "11": 0.2}))
    if force == "pull":
        rules.append(Rule("force-pull", "الگوی کششی ← درگیری گرفتن", {"10": 0.2}))

    # --- عضله ---
    if muscles & {"abdominals", "lower back"}:
        rules.append(Rule("muscle-core", "تمرکز شکم/کمر ← پایداری مرکز + وضعیت بدنی", {"7": 0.5, "6": 0.2}))
    if "forearms" in muscles:
        rules.append(Rule("muscle-forearm", "تمرکز ساعد ← قدرت گرفتن", {"10": 0.6}))
    if muscles & {"neck", "traps", "middle back"}:
        rules.append(Rule("muscle-posture", "گردن/کول/میان‌کمر ← وضعیت بدنی", {"6": 0.3}))

    # --- تجهیزات ---
    equip_rules = {
        "exercise ball": Rule("equip-ball", "توپ تعادل ← تعادل/مرکز", {"2": 0.4, "7": 0.3}),
        "kettlebells": Rule("equip-kb", "کتل‌بل ← قدرت/هماهنگی/گرفتن", {"3": 0.2, "8": 0.2, "10": 0.2}),
        "foam roll": Rule("equip-foam", "رول فوم ← بازیابی/تحرک/آگاهی بدن", {"12": 0.5, "1": 0.3, "13": 0.2}),
        "bands": Rule("equip-band", "کش ← تحرک/پیشگیری آسیب (فعال‌سازی)", {"1": 0.2, "13": 0.2}),
        "medicine ball": Rule("equip-med", "توپ طبی ← هماهنگی/قدرت", {"8": 0.3, "3": 0.2}),
    }
    if equipment in equip_rules:
        rules.append(equip_rules[equipment])

    # --- سطح ---
    if level == "beginner":
        rules.append(Rule("level-beginner", "سطح مبتدی ← یادگیری الگو/آگاهی بدن/مهارت پایه", {"13": 0.2, "14": 0.2}))
    if level == "expert":
        rules.append(Rule("level-expert", "سطح پیشرفته ← بار مهارتی هماهنگی", {"8": 0.1}))

    # --- الگوی نام ---
    if "balance" in name:
        rules.append(Rule("name-balance", "نام با تعادل ← تعادل", {"2": 0.6}))
    if "breath" in name or "breathing" in name:
        rules.append(Rule("name-breath", "نام با تنفس ← کنترل تنفس", {"11": 0.7}))
    return rules


def tag_exercise(row: dict) -> tuple[dict[str, float], list[str]]:
    """بردار پوشش + فهرست rule_idهای منطبق (max-merge روی هر محور)."""
    rules = _match(row)
    coverage: dict[str, float] = {}
    for rule in rules:
        for axis, weight in rule.weights.items():
            coverage[axis] = max(coverage.get(axis, 0.0), weight)
    return coverage, [r.rule_id for r in rules]


def intensity_band(row: dict) -> str:
    """باند شدت نسبی (قاعدهٔ ثبت‌شده): دسته/تجهیز مقدم بر سطح."""
    category = (row.get("category") or "").lower()
    equipment = (row.get("equipment") or "").lower()
    level = (row.get("level") or "").lower()
    if category in {"powerlifting", "olympic weightlifting", "strongman"} or equipment == "barbell":
        return "high"
    if category in {"stretching"} or equipment == "foam roll":
        return "low"
    if category in {"cardio", "plyometrics"}:
        return "moderate"
    return {"beginner": "low", "intermediate": "moderate", "expert": "high"}.get(level, "moderate")


# --- واژه‌نامهٔ فارسی نام‌ها (candidate — تا review انسانی) ---
PHRASES_FA: list[tuple[str, str]] = [
    ("bench press", "پرس سینه"), ("push up", "شنای سوئدی"), ("push ups", "شنای سوئدی"),
    ("pull up", "بارفیکس"), ("pull ups", "بارفیکس"), ("chin up", "زیر بارفیکس"),
    ("sit up", "دراز و نشست"), ("sit ups", "دراز و نشست"), ("dead lift", "ددلیفت"),
    ("lateral raise", "نشر جانبی"), ("front raise", "نشر جلو"), ("upright row", "زیر گردن"),
    ("pulldown", "زیر بغل سیم‌کش"), ("pull down", "زیر بغل سیم‌کش"),
    ("leg press", "پرس پا"), ("leg extension", "جلو ران"), ("leg curl", "پشت ران"),
    ("calf raise", "ساق پا"), ("lunge", "لانج"), ("split squat", "اسکوات پرشی"),
    ("box jump", "پرش جعبه"), ("jump squat", "اسکوات پرشی"), ("kettlebell swing", "کتل‌بل سوئینگ"),
    ("turkish get up", "برخاست ترکی"), ("farmer", "کشاورز"),
]
TOKENS_FA: dict[str, str] = {
    "press": "پرس", "dumbbell": "دمبل", "barbell": "هالتر", "cable": "سیم‌کش",
    "machine": "دستگاه", "smith": "اسمیت", "kettlebell": "کتل‌بل", "kettlebells": "کتل‌بل",
    "band": "کش", "bands": "کش‌ها", "ball": "توپ", "rope": "طناب", "plate": "صفحه",
    "ez": "ایزی", "bar": "میله", "sled": "سورتمه", "chain": "زنجیر", "chains": "زنجیرها",
    "stretch": "کشش", "stretching": "کششی", "curl": "جلو بازو", "curls": "جلو بازو",
    "extension": "اکستنشن", "row": "روئینگ", "rows": "روئینگ", "raise": "نشر",
    "raises": "نشر", "squat": "اسکوات", "squats": "اسکوات", "deadlift": "ددلیفت",
    "shrug": "شراگ", "shrugs": "شراگ", "flyes": "فلای", "fly": "فلای",
    "crunch": "کرانچ", "crunches": "کرانچ", "plank": "پلانک", "dip": "دیپ",
    "dips": "دیپ", "jump": "پرش", "jumps": "پرش", "throw": "پرتاب", "clean": "کلین",
    "snatch": "یک‌ضرب", "jerk": "ضرب", "hang": "معلق", "pull": "کشش", "push": "فشار",
    "grip": "گرفتن", "hold": "نگه‌داشتن", "carry": "حمل", "carrys": "حمل",
    "rotation": "چرخش", "rotations": "چرخش", "circles": "دایره", "circle": "دایره",
    "arm": "بازو", "arms": "بازوها", "leg": "پا", "legs": "پاها", "chest": "سینه",
    "back": "کمر", "shoulder": "شانه", "shoulders": "شانه‌ها", "neck": "گردن",
    "wrist": "مچ", "wrists": "مچ‌ها", "hip": "لگن", "hips": "لگن", "knee": "زانو",
    "knees": "زانوها", "ankle": "مچ پا", "head": "سر", "body": "بدن",
    "triceps": "پشت بازو", "tricep": "پشت بازو", "biceps": "جلو بازو", "bicep": "جلو بازو",
    "delt": "دلتوئید", "delts": "دلتوئید", "quad": "چهارسر", "quads": "چهارسر",
    "hamstring": "همسترینگ", "hamstrings": "همسترینگ", "glute": "سرینی", "glutes": "سرینی",
    "calf": "ساق", "calves": "ساق", "abs": "شکم", "ab": "شکم", "oblique": "مایل شکم",
    "obliques": "مایل شکم", "groin": "کشاله ران", "adductor": "نزدیک‌کننده ران",
    "adductors": "نزدیک‌کننده ران", "abductor": "دورکننده ران", "abductors": "دورکننده ران",
    "forearm": "ساعد", "forearms": "ساعد", "trap": "کول", "traps": "کول", "lats": "زیر بغل",
    "lat": "زیر بغل", "incline": "شیب‌دار", "decline": "سرشیب", "standing": "ایستاده",
    "seated": "نشسته", "lying": "خوابیده", "kneeling": "زانو زده", "walking": "در حال حرکت",
    "running": "دویدن", "one": "تک", "single": "تک", "double": "دوبل", "two": "دو",
    "alternating": "یکی در میان", "alternate": "یکی در میان", "wide": "پهن", "close": "باریک",
    "high": "بالا", "low": "پایین", "front": "جلو", "rear": "عقب", "side": "جانبی",
    "over": "بالای سر", "overhead": "بالای سر", "underhand": "زیردست", "palms": "کف دست",
    "power": "قدرت", "weighted": "با وزنه", "bent": "خمیده",
    "straight": "صاف", "reverse": "معکوس", "preacher": "پریچر", "hack": "هک",
    "lever": "اهرم", "leverage": "اهرم", "floor": "کف",
    "ground": "زمین", "wall": "دیوار", "chair": "صندلی", "bench": "نیمکت",
    "box": "جعبه", "step": "پله", "stair": "پله", "stairs": "پله‌ها",
    "swim": "شنا", "swimming": "شنا", "bike": "دوچرخه", "bicycle": "دوچرخه",
    "climb": "کوهنوردی", "climbing": "کوهنوردی", "crawl": "چهار دست و پا",
    "twist": "پیچش", "twists": "پیچش", "bend": "خم شدن", "bends": "خم شدن",
    "good": "خوب", "morning": "صبحگاهی", "windmill": "آسیاب بادی", "sit": "نشست",
    "get": "برخاست", "up": "بالا", "down": "پایین", "in": "درون", "out": "بیرون",
    "on": "روی", "from": "از", "with": "با", "and": "و", "the": "", "a": "", "to": "به",
    "of": "", "for": "", "smr": "رول فوم", "self": "خود", "massage": "ماساژ",
    "release": "رهاسازی", "activation": "فعال‌سازی", "warm": "گرم", "cool": "سرد",
    "downs": "پایین", "march": "رژه", "marches": "رژه", "jog": "دو آرام",
    "jogging": "دو آرام", "sprint": "اسپرینت", "sprints": "اسپرینت",
}


def name_fa_for(name: str) -> tuple[str, float]:
    """نام فارسی candidate + کسر توکن‌های ترجمه‌شده (کیفیت خودکار).

    تطبیق حریصانه با طول بیشینه: ابتدا عبارت‌ها، سپس تک‌توکن‌ها — هر عبارت به‌اندازهٔ
    توکن‌هایش امتیاز ترجمه می‌گیرد.
    """
    tokens = [t.strip(".").lower() for t in name.replace("/", " ").replace("-", " ").split() if t.strip()]
    phrases = sorted(PHRASES_FA, key=lambda p: -len(p[0].split()))
    translated: list[str] = []
    hits = 0
    i = 0
    while i < len(tokens):
        matched = False
        for en, fa in phrases:
            en_tokens = en.split()
            if tokens[i : i + len(en_tokens)] == en_tokens:
                hits += len(en_tokens)
                if fa:
                    translated.append(fa)
                i += len(en_tokens)
                matched = True
                break
        if not matched:
            key = tokens[i]
            if key in TOKENS_FA:
                hits += 1
                if TOKENS_FA[key]:
                    translated.append(TOKENS_FA[key])
            else:
                translated.append(key)
            i += 1
    fa_name = " ".join(translated).strip()
    quality = hits / max(len(tokens), 1)
    if quality < 0.5 or not fa_name:
        return "", quality
    return fa_name, quality


def tag_all(session) -> dict:
    """برچسب‌زنی همهٔ ردیف‌های catalog — idempotent."""
    stats = {"rows": 0, "with_axis": 0, "with_fa": 0, "rules_hit": 0}
    for row in session.query(CatalogExercise).all():
        source_row = {
            "name": row.name,
            "category": row.category,
            "level": row.level,
            "force": row.force,
            "mechanic": row.mechanic,
            "equipment": row.equipment,
            "primary_muscles": json.loads(row.primary_muscles),
        }
        coverage, rule_ids = tag_exercise(source_row)
        fa_name, quality = name_fa_for(row.name)
        row.axis_coverage = json.dumps(coverage, ensure_ascii=False, sort_keys=True)
        row.intensity_band = intensity_band(source_row)
        row.name_fa = fa_name
        if row.review_status != "verified":
            row.review_status = "candidate"
        meta = json.loads(row.review_meta or "{}")
        meta.update({"name_quality": round(quality, 2), "rules": rule_ids, "tagger": "m33c3-v1"})
        row.review_meta = json.dumps(meta, ensure_ascii=False)
        stats["rows"] += 1
        stats["with_axis"] += bool(coverage)
        stats["with_fa"] += bool(fa_name)
        stats["rules_hit"] += len(rule_ids)
    session.commit()
    return stats


def dump_rules() -> list[dict]:
    """رجیستری قواعد برای rule-evidence — نمونه‌های مرجع که هر ۲۳ قاعده را می‌پوشانند."""
    sample_rows = [
        {"name": "Barbell Squat", "category": "strength", "level": "beginner", "force": "push", "mechanic": "compound", "equipment": "barbell", "primary_muscles": ["quadriceps"]},
        {"name": "Bench Press", "category": "powerlifting", "level": "intermediate", "force": "push", "mechanic": "compound", "equipment": "barbell", "primary_muscles": ["chest"]},
        {"name": "Plank", "category": "strength", "level": "beginner", "force": "static", "mechanic": "isolation", "equipment": "body only", "primary_muscles": ["abdominals"]},
        {"name": "Clean", "category": "olympic weightlifting", "level": "expert", "force": "pull", "mechanic": "compound", "equipment": "barbell", "primary_muscles": ["quadriceps"]},
        {"name": "Atlas Stone", "category": "strongman", "level": "expert", "force": "pull", "mechanic": "compound", "equipment": "other", "primary_muscles": ["lower back"]},
        {"name": "Run", "category": "cardio", "level": "beginner", "force": None, "mechanic": None, "equipment": "body only", "primary_muscles": ["quadriceps"]},
        {"name": "Hamstring Stretch", "category": "stretching", "level": "beginner", "force": "static", "mechanic": None, "equipment": "body only", "primary_muscles": ["hamstrings"]},
        {"name": "Box Jump", "category": "plyometrics", "level": "intermediate", "force": "push", "mechanic": "compound", "equipment": "body only", "primary_muscles": ["quadriceps"]},
        {"name": "Face Pull", "category": "strength", "level": "intermediate", "force": "pull", "mechanic": "isolation", "equipment": "cable", "primary_muscles": ["shoulders"]},
        {"name": "Wrist Curl", "category": "strength", "level": "beginner", "force": "pull", "mechanic": "isolation", "equipment": "barbell", "primary_muscles": ["forearms"]},
        {"name": "Neck Curl", "category": "strength", "level": "beginner", "force": "pull", "mechanic": "isolation", "equipment": "body only", "primary_muscles": ["neck"]},
        {"name": "Stability Ball Crunch", "category": "strength", "level": "beginner", "force": "pull", "mechanic": "isolation", "equipment": "exercise ball", "primary_muscles": ["abdominals"]},
        {"name": "Kettlebell Swing", "category": "strength", "level": "intermediate", "force": "pull", "mechanic": "compound", "equipment": "kettlebells", "primary_muscles": ["glutes"]},
        {"name": "Hammer Foam Roll", "category": "stretching", "level": "beginner", "force": "static", "mechanic": None, "equipment": "foam roll", "primary_muscles": ["calves"]},
        {"name": "Band Pull-Apart", "category": "strength", "level": "beginner", "force": "pull", "mechanic": "isolation", "equipment": "bands", "primary_muscles": ["shoulders"]},
        {"name": "Medicine Ball Slam", "category": "plyometrics", "level": "intermediate", "force": "pull", "mechanic": "compound", "equipment": "medicine ball", "primary_muscles": ["abdominals"]},
        {"name": "Snatch Balance", "category": "olympic weightlifting", "level": "expert", "force": "push", "mechanic": "compound", "equipment": "barbell", "primary_muscles": ["shoulders"]},
        {"name": "Balance Board Squat", "category": "strength", "level": "intermediate", "force": "push", "mechanic": "compound", "equipment": "other", "primary_muscles": ["quadriceps"]},
        {"name": "Breathing Exercise", "category": "cardio", "level": "beginner", "force": "static", "mechanic": None, "equipment": "body only", "primary_muscles": ["abdominals"]},
    ]
    registry: dict[str, dict] = {}
    for row in sample_rows:
        for rule in _match(row):
            registry[rule.rule_id] = {
                "rule_id": rule.rule_id,
                "description": rule.description,
                "weights": rule.weights,
            }
    return sorted(registry.values(), key=lambda r: r["rule_id"])


def main() -> int:
    parser = argparse.ArgumentParser(description="tag catalog exercises with 14-axis coverage")
    parser.add_argument("--dump-rules", action="store_true")
    args = parser.parse_args()
    if args.dump_rules:
        print(json.dumps(dump_rules(), ensure_ascii=False, indent=2))
        return 0
    session = get_session_factory()()
    try:
        stats = tag_all(session)
        print(json.dumps(stats, ensure_ascii=False))
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
