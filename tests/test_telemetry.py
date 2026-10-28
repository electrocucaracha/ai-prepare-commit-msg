"""Tests for opt-in metrics, savings accounting, and OTLP delivery."""

# pylint: disable=protected-access

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import litellm
import pytest
from click.testing import CliRunner
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (  # pylint: disable=no-name-in-module
    ExportMetricsServiceRequest,
)

import ai_prepare_commit_msg
from ai_prepare_commit_msg import telemetry


@pytest.fixture(autouse=True)
def isolated_telemetry(monkeypatch):
    """Prevent ambient telemetry configuration or state affecting tests."""
    monkeypatch.delenv(telemetry.ENDPOINT_ENV, raising=False)
    monkeypatch.delenv("AI_PREPARE_COMMIT_MANUAL_SECONDS", raising=False)
    monkeypatch.delenv("AI_PREPARE_COMMIT_AUTO_APPROVE", raising=False)
    monkeypatch.delenv("TYPESAFE_BASE_URL", raising=False)
    monkeypatch.setattr(telemetry, "_active", None)


@pytest.mark.parametrize("endpoint", [None, "", " ", "\n\t"])
def test_disabled_telemetry_never_exports(monkeypatch, endpoint):
    """Unset or blank endpoints disable telemetry regardless of other settings."""
    if endpoint is not None:
        monkeypatch.setenv(telemetry.ENDPOINT_ENV, endpoint)
    monkeypatch.setenv("AI_PREPARE_COMMIT_MANUAL_SECONDS", "90")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_METRICS_HEADERS", "X-Test=unused")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_METRICS_CERTIFICATE", "/unused/ca.pem")

    def unexpected_export(*_args):
        pytest.fail("Telemetry must be opt-in")

    monkeypatch.setattr(telemetry, "_export", unexpected_export)

    @telemetry.instrument_cli
    def operation():
        telemetry.record_attempt()
        with telemetry.request("private-model", "generation") as record:
            record(object())
        return "unchanged"

    assert operation() == "unchanged"
    assert telemetry._active is None


@pytest.mark.parametrize(
    "endpoint",
    ["file:///tmp/metrics", "https://user:secret@example.com", "not a URL"],
)
def test_invalid_endpoint_does_not_export(monkeypatch, endpoint):
    """Invalid endpoint configuration must not block normal execution."""
    monkeypatch.setenv(telemetry.ENDPOINT_ENV, endpoint)
    exported = []
    monkeypatch.setattr(telemetry, "_export", lambda *_args: exported.append(True))
    assert telemetry.instrument_cli(lambda: "ok")() == "ok"
    assert not exported


def test_usage_includes_summarization_and_retries(monkeypatch):
    """Unknown pricing must not discard compression or usage counts."""
    metrics = telemetry.RunMetrics()
    monkeypatch.setattr(telemetry, "_active", metrics)
    monkeypatch.setattr(litellm, "completion_cost", lambda **_kwargs: 0.02)
    monkeypatch.setattr(litellm, "cost_per_token", lambda **_kwargs: (0.001, 0))
    response = SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=10)
    )
    telemetry.set_compression(1000, 900)
    telemetry.set_compression(200, 100)
    telemetry.record_attempt()
    with telemetry.request("test", "generation") as record:
        record(response)
    with telemetry.request("test", "summarization") as record:
        record(response)
    telemetry.record_attempt()
    with pytest.raises(RuntimeError), telemetry.request("test", "generation"):
        raise RuntimeError("provider failure")
    assert metrics.values["generation.requests"] == 2
    assert metrics.values["generation.failures"] == 1
    assert metrics.values["summarization.requests"] == 1
    assert metrics.values["generation.input_tokens"] == 100
    assert metrics.values["summarization.output_tokens"] == 10
    assert metrics.values["compression.tokens_saved"] == 100
    assert metrics.values["compression.cost_saved_estimated"] == 0.001
    assert metrics.values["cost_estimated"] == 0.04
    assert metrics.values["cost_priced_requests"] == 2
    assert metrics.values["retries"] == 1


