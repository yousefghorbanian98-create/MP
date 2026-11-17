"""Prometheus metrics backed by the official client library.

The previous hand-built text exposition used invalid histogram sample names and
stored counters independently in each Uvicorn worker. Prometheus' Apache-2.0
client now provides standards-compliant exposition and optional multiprocess
aggregation for the production worker model.
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict
from collections.abc import Mapping

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest

_DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 2.5, 5.0, 10.0)
_SLO_SAMPLE_LIMIT = 5000


class Metrics:
    """Thread-safe wrappers for dynamically named counters and histograms."""

    def __init__(self) -> None:
        self._registry = CollectorRegistry()
        self._counters: dict[tuple[str, tuple[str, ...]], Counter] = {}
        self._histograms: dict[tuple[str, tuple[str, ...]], Histogram] = {}
        self._slo_values: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.RLock()

    @staticmethod
    def _labels(labels: Mapping[str, str]) -> dict[str, str]:
        return {name: str(value) for name, value in labels.items()}

    def inc(self, name: str, value: float = 1.0, **labels: str) -> None:
        label_values = self._labels(labels)
        label_names = tuple(sorted(label_values))
        key = (name, label_names)
        with self._lock:
            metric = self._counters.get(key)
            if metric is None:
                metric = Counter(
                    name,
                    f"Muscle Paradise counter: {name}",
                    labelnames=label_names,
                    registry=self._registry,
                )
                self._counters[key] = metric
        child = metric.labels(**label_values) if label_names else metric
        child.inc(value)

    def observe(self, name: str, value: float, **labels: str) -> None:
        label_values = self._labels(labels)
        label_names = tuple(sorted(label_values))
        key = (name, label_names)
        with self._lock:
            metric = self._histograms.get(key)
            if metric is None:
                metric = Histogram(
                    name,
                    f"Muscle Paradise observation: {name}",
                    labelnames=label_names,
                    buckets=_DEFAULT_BUCKETS,
                    registry=self._registry,
                )
                self._histograms[key] = metric
            if name == "mp_checkin_duration_seconds":
                samples = self._slo_values[name]
                samples.append(value)
                if len(samples) > _SLO_SAMPLE_LIMIT:
                    del samples[: len(samples) - _SLO_SAMPLE_LIMIT // 2]
        child = metric.labels(**label_values) if label_names else metric
        child.observe(value)

    def render(self) -> str:
        """Return standards-compliant Prometheus text exposition."""
        multiprocess_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
        if multiprocess_dir:
            from prometheus_client import multiprocess

            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry, path=multiprocess_dir)
        else:
            registry = self._registry
        return generate_latest(registry).decode("utf-8")

    def checkin_slo_ok(self, threshold: float = 2.0) -> bool:
        """Report whether the current bounded sample window has p99 < threshold."""
        with self._lock:
            values = self._slo_values.get("mp_checkin_duration_seconds", [])
            if not values:
                return True
            ordered = sorted(values)
            index = min(int(0.99 * len(ordered)), len(ordered) - 1)
            return ordered[index] < threshold


metrics = Metrics()


class Timer:
    """Context manager that records elapsed seconds, including raised errors."""

    def __init__(self, name: str, **labels: str) -> None:
        self.name = name
        self.labels = labels
        self.start = 0.0

    def __enter__(self) -> Timer:
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> bool:
        metrics.observe(self.name, time.perf_counter() - self.start, **self.labels)
        return False
