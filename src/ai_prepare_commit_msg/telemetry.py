"""Opt-in, content-free OpenTelemetry metrics for one hook invocation."""

# pylint: disable=broad-exception-caught

import logging
import math
import os
import re
import threading
import time
from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from typing import Any
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)
ENDPOINT_ENV = "AI_PREPARE_COMMIT_TELEMETRY_ENDPOINT"
_active: "RunMetrics | None" = None  # pylint: disable=invalid-name


class RunMetrics:
    """Accumulate numeric measurements without retaining prompt content."""

    def __init__(self) -> None:
        self.started = time.monotonic()
        self.outcome = "error"
        self.commit_type = "unknown"
        self.approval = "none"
        self.values: defaultdict[str, float] = defaultdict(int)
        self.lock = threading.Lock()
        self.compression = (0, 0)

    def add(self, name: str, value: float = 1) -> None:
        """Record a measurement from a generation or summarization thread."""
        if math.isfinite(value) and value >= 0:
            with self.lock:
                self.values[name] += value

    def snapshot(self) -> dict[str, float]:
        """Copy measurements safely while summarization workers may finish."""
        with self.lock:
            return dict(self.values)


def set_outcome(outcome: str, message: str = "", approval: str = "none") -> None:
    """Record a fixed outcome and an allowlisted Conventional Commit type."""
    if _active is None:
        return
    _active.outcome = outcome
    _active.approval = approval
    match = re.match(
        r"^(feat|fix|refactor|revert|style|docs|test|chore|build|ci|perf)"
        r"(?:\([^\n)]*\))?!?: ",
        message,
    )
    _active.commit_type = match.group(1) if match else "unknown"


def set_compression(tokens_before: int, tokens_after: int) -> None:
    """Remember the latest candidate prompt, not discarded compression passes."""
    if _active is not None:
        _active.compression = (tokens_before, tokens_after)


def record_attempt() -> None:
    """Count generation attempts, including empty responses retried by the CLI."""
    if _active is not None:
        _active.add("attempts")
        if _active.values["attempts"] > 1:
            _active.add("retries")


@contextmanager
def request(model: str, stage: str) -> Iterator[Callable[[Any], None]]:
    """Measure an AI request, including failures, without exporting its content."""
    metrics = _active
    if metrics is None:
        yield lambda _response: None
        return
    started = time.monotonic()
    metrics.add(f"{stage}.requests")
    compression = metrics.compression if stage == "generation" else (0, 0)

    def record(response: Any) -> None:
        try:
            import litellm  # pylint: disable=import-outside-toplevel

            usage = getattr(response, "usage", None)
            for source, target in (
                ("prompt_tokens", "input_tokens"),
                ("completion_tokens", "output_tokens"),
            ):
                value = getattr(usage, source, None)
                if isinstance(value, (int, float)):
                    metrics.add(f"{stage}.{target}", value)
            before, after = compression
            if before and 0 <= after <= before:
                saved = before - after
                metrics.add("compression.tokens_before", before)
                metrics.add("compression.tokens_after", after)
                metrics.add("compression.tokens_saved", saved)
                try:
                    input_cost, _ = litellm.cost_per_token(
                        model=model, prompt_tokens=saved, completion_tokens=0
                    )
                    metrics.add("compression.cost_saved_estimated", input_cost)
                except Exception:  # noqa: BLE001
                    logger.debug("Compression pricing is unavailable.")
            if usage is not None:
                cost = litellm.completion_cost(
                    completion_response=response, model=model
                )
                if cost is not None:
                    metrics.add("cost_estimated", cost)
                    metrics.add("cost_priced_requests")
        except Exception:  # noqa: BLE001
            logger.debug("Some AI usage or pricing metrics are unavailable.")

    try:
        yield record
    except Exception:
        metrics.add(f"{stage}.failures")
        raise
    finally:
        metrics.add(f"{stage}.duration", time.monotonic() - started)


# pylint: disable-next=too-many-locals
def _export(endpoint: str, metrics: RunMetrics) -> None:
    # pylint: disable=import-outside-toplevel
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.sdk.metrics import Counter as SDKCounter
    from opentelemetry.sdk.metrics import Histogram, MeterProvider, UpDownCounter
    from opentelemetry.sdk.metrics.export import (
        AggregationTemporality,
        InMemoryMetricReader,
    )
    from opentelemetry.sdk.resources import Resource

    reader = InMemoryMetricReader(
        preferred_temporality={
            SDKCounter: AggregationTemporality.DELTA,
            Histogram: AggregationTemporality.DELTA,
            UpDownCounter: AggregationTemporality.DELTA,
        }
    )
    provider = MeterProvider(
        metric_readers=[reader],
        resource=Resource({"service.name": "ai-prepare-commit-msg"}),
        shutdown_on_exit=False,
    )
    exporter = None
    try:
        meter = provider.get_meter("ai_prepare_commit_msg")
        attributes = {
            "outcome": metrics.outcome,
            "commit.type": metrics.commit_type,
            "approval": metrics.approval,
        }
        duration = time.monotonic() - metrics.started
        meter.create_counter("commit_assistant.invocations").add(1, attributes)
        measurements = metrics.snapshot()
        measurements["duration"] = duration
        baseline = os.getenv("AI_PREPARE_COMMIT_MANUAL_SECONDS", "120")
        try:
            baseline_seconds = float(baseline)
        except ValueError:
            baseline_seconds = 0
        if (
            metrics.outcome == "written"
            and math.isfinite(baseline_seconds)
            and baseline_seconds > 0
        ):
            measurements["manual_baseline"] = baseline_seconds
            measurements["time_saved_estimated"] = baseline_seconds - duration
        for name, value in measurements.items():
            unit = "1"
            if name.endswith("duration") or name in {
                "manual_baseline",
                "time_saved_estimated",
            }:
                unit = "s"
            elif "cost" in name and "requests" not in name:
                unit = "USD"
            full_name = f"commit_assistant.{name}"
            if name == "time_saved_estimated":
                meter.create_up_down_counter(full_name, unit=unit).add(
                    value, attributes
                )
            elif unit == "s":
                meter.create_histogram(full_name, unit=unit).record(value, attributes)
            else:
                meter.create_counter(full_name, unit=unit).add(value, attributes)
        data = reader.get_metrics_data()
        if data is not None:
            exporter = OTLPMetricExporter(endpoint=endpoint, timeout=1)
            exporter.export(data, timeout_millis=1000)
    finally:
        if exporter is not None:
            exporter.shutdown()
        provider.shutdown()


def instrument_cli(function: Callable[..., Any]) -> Callable[..., Any]:
    """Collect and export once at CLI exit only when explicitly configured."""

    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        global _active  # pylint: disable=global-statement
        endpoint = os.getenv(ENDPOINT_ENV, "").strip()
        if not endpoint:
            return function(*args, **kwargs)
        try:
            parsed = urlsplit(endpoint)
            if any(
                (
                    parsed.scheme not in {"http", "https"},
                    not parsed.hostname,
                    parsed.username,
                    parsed.password,
                    parsed.query,
                    parsed.fragment,
                )
            ):
                raise ValueError("Invalid telemetry endpoint")
        except ValueError:
            logger.warning("Telemetry disabled: endpoint must be an HTTP(S) URL.")
            return function(*args, **kwargs)
        metrics = RunMetrics()
        previous, _active = _active, metrics
        try:
            return function(*args, **kwargs)
        finally:
            _active = previous
            try:
                _export(endpoint, metrics)
            except Exception:  # noqa: BLE001
                logger.warning("Telemetry export unavailable; continuing without it.")

    return wrapped