def test_unknown_pricing_preserves_token_savings(monkeypatch):
    """Providers without pricing metadata still contribute measured tokens."""
    metrics = telemetry.RunMetrics()
    monkeypatch.setattr(telemetry, "_active", metrics)

    def unavailable(**_kwargs):
        raise ValueError("unknown model")

    monkeypatch.setattr(litellm, "completion_cost", unavailable)
    monkeypatch.setattr(litellm, "cost_per_token", unavailable)
    telemetry.set_compression(200, 100)
    with telemetry.request("custom", "generation") as record:
        record(SimpleNamespace(usage=SimpleNamespace(prompt_tokens=100)))
    assert metrics.values["compression.tokens_saved"] == 100
    assert metrics.values["generation.input_tokens"] == 100
    assert "cost_estimated" not in metrics.values


@pytest.mark.parametrize("approved", [True, False])
def test_cli_outcomes_and_failed_export(monkeypatch, approved):
    """Exporter errors cannot change whether the user-approved message is written."""
    written = []
    exported = []
    repo = SimpleNamespace(
        get_diff_message=lambda: "private diff",
        write_commit_msg=written.append,
    )
    monkeypatch.setenv(telemetry.ENDPOINT_ENV, "http://localhost:4318/v1/metrics")
    monkeypatch.setattr(ai_prepare_commit_msg.git, "GitRepository", lambda _path: repo)
    monkeypatch.setattr(
        ai_prepare_commit_msg, "get_commit_msg", lambda *_args: "feat(secret): private"
    )
    monkeypatch.setattr(
        ai_prepare_commit_msg, "_confirm_generated_message", lambda _message: approved
    )

    def failed_export(_endpoint, metrics):
        exported.append(metrics)
        raise ConnectionError("unreachable receiver")

    monkeypatch.setattr(telemetry, "_export", failed_export)
    result = CliRunner().invoke(ai_prepare_commit_msg.cli, ["--model", "test"])
    assert result.exit_code == (0 if approved else 1)
    assert bool(written) == approved
    assert exported[0].outcome == ("written" if approved else "rejected")
    assert exported[0].approval == ("accepted" if approved else "rejected")
    assert exported[0].commit_type == "feat"
    assert telemetry._active is None


@pytest.mark.parametrize("outcome", ["written", "rejected", "oversized"])
def test_otlp_delivery_is_content_free(monkeypatch, outcome):
    """Decode an actual OTLP/HTTP export and check values and privacy boundaries."""
    received = []

    class Receiver(BaseHTTPRequestHandler):
        """Accept one binary OTLP payload without logging request details."""

        def do_POST(self):  # pylint: disable=invalid-name
            """Capture the request and acknowledge it."""
            received.append(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(200)
            self.end_headers()

        def log_message(self, _format, *args):  # pylint: disable=arguments-differ
            """Suppress HTTP server diagnostics."""

    server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("AI_PREPARE_COMMIT_MANUAL_SECONDS", "1")
    metrics = telemetry.RunMetrics()
    metrics.started -= 2
    metrics.outcome = outcome
    metrics.commit_type = "fix"
    metrics.approval = "auto"
    metrics.add("generation.input_tokens", 100)
    try:
        telemetry._export(f"http://127.0.0.1:{server.server_port}/v1/metrics", metrics)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    payload = ExportMetricsServiceRequest.FromString(received[0])
    resource = payload.resource_metrics[0]
    assert [attribute.key for attribute in resource.resource.attributes] == [
        "service.name"
    ]
    exported = {
        metric.name: metric
        for scope in resource.scope_metrics
        for metric in scope.metrics
    }
    assert exported["commit_assistant.invocations"].sum.data_points[0].as_int == 1
    tokens = exported["commit_assistant.generation.input_tokens"]
    assert tokens.sum.data_points[0].as_int == 100
    assert tokens.sum.aggregation_temporality == 1
    assert {attribute.key for attribute in tokens.sum.data_points[0].attributes} == {
        "outcome",
        "commit.type",
        "approval",
    }
    saved = exported.get("commit_assistant.time_saved_estimated")
    if outcome == "written":
        assert saved.sum.data_points[0].as_double < 0
    else:
        assert saved is None
