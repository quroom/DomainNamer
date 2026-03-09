from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Iterable, Literal, Protocol

AvailabilityStatus = Literal["available", "unavailable", "uncertain"]
ProviderOutcome = Literal["available", "unavailable", "error"]
ErrorCode = Literal["timeout", "rate_limited", "error"]


@dataclass
class ProviderCheckResult:
    provider: str
    outcome: ProviderOutcome
    latency_ms: int
    ip: str
    error_code: ErrorCode | None = None
    source_quality: float = 0.8
    request_meta: dict[str, object] = field(default_factory=dict)


@dataclass
class AvailabilityDecision:
    status: AvailabilityStatus
    reason: str | None
    confidence: float
    evidence: list[dict[str, object]]
    checked_at: str


class AvailabilityProvider(Protocol):
    name: str
    source_quality: float

    def check(self, domain: str, ip: str) -> ProviderCheckResult:
        """Check the given domain from the given outbound ip."""


@dataclass
class RdapProvider:
    name: str = "rdap"
    source_quality: float = 0.95
    endpoint_template: str = "https://rdap.org/domain/{domain}"
    timeout_ms: int = 1200
    user_agent: str = "DomainNamer/1.0"

    def check(self, domain: str, ip: str) -> ProviderCheckResult:
        started = time.monotonic()
        endpoint = self.endpoint_template.format(domain=domain)
        request = urllib.request.Request(
            endpoint,
            headers={"User-Agent": self.user_agent, "Accept": "application/rdap+json, application/json"},
        )
        meta = {"endpoint": endpoint, "protocol": "rdap-http", "via_ip": ip}
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_ms / 1000) as response:
                payload = response.read().decode("utf-8", errors="ignore")
                latency_ms = int((time.monotonic() - started) * 1000)
                if response.status == 429:
                    return ProviderCheckResult(
                        provider=self.name,
                        outcome="error",
                        error_code="rate_limited",
                        latency_ms=latency_ms,
                        ip=ip,
                        source_quality=self.source_quality,
                        request_meta=meta,
                    )
                if response.status >= 500:
                    return ProviderCheckResult(
                        provider=self.name,
                        outcome="error",
                        error_code="error",
                        latency_ms=latency_ms,
                        ip=ip,
                        source_quality=self.source_quality,
                        request_meta=meta,
                    )
                outcome = "unavailable"
                if self._looks_available(payload):
                    outcome = "available"
                return ProviderCheckResult(
                    provider=self.name,
                    outcome=outcome,
                    latency_ms=latency_ms,
                    ip=ip,
                    source_quality=self.source_quality,
                    request_meta=meta,
                )
        except urllib.error.HTTPError as exc:
            latency_ms = int((time.monotonic() - started) * 1000)
            if exc.code == 404:
                return ProviderCheckResult(
                    provider=self.name,
                    outcome="available",
                    latency_ms=latency_ms,
                    ip=ip,
                    source_quality=self.source_quality,
                    request_meta=meta,
                )
            error_code: ErrorCode = "rate_limited" if exc.code == 429 else "error"
            return ProviderCheckResult(
                provider=self.name,
                outcome="error",
                error_code=error_code,
                latency_ms=latency_ms,
                ip=ip,
                source_quality=self.source_quality,
                request_meta=meta,
            )
        except socket.timeout:
            latency_ms = int((time.monotonic() - started) * 1000)
            return ProviderCheckResult(
                provider=self.name,
                outcome="error",
                error_code="timeout",
                latency_ms=latency_ms,
                ip=ip,
                source_quality=self.source_quality,
                request_meta=meta,
            )
        except urllib.error.URLError as exc:
            latency_ms = int((time.monotonic() - started) * 1000)
            error_code: ErrorCode = "timeout" if isinstance(getattr(exc, "reason", None), socket.timeout) else "error"
            return ProviderCheckResult(
                provider=self.name,
                outcome="error",
                error_code=error_code,
                latency_ms=latency_ms,
                ip=ip,
                source_quality=self.source_quality,
                request_meta=meta,
            )

    @staticmethod
    def _looks_available(payload: str) -> bool:
        lower_payload = payload.lower()
        if "not found" in lower_payload or "no object found" in lower_payload:
            return True
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return False
        if isinstance(data, dict) and data.get("errorCode") == 404:
            return True
        return False


