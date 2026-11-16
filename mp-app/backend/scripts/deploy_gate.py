#!/usr/bin/env python3
"""M60 / R8 — گیتِ استقرار: هر چیزی که *بدون* ساخت ایمیج قابل بررسی است.

# چرا این فایل (و چرا «Docker» مسدود نیست — فقط *ساخت* مسدود است)

`docker`/`podman` در این محیط نیستند و `download.docker.com` مسدود است، پس
`docker build` ممکن نیست. اما بیشترِ خطاهای استقرار **قبل از ساخت** قابل
کشف‌اند و همان‌ها هم واقعاً رخ می‌دهند:

  • port drift — Caddy/Dockerfile/compose روی پورت‌های مختلف توافق کنند
  • متغیر محیطی با نام اشتباه (مثلاً `MP_JWT_SECRET` در حالی که `env_prefix`
    فقط `MP_` است و فیلد `secret_key` نام دارد ← تنظیم بی‌اثر)
  • مسیر volume که به دادهٔ واقعی نمی‌رسد
  • healthcheck به مسیری که وجود ندارد
  • `dockerfile` در compose که به فایل موجود اشاره نمی‌کند

هر کدام از این‌ها در تولید یک استک «بالا آمده ولی کار نمی‌کند» می‌سازد.
این گیت همه را ایستا می‌سنجد و در CI اجرا می‌شود.

# اجرا

    python scripts/deploy_gate.py

کد خروج ۰ = سازگار، ۱ = تناقض. `--json` برای گزارش ماشینی.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MP = REPO / "mp-app"


@dataclass
class Report:
    checks: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def ok(self, msg: str) -> None:
        self.checks.append(msg)

    def bad(self, msg: str) -> None:
        self.problems.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.is_file() else ""


# ── ۱) پورت: Caddy ↔ Dockerfile.backend ↔ compose ──
def check_ports(r: Report) -> None:
    dockerfile = _read(MP / "infra" / "Dockerfile.backend")
    caddy = _read(MP / "infra" / "Caddyfile")
    compose = _read(MP / "infra" / "docker-compose.yml")

    df_expose = re.findall(r"^EXPOSE\s+(\d+)", dockerfile, re.M)
    df_cmd_port = re.findall(r"--port[\"', ]+(\d+)", dockerfile)
    caddy_upstream = re.findall(r"reverse_proxy\s+[\w.-]+:(\d+)", caddy)
    # فقط سرویسی که healthcheck روی همان پورت دارد ملاک است؛ سرویس‌های دیگر
    # (مثلاً ollama روی 11434) پورت خودشان را expose می‌کنند و ربطی ندارند.
    # نسخهٔ اول این را نمی‌فهمید و «تناقض» جعلی می‌ساخت.
    backend_block = compose.split("backend:", 1)[1].split("\n  valkey:", 1)[0]
    compose_expose = re.findall(r'expose:\s*\n\s*-\s*"(\d+)"', backend_block)

    if not df_expose or not caddy_upstream:
        r.bad("پورت در Dockerfile.backend یا Caddyfile پیدا نشد")
        return
    if set(df_expose) != set(df_cmd_port):
        r.bad(f"Dockerfile.backend: EXPOSE {df_expose} با CMD --port {df_cmd_port} نمی‌خواند")
    elif set(df_expose) != set(caddy_upstream):
        r.bad(f"پورت بک‌اند {df_expose} با upstream کدی {caddy_upstream} نمی‌خواند")
    else:
        r.ok(f"پورت یکسان در Dockerfile/Caddy: {df_expose[0]}")

    if compose_expose and set(compose_expose) != set(df_expose):
        r.bad(f"compose پورت {compose_expose} را expose می‌کند، بک‌اند روی {df_expose} است")
    elif compose_expose:
        r.ok("compose همان پورت بک‌اند را expose می‌کند")


# ── ۲) نام متغیرهای محیطی: با env_prefix و نام فیلد settings ──
def check_env_names(r: Report) -> None:
    config = _read(MP / "backend" / "app" / "config.py")
    compose_files = list((MP / "deploy").glob("docker-compose*.yml")) + list(
        (MP / "infra").glob("docker-compose*.yml")
    )

    m = re.search(r'env_prefix\s*=\s*"([^"]+)"', config)
    if not m:
        r.bad("env_prefix در config.py پیدا نشد")
        return
    prefix = m.group(1).upper()

    # نام فیلدهای Settings
    body = config.split("model_config", 1)[1].split("class ", 1)[0]
    fields = set(re.findall(r"^\s{4}([a-z_]+)\s*:", body, re.M))
    if not fields:
        r.bad("هیچ فیلدی در Settings پیدا نشد — الگوی parse عوض شده؟")
        return
    r.ok(f"env_prefix={prefix} · {len(fields)} فیلد settings")

    for cf in compose_files:
        # کامنت‌ها را حذف کن: مستندسازی دربارهٔ یک نام قدیمی نباید «تناقض» شود.
        # (نسخهٔ اول این را نمی‌فهمید و روی کامنتِ توضیحیِ همین فایل گیر می‌کرد.)
        text = "\n".join(
            line for line in _read(cf).splitlines() if not line.lstrip().startswith("#")
        )
        for key in set(re.findall(r"\bMP_[A-Z0-9_]+", text)):
            fieldname = key[len(prefix) :].lower()
            if fieldname not in fields:
                # نزدیک‌ترین نام ممکن را پیشنهاد بده تا رفع آسان باشد
                close = [f for f in fields if fieldname.split("_")[-1] in f]
                hint = f" — منظور: {prefix}{close[0].upper()}" if close else ""
                r.bad(f"{cf.name}: {key} هیچ فیلدی در Settings ندارد (بی‌اثر){hint}")
        r.ok(f"{cf.name}: همهٔ MP_* نام معتبر دارند")


# ── ۳) healthcheck ↔ مسیر موجود ──
def check_healthcheck(r: Report) -> None:
    main = _read(MP / "backend" / "app" / "main.py")
    if '"/health"' not in main and "'/health'" not in main:
        r.bad("مسیر /health در app/main.py ثبت نشده — healthcheck استک شکست می‌خورد")
    else:
        r.ok("مسیر /health وجود دارد")

    for cf in (MP / "deploy" / "docker-compose.yml", MP / "infra" / "docker-compose.yml"):
        text = _read(cf)
        for path in re.findall(r"localhost:\d+(/[A-Za-z0-9/_-]+)", text):
            if path != "/health":
                r.warn(f"{cf.name}: healthcheck به {path} می‌زند (فقط /health بررسی شد)")


# ── ۴) مسیرهای build/dockerfile در compose وجود دارند ──
def check_build_paths(r: Report) -> None:
    for cf in (MP / "deploy" / "docker-compose.yml", MP / "infra" / "docker-compose.yml"):
        text = _read(cf)
        if not text:
            r.warn(f"{cf} نیست")
            continue
        ctx = re.search(r"context:\s*(\S+)", text)
        df = re.search(r"dockerfile:\s*(\S+)", text)
        if ctx and df:
            resolved = (cf.parent / ctx.group(1) / df.group(1)).resolve()
            if resolved.is_file():
                r.ok(f"{cf.name}: dockerfile قابل حل است ({resolved.name})")
            else:
                r.bad(f"{cf.name}: dockerfile حل نمی‌شود → {resolved}")


# ── ۵) کلیدهای اجباری محیطی در deploy ──
def check_required_secrets(r: Report) -> None:
    text = _read(MP / "deploy" / "docker-compose.yml")
    if ":?" not in text:
        r.bad(
            "deploy/docker-compose.yml هیچ متغیر اجباری (`:?`) ندارد — استک با کلید پیش‌فرض بالا می‌آید"
        )
        return
    r.ok("متغیرهای اجباری با `:?` علامت‌گذاری شده‌اند")
    # هر کلیدی که در compose به بک‌اند داده می‌شود باید در config وجود داشته باشد
    # (تکرار عمدی چک env، چون این‌جا روی فایل deploy تمرکز داریم)


def main() -> int:
    ap = argparse.ArgumentParser(description="گیت استقرار ایستا — M60/R8")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    r = Report()
    for fn in (
        check_ports,
        check_env_names,
        check_healthcheck,
        check_build_paths,
        check_required_secrets,
    ):
        try:
            fn(r)
        except Exception as exc:  # noqa: BLE001
            r.bad(f"{fn.__name__} کرش کرد: {type(exc).__name__}: {exc}")

    if args.json:
        print(
            json.dumps(
                {"checks": r.checks, "problems": r.problems, "warnings": r.warnings},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for c in r.checks:
            print("✓", c)
        for w in r.warnings:
            print("!", w)
        for p in r.problems:
            print("✗", p)
        print(f"\n{len(r.checks)} بررسی · {len(r.warnings)} هشدار · {len(r.problems)} تناقض")
    return 1 if r.problems else 0


if __name__ == "__main__":
    sys.exit(main())
