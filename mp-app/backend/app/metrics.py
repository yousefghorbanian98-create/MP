"""متریک‌های درون‌پروسه‌ای Prometheus-style (M13) — /metrics.

SLO گیت ورود: ۹۹٪ درخواست‌های check-in < ۲ ثانیه — histogram ساده نگه می‌داریم.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict


class Metrics:
    """شمارنده‌های ساده و thread-safe (بدون وابستگی سنگین)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, list[float]] = defaultdict(list)

    def inc(self, name: str, value: float = 1.0, **labels: str) -> None:
        key = self._key(name, labels)
        with self._lock:
            self._counters[key] += value

    def observe(self, name: str, value: float, **labels: str) -> None:
        key = self._key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            if len(self._histograms[key]) > 5000:  # محدودیت حافظه
                self._histograms[key] = self._histograms[key][-2500:]

    @staticmethod
    def _key(name: str, labels: dict[str, str]) -> str:
        if not labels:
            return name
        rendered = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{rendered}}}"

    def render(self) -> str:
        """خروجی متنی فرمت Prometheus."""
        lines: list[str] = []
        with self._lock:
            for key, val in sorted(self._counters.items()):
                lines.append(f"{key} {val}")
            for key, values in sorted(self._histograms.items()):
                if not values:
                    continue
                lines.append(f"{key}_count {len(values)}")
                lines.append(f"{key}_sum {sum(values):.6f}")
                svals = sorted(values)
                for q, label in ((0.5, "0.5"), (0.9, "0.9"), (0.99, "0.99")):
                    idx = min(int(q * len(svals)), len(svals) - 1)
                    lines.append(f'{key}_quantile{{quantile="{label}"}} {svals[idx]:.6f}')
        return "\n".join(lines) + "\n"

    def checkin_slo_ok(self, threshold: float = 2.0) -> bool:
        """SLO: ۹۹٪ چک‌این‌ها زیر threshold ثانیه."""
        with self._lock:
            values = self._histograms.get("mp_checkin_duration_seconds", [])
            if not values:
                return True
            svals = sorted(values)
            idx = min(int(0.99 * len(svals)), len(svals) - 1)
            return svals[idx] < threshold


metrics = Metrics()


class Timer:
    """context manager برای اندازه‌گیری مدت."""

    def __init__(self, name: str, **labels: str):
        self.name = name
        self.labels = labels
        self.start = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        metrics.observe(self.name, time.perf_counter() - self.start, **self.labels)
        return False