@dataclass
class WhoisProvider:
    name: str = "whois"
    source_quality: float = 0.90
    timeout_ms: int = 1200
    default_server: str = "whois.verisign-grs.com"
    port: int = 43

    def check(self, domain: str, ip: str) -> ProviderCheckResult:
        started = time.monotonic()
        meta = {
            "server": self.default_server,
            "protocol": "whois",
            "port": self.port,
            "via_ip": ip,
        }
        try:
            with socket.create_connection(
                (self.default_server, self.port),
                timeout=self.timeout_ms / 1000,
            ) as conn:
                conn.sendall(f"{domain}\r\n".encode("utf-8"))
                payload = self._recv_all(conn)
            latency_ms = int((time.monotonic() - started) * 1000)
            outcome = "available" if self._looks_available(payload) else "unavailable"
            return ProviderCheckResult(
                provider=self.name,
                outcome=outcome,
                latency_ms=latency_ms,
                ip=ip,
                source_quality=self.source_quality,
                request_meta=meta,
            )
        except socket.timeout:
            latency_ms = int((time.monotonic() - started) * 1000)
            return ProviderCheckResult(
                provider=self.name,
                outcome="error",
                error_code="timeout",
                latency_ms=latency_ms,
                ip=ip,
                source_quality=self.source_quality,
                request_meta=meta,
            )
        except OSError:
            latency_ms = int((time.monotonic() - started) * 1000)
            return ProviderCheckResult(
                provider=self.name,
                outcome="error",
                error_code="error",
                latency_ms=latency_ms,
                ip=ip,
                source_quality=self.source_quality,
                request_meta=meta,
            )

    @staticmethod
    def _recv_all(conn: socket.socket) -> str:
        chunks: list[bytes] = []
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if len(chunks) > 128:
                break
        return b"".join(chunks).decode("utf-8", errors="ignore")

    @staticmethod
    def _looks_available(payload: str) -> bool:
        normalized = payload.lower()
        return (
            "no match for" in normalized
            or "not found" in normalized
            or "status: free" in normalized
        )


@dataclass
class IpHealth:
    ip: str
    successes: int = 0
    errors: int = 0
    rate_limited_count: int = 0
    timeout_count: int = 0
    consecutive_429: int = 0
    consecutive_timeout: int = 0
    cooldown_level: int = 0
    cooldown_until: datetime | None = None
    latency_samples: list[int] = field(default_factory=list)

    def is_available(self, now: datetime) -> bool:
        return not self.cooldown_until or now >= self.cooldown_until


