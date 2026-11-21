"""WP 4.5 (F‑22) — migration c3f01ab129e2 نباید SQL را با f‑string بسازد.

قبل از اصلاح: چهار `op.execute(f"DROP INDEX IF EXISTS ...")` (خطوط 67، 165، 169، 171).
قاعدهٔ semgrep `mp-raw-sql-string-format` هم این فایل را نمی‌گرفت، چون:
  (۱) مسیر `**/migrations/*` را مستثنا کرده بود؛
  (۲) الگوها فقط با آرگومان دوم (`, ...`) تطبیق می‌یافتند؛
  (۳) یک `pattern-not-inside: def $F(...): ...` هر تابعی را می‌پوشاند و قاعده را خاموش می‌کرد.
بعد از اصلاح: هیچ فراخوانی `execute` در این migration آرگومانِ ساخته‌شده با f‑string،
`%`، `.format` یا `+` ندارد.
"""

from __future__ import annotations

import ast
from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "db"
    / "migrations"
    / "versions"
    / "c3f01ab129e2_m47_c1_align_indexes_and_nullability_.py"
)
EXECUTE_NAMES = {"execute", "exec_driver_sql"}


def _built_sql_calls(tree: ast.AST) -> list[int]:
    """خطوط فراخوانی‌هایی که آرگومان اولشان SQL ساخته‌شده است."""
    bad: list[int] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr not in EXECUTE_NAMES or not node.args:
            continue
        arg = node.args[0]
        built = (
            isinstance(arg, ast.JoinedStr)
            or (isinstance(arg, ast.BinOp) and isinstance(arg.op, (ast.Mod, ast.Add)))
            or (
                isinstance(arg, ast.Call)
                and isinstance(arg.func, ast.Attribute)
                and arg.func.attr == "format"
            )
        )
        if built:
            bad.append(node.lineno)
    return bad


def test_migration_has_no_sql_built_from_strings() -> None:
    tree = ast.parse(MIGRATION.read_text(encoding="utf-8"))
    assert _built_sql_calls(tree) == [], "F‑22: execute با SQL ساخته‌شده از رشته"


def test_detector_catches_fstring_drop_index() -> None:
    """خود آشکارساز باید روی الگوی خطا کار کند (جلوگیری از سبز کاذب)."""
    sample = ast.parse('op.execute(f"DROP INDEX IF EXISTS ix_{t}_x")')
    assert _built_sql_calls(sample) == [1]