class IpPool:
    def __init__(
        self,
        ips: Iterable[str],
        cooldown_base_sec: int = 60,
        cooldown_max_sec: int = 600,
    ) -> None:
        self._ips = [IpHealth(ip=ip) for ip in ips]
        self.cooldown_base_sec = cooldown_base_sec
        self.cooldown_max_sec = cooldown_max_sec

    @property
    def ips(self) -> list[IpHealth]:
        return self._ips

    def select_ip(self, now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        candidates = [entry for entry in self._ips if entry.is_available(now)]
        if not candidates:
            # If every ip is cooling down, use the soonest to recover.
            candidates = sorted(
                self._ips,
                key=lambda item: item.cooldown_until or datetime.min.replace(tzinfo=timezone.utc),
            )
        chosen = max(candidates, key=lambda item: self.health_score(item, now))
        return chosen.ip

    def get(self, ip: str) -> IpHealth:
        for item in self._ips:
            if item.ip == ip:
                return item
        raise KeyError(f"ip {ip} not found")

    def record(self, result: ProviderCheckResult, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        item = self.get(result.ip)
        item.latency_samples.append(result.latency_ms)
        if len(item.latency_samples) > 20:
            item.latency_samples = item.latency_samples[-20:]

        if result.outcome != "error":
            item.successes += 1
            item.consecutive_429 = 0
            item.consecutive_timeout = 0
            item.cooldown_level = max(0, item.cooldown_level - 1)
            return

        item.errors += 1
        if result.error_code == "rate_limited":
            item.rate_limited_count += 1
            item.consecutive_429 += 1
            item.consecutive_timeout = 0
            if item.consecutive_429 >= 3:
                self._apply_cooldown(item, now)
        elif result.error_code == "timeout":
            item.timeout_count += 1
            item.consecutive_timeout += 1
            item.consecutive_429 = 0
            if item.consecutive_timeout >= 4:
                self._apply_cooldown(item, now)
        else:
            item.consecutive_429 = 0
            item.consecutive_timeout = 0

    def _apply_cooldown(self, item: IpHealth, now: datetime) -> None:
        item.cooldown_level += 1
        duration = min(self.cooldown_base_sec * (2 ** (item.cooldown_level - 1)), self.cooldown_max_sec)
        item.cooldown_until = now + timedelta(seconds=duration)

    def health_score(self, item: IpHealth, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        total = item.successes + item.errors
        err_rate = (item.errors / total) if total else 0.0
        rate429 = (item.rate_limited_count / total) if total else 0.0
        timeout_rate = (item.timeout_count / total) if total else 0.0
        avg_latency = mean(item.latency_samples) if item.latency_samples else 300.0
        latency_penalty = min(max((avg_latency - 800.0) / 1200.0, 0.0), 1.0)
        cooldown_penalty = 0.25 if item.cooldown_until and item.cooldown_until > now else 0.0
        score = 1.0 - (0.4 * err_rate) - (0.3 * rate429) - (0.2 * timeout_rate) - (0.1 * latency_penalty) - cooldown_penalty
        return max(min(score, 1.0), 0.0)


@dataclass
class AvailabilityConfig:
    timeout_ms: int = 1200
    budget_timeout_ms: int = 1800
    quorum_min: int = 2
    uncertain_confidence_cap: float = 0.49
    confidence_weight_agreement: float = 0.45
    confidence_weight_source: float = 0.20
    confidence_weight_health: float = 0.15
    confidence_weight_freshness: float = 0.10
    confidence_weight_error: float = 0.10
    fallback_to_legacy: bool = True
    shadow_mode: bool = False
    max_attempts_per_provider: int = 3


class InMemoryTelemetry:
    def __init__(self) -> None:
        self.total_checks = 0
        self.uncertain_checks = 0
        self.false_available_reports = 0
        self.latencies_ms: list[int] = []
        self.provider_errors: dict[str, int] = {}
        self.provider_calls: dict[str, int] = {}

    def record(self, decision: AvailabilityDecision, provider_results: list[ProviderCheckResult]) -> None:
        self.total_checks += 1
        if decision.status == "uncertain":
            self.uncertain_checks += 1
        request_latency = max((result.latency_ms for result in provider_results), default=0)
        self.latencies_ms.append(request_latency)
        if len(self.latencies_ms) > 1000:
            self.latencies_ms = self.latencies_ms[-1000:]
        for result in provider_results:
            self.provider_calls[result.provider] = self.provider_calls.get(result.provider, 0) + 1
            if result.outcome == "error":
                self.provider_errors[result.provider] = self.provider_errors.get(result.provider, 0) + 1

    def report_false_available(self) -> None:
        self.false_available_reports += 1

    def snapshot(self) -> dict[str, object]:
        latency_sorted = sorted(self.latencies_ms)
        p95_index = int(len(latency_sorted) * 0.95) - 1 if latency_sorted else -1
        p95_latency = latency_sorted[max(p95_index, 0)] if latency_sorted else 0
        provider_error_rate = {}
        for provider, calls in self.provider_calls.items():
            errors = self.provider_errors.get(provider, 0)
            provider_error_rate[provider] = (errors / calls) if calls else 0.0
        return {
            "false_available_rate": (self.false_available_reports / self.total_checks) if self.total_checks else 0.0,
            "uncertain_rate": (self.uncertain_checks / self.total_checks) if self.total_checks else 0.0,
            "p95_latency_ms": p95_latency,
            "provider_error_rate": provider_error_rate,
        }


def evaluate_quorum(results: Iterable[ProviderCheckResult], quorum_min: int = 2) -> AvailabilityStatus:
    available_count = 0
    unavailable_count = 0
    for result in results:
        if result.outcome == "available":
            available_count += 1
        elif result.outcome == "unavailable":
            unavailable_count += 1
    if unavailable_count >= quorum_min:
        return "unavailable"
    if available_count >= quorum_min and unavailable_count == 0:
        return "available"
    return "uncertain"


def compute_confidence(
    status: AvailabilityStatus,
    results: Iterable[ProviderCheckResult],
    ip_pool: IpPool,
    config: AvailabilityConfig,
    now: datetime | None = None,
) -> float:
    now = now or datetime.now(timezone.utc)
    result_list = list(results)
    if not result_list:
        return 0.0

    non_error = [item for item in result_list if item.outcome != "error"]
    outcomes = {item.outcome for item in non_error}
    if len(non_error) >= 2 and len(outcomes) == 1:
        agreement_score = 1.0
    elif status in ("available", "unavailable"):
        agreement_score = 0.75
    else:
        agreement_score = 0.20

    source_quality = mean(item.source_quality for item in result_list)
    ip_health_score = mean(ip_pool.health_score(ip_pool.get(item.ip), now) for item in result_list)
    max_latency = max(item.latency_ms for item in result_list)
    if max_latency <= 800:
        freshness = 1.0
    elif max_latency <= 1200:
        freshness = 0.8
    elif max_latency <= 1800:
        freshness = 0.6
    else:
        freshness = 0.4
    error_penalty = sum(1 for item in result_list if item.outcome == "error") / len(result_list)

    raw = (
        config.confidence_weight_agreement * agreement_score
        + config.confidence_weight_source * source_quality
        + config.confidence_weight_health * ip_health_score
        + config.confidence_weight_freshness * freshness
        - config.confidence_weight_error * error_penalty
    )
    confidence = min(max(raw, 0.0), 1.0)
    if status == "uncertain":
        return min(confidence, config.uncertain_confidence_cap)
    return confidence


@dataclass
class RuleBasedProvider:
    name: str
    source_quality: float = 0.8
    blocked_domains: set[str] = field(default_factory=set)
    timeout_domains: set[str] = field(default_factory=set)
    rate_limited_domains: set[str] = field(default_factory=set)

    def check(self, domain: str, ip: str) -> ProviderCheckResult:
        if domain in self.rate_limited_domains:
            return ProviderCheckResult(
                provider=self.name,
                outcome="error",
                error_code="rate_limited",
                latency_ms=900,
                ip=ip,
                source_quality=self.source_quality,
            )
        if domain in self.timeout_domains:
            return ProviderCheckResult(
                provider=self.name,
                outcome="error",
                error_code="timeout",
                latency_ms=1500,
                ip=ip,
                source_quality=self.source_quality,
            )
        outcome: ProviderOutcome = "unavailable" if domain in self.blocked_domains else "available"
        return ProviderCheckResult(
            provider=self.name,
            outcome=outcome,
            latency_ms=350,
            ip=ip,
            source_quality=self.source_quality,
        )


class AvailabilityOrchestrator:
    def __init__(
        self,
        providers: list[AvailabilityProvider],
        ip_pool: IpPool,
        config: AvailabilityConfig | None = None,
        telemetry: InMemoryTelemetry | None = None,
    ) -> None:
        self.providers = providers
        self.ip_pool = ip_pool
        self.config = config or AvailabilityConfig()
        self.telemetry = telemetry or InMemoryTelemetry()

    def check(self, domain: str, checked_at: datetime | None = None) -> AvailabilityDecision:
        checked_at = checked_at or datetime.now(timezone.utc)
        provider_results: list[ProviderCheckResult] = []
        for provider in self.providers:
            provider_results.append(self._check_provider_with_failover(provider, domain, checked_at))
        status = evaluate_quorum(provider_results, quorum_min=self.config.quorum_min)
        confidence = compute_confidence(status, provider_results, self.ip_pool, self.config, now=checked_at)
        reason = None
        if status == "unavailable":
            reason = "already_registered"
        elif status == "uncertain":
            reason = "insufficient_quorum"
        evidence = [
            {
                "provider": result.provider,
                "outcome": result.outcome,
                "error_code": result.error_code,
                "latency_ms": result.latency_ms,
                "ip": result.ip,
                "request_meta": result.request_meta,
            }
            for result in provider_results
        ]
        decision = AvailabilityDecision(
            status=status,
            reason=reason,
            confidence=confidence,
            evidence=evidence,
            checked_at=checked_at.isoformat(),
        )
        self.telemetry.record(decision, provider_results)
        return decision

    def _check_provider_with_failover(
        self, provider: AvailabilityProvider, domain: str, now: datetime
    ) -> ProviderCheckResult:
        max_attempts = self.config.max_attempts_per_provider
        latest_error: ProviderCheckResult | None = None
        for _ in range(max_attempts):
            ip = self.ip_pool.select_ip(now)
            result = provider.check(domain, ip)
            self.ip_pool.record(result, now)
            if result.outcome != "error":
                return result
            latest_error = result
            if result.error_code not in ("timeout", "rate_limited"):
                break
        return latest_error or ProviderCheckResult(
            provider=provider.name,
            outcome="error",
            error_code="error",
            latency_ms=self.config.timeout_ms,
            ip=self.ip_pool.select_ip(now),
            source_quality=provider.source_quality,
        )
