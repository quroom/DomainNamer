import json
from datetime import datetime, timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from .models import DomainAlertEvent, DomainWatchItem, WatchlistCheckJob
from .services.availability import (
    AvailabilityDecision,
    AvailabilityConfig,
    AvailabilityOrchestrator,
    IpPool,
    ProviderCheckResult,
    RdapProvider,
    WhoisProvider,
    compute_confidence,
    evaluate_quorum,
)

from .services.domain_recommender import normalize_candidate, recommend_domains
from .services.watchlist import run_watchlist_check

User = get_user_model()


class SequenceProvider:
    def __init__(self, name: str, sequence, source_quality: float = 0.9):
        self.name = name
        self.sequence = list(sequence)
        self.source_quality = source_quality

    def check(self, domain: str, ip: str) -> ProviderCheckResult:
        outcome, error_code, latency = self.sequence.pop(0) if self.sequence else ("error", "error", 500)
        return ProviderCheckResult(
            provider=self.name,
            outcome=outcome,
            error_code=error_code,
            latency_ms=latency,
            ip=ip,
            source_quality=self.source_quality,
        )


class FakeHttpResponse:
    def __init__(self, status: int, body: str):
        self.status = status
        self._body = body.encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeSocketConnection:
    def __init__(self, payload: str):
        self.payload = payload.encode("utf-8")
        self.sent = b""
        self._reads = 0

    def sendall(self, data: bytes):
        self.sent += data

    def recv(self, _size: int):
        if self._reads == 0:
            self._reads += 1
            return self.payload
        return b""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DomainRecommenderServiceTests(TestCase):
    def test_normalize_candidate_removes_case_spacing_and_hyphen(self):
        self.assertEqual(normalize_candidate(" My-App Name.COM "), "myappname")

    def test_recommend_domains_marks_duplicate_after_normalization(self):
        data = recommend_domains(["my-app.com", "My App.com"])
        self.assertEqual(data["results"][0]["status"], "available")
        self.assertEqual(data["results"][1]["status"], "duplicate")
        self.assertEqual(data["results"][1]["reason"], "duplicate_candidate")
        self.assertIn("confidence", data["results"][1])
        self.assertIn("evidence", data["results"][1])
        self.assertIn("checked_at", data["results"][1])

    def test_recommend_domains_generates_alternatives_for_unavailable(self):
        unavailable = {"brandhub.com", "brandhubgo.com"}

        def checker(domain: str) -> bool:
            return domain not in unavailable

        data = recommend_domains(["brandhub.com"], availability_checker=checker)
        result = data["results"][0]

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "already_registered")
        self.assertGreater(len(result["alternatives"]), 0)
        self.assertNotIn("brandhubgo.com", result["alternatives"])
        self.assertIn("confidence", result)
        self.assertIn("evidence", result)

    def test_recommend_domains_prioritizes_tld_fallback_for_unavailable_dotcom(self):
        unavailable = {"brandhub.com"}

        def checker(domain: str) -> bool:
            return domain not in unavailable

        data = recommend_domains(
            ["brandhub.com"],
            availability_checker=checker,
            preferred_tlds=("com", "kr", "io"),
        )
        alternatives = data["results"][0]["alternatives"]
        self.assertGreaterEqual(len(alternatives), 2)
        self.assertEqual(alternatives[0], "brandhub.kr")
        self.assertEqual(alternatives[1], "brandhub.io")


class WatchlistServiceTests(TestCase):
    @staticmethod
    def _decision(status: str) -> AvailabilityDecision:
        reason = None if status == "available" else "already_registered"
        if status == "uncertain":
            reason = "insufficient_quorum"
        return AvailabilityDecision(
            status=status, reason=reason, confidence=0.8, evidence=[], checked_at=datetime.now(timezone.utc).isoformat()
        )

    def test_transition_unavailable_to_available_creates_single_alert(self):
        item = DomainWatchItem.objects.create(base_name="quroom", tlds=["com"])

        statuses = iter(["unavailable", "available", "available"])

        def resolver(_domain: str):
            return self._decision(next(statuses))

        run_watchlist_check([item], resolver)
        run_watchlist_check([item], resolver)
        run_watchlist_check([item], resolver)

        self.assertEqual(DomainAlertEvent.objects.count(), 1)
        alert = DomainAlertEvent.objects.first()
        self.assertEqual(alert.domain, "quroom.com")
        self.assertEqual(alert.previous_status, "unavailable")
        self.assertEqual(alert.current_status, "available")


class AvailabilityDecisionTests(TestCase):
    def test_quorum_decisions(self):
        unavailable = evaluate_quorum(
            [
                ProviderCheckResult("a", "unavailable", 300, "1.1.1.1"),
                ProviderCheckResult("b", "unavailable", 320, "1.1.1.2"),
                ProviderCheckResult("c", "available", 310, "1.1.1.3"),
            ]
        )
        self.assertEqual(unavailable, "unavailable")

        available = evaluate_quorum(
            [
                ProviderCheckResult("a", "available", 300, "1.1.1.1"),
                ProviderCheckResult("b", "available", 320, "1.1.1.2"),
                ProviderCheckResult("c", "error", 1200, "1.1.1.3", "timeout"),
            ]
        )
        self.assertEqual(available, "available")

        uncertain = evaluate_quorum(
            [
                ProviderCheckResult("a", "available", 300, "1.1.1.1"),
                ProviderCheckResult("b", "unavailable", 320, "1.1.1.2"),
                ProviderCheckResult("c", "error", 1200, "1.1.1.3", "timeout"),
            ]
        )
        self.assertEqual(uncertain, "uncertain")

    def test_confidence_thresholds_and_uncertain_cap(self):
        pool = IpPool(["10.0.0.1", "10.0.0.2", "10.0.0.3"])
        config = AvailabilityConfig()

        high = compute_confidence(
            "available",
            [
                ProviderCheckResult("a", "available", 250, "10.0.0.1", source_quality=1.0),
                ProviderCheckResult("b", "available", 260, "10.0.0.2", source_quality=1.0),
                ProviderCheckResult("c", "available", 270, "10.0.0.3", source_quality=1.0),
            ],
            pool,
            config,
        )
        self.assertGreaterEqual(high, 0.90)

        medium = compute_confidence(
            "available",
            [
                ProviderCheckResult("a", "available", 450, "10.0.0.1", source_quality=0.9),
                ProviderCheckResult("b", "available", 500, "10.0.0.2", source_quality=0.9),
                ProviderCheckResult("c", "error", 1300, "10.0.0.3", "timeout", source_quality=0.9),
            ],
            pool,
            config,
        )
        self.assertGreaterEqual(medium, 0.60)
        self.assertLess(medium, 0.90)

        low = compute_confidence(
            "uncertain",
            [
                ProviderCheckResult("a", "available", 900, "10.0.0.1", source_quality=0.9),
                ProviderCheckResult("b", "unavailable", 920, "10.0.0.2", source_quality=0.9),
                ProviderCheckResult("c", "error", 1500, "10.0.0.3", "timeout", source_quality=0.9),
            ],
            pool,
            config,
        )
        self.assertLessEqual(low, 0.49)


class RealProviderParsingTests(TestCase):
    @patch("domainamer.services.availability.urllib.request.urlopen")
    def test_rdap_provider_parses_404_as_available(self, mock_urlopen):
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError(
            url="https://rdap.org/domain/free.com",
            code=404,
            msg="not found",
            hdrs=None,
            fp=None,
        )
        provider = RdapProvider()
        result = provider.check("free.com", "10.0.0.1")
        self.assertEqual(result.outcome, "available")

    @patch("domainamer.services.availability.urllib.request.urlopen")
    def test_rdap_provider_parses_registered_as_unavailable(self, mock_urlopen):
        mock_urlopen.return_value = FakeHttpResponse(
            200,
            '{"objectClassName":"domain","ldhName":"taken.com"}',
        )
        provider = RdapProvider()
        result = provider.check("taken.com", "10.0.0.1")
        self.assertEqual(result.outcome, "unavailable")

    @patch("domainamer.services.availability.socket.create_connection")
    def test_whois_provider_parses_not_found_as_available(self, mock_conn):
        mock_conn.return_value = FakeSocketConnection("No match for domain \"FREE.COM\"")
        provider = WhoisProvider()
        result = provider.check("free.com", "10.0.0.1")
        self.assertEqual(result.outcome, "available")

    @patch("domainamer.services.availability.socket.create_connection")
    def test_whois_provider_parses_registered_as_unavailable(self, mock_conn):
        mock_conn.return_value = FakeSocketConnection("Domain Name: TAKEN.COM\nRegistrar: Example")
        provider = WhoisProvider()
        result = provider.check("taken.com", "10.0.0.1")
        self.assertEqual(result.outcome, "unavailable")


class IpPoolBehaviorTests(TestCase):
    def test_cooldown_trigger_for_rate_limit_and_timeout(self):
        pool = IpPool(["10.0.0.1"])
        now = datetime.now(timezone.utc)
        for _ in range(3):
            pool.record(
                ProviderCheckResult("a", "error", 1000, "10.0.0.1", "rate_limited"),
                now,
            )
        self.assertFalse(pool.get("10.0.0.1").is_available(now))

        pool = IpPool(["10.0.0.1"])
        for _ in range(4):
            pool.record(
                ProviderCheckResult("a", "error", 1500, "10.0.0.1", "timeout"),
                now,
            )
        self.assertFalse(pool.get("10.0.0.1").is_available(now))

    def test_ip_selection_excludes_cooldown_ip(self):
        pool = IpPool(["10.0.0.1", "10.0.0.2"])
        now = datetime.now(timezone.utc)
        for _ in range(3):
            pool.record(
                ProviderCheckResult("a", "error", 1000, "10.0.0.1", "rate_limited"),
                now,
            )
        selected = pool.select_ip(now)
        self.assertEqual(selected, "10.0.0.2")


class AvailabilityOrchestratorTests(TestCase):
    def test_failover_after_timeout_or_rate_limit(self):
        provider = SequenceProvider(
            "p1",
            [
                ("error", "timeout", 1500),
                ("error", "rate_limited", 900),
                ("available", None, 320),
            ],
        )
        orchestrator = AvailabilityOrchestrator(
            providers=[provider],
            ip_pool=IpPool(["10.0.0.1", "10.0.0.2", "10.0.0.3"]),
        )
        decision = orchestrator.check("example.com")
        self.assertEqual(decision.status, "uncertain")
        self.assertLessEqual(decision.confidence, 0.49)

    def test_conflicting_provider_results_return_uncertain(self):
        providers = [
            SequenceProvider("a", [("available", None, 300)]),
            SequenceProvider("b", [("unavailable", None, 350)]),
            SequenceProvider("c", [("error", "timeout", 1400)]),
        ]
        orchestrator = AvailabilityOrchestrator(
            providers=providers,
            ip_pool=IpPool(["10.0.0.1", "10.0.0.2", "10.0.0.3"]),
        )
        payload = recommend_domains(
            ["conflict-domain"],
            availability_resolver=orchestrator.check,
        )
        result = payload["results"][0]
        self.assertEqual(result["status"], "uncertain")
        self.assertLessEqual(result["confidence"], 0.49)
        self.assertGreater(len(result["evidence"]), 0)

    def test_failure_injection_never_leaks_false_available(self):
        providers = [
            SequenceProvider("a", [("available", None, 300)]),
            SequenceProvider("b", [("error", "timeout", 1500)]),
            SequenceProvider("c", [("error", "rate_limited", 900)]),
        ]
        orchestrator = AvailabilityOrchestrator(
            providers=providers,
            ip_pool=IpPool(["10.0.0.1", "10.0.0.2", "10.0.0.3"]),
        )
        decision = orchestrator.check("spiky-domain.com")
        self.assertNotEqual(decision.status, "available")

    def test_telemetry_snapshot_contains_required_metrics(self):
        providers = [
            SequenceProvider("a", [("available", None, 300)]),
            SequenceProvider("b", [("available", None, 310)]),
            SequenceProvider("c", [("available", None, 320)]),
        ]
        orchestrator = AvailabilityOrchestrator(
            providers=providers,
            ip_pool=IpPool(["10.0.0.1", "10.0.0.2", "10.0.0.3"]),
        )
        orchestrator.check("ok-domain.com")
        metrics = orchestrator.telemetry.snapshot()
        self.assertIn("false_available_rate", metrics)
        self.assertIn("uncertain_rate", metrics)
        self.assertIn("p95_latency_ms", metrics)
        self.assertIn("provider_error_rate", metrics)


class DomainRecommendationViewTests(TestCase):
    @override_settings(DOMAIN_HARDENED_CHECK_ENABLED=True, DOMAIN_SHADOW_MODE=False)
    def test_recommend_endpoint_returns_hardened_contract(self):
        response = self.client.post(
            "/domainamer/recommend/",
            data=json.dumps({"candidates": ["my-app", "my app", "brandhub"]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("results", payload)
        self.assertEqual(len(payload["results"]), 3)
        for item in payload["results"]:
            self.assertIn("candidate", item)
            self.assertIn("status", item)
            self.assertIn("reason", item)
            self.assertIn("alternatives", item)
            self.assertIn("confidence", item)
            self.assertIn("evidence", item)
            self.assertIn("checked_at", item)

    @override_settings(
        DOMAIN_HARDENED_CHECK_ENABLED=True,
        DOMAIN_SHADOW_MODE=True,
        DOMAIN_TIMEOUT_DOMAINS=["flaky.com"],
    )
    def test_shadow_mode_keeps_legacy_visible_response(self):
        response = self.client.post(
            "/domainamer/recommend/",
            data=json.dumps({"candidates": ["flaky"]}),
            content_type="application/json",
        )
        payload = response.json()
        self.assertEqual(payload["results"][0]["status"], "available")

    @override_settings(DOMAIN_HARDENED_CHECK_ENABLED=False)
    def test_feature_flag_can_disable_hardened_check(self):
        response = self.client.post(
            "/domainamer/recommend/",
            data=json.dumps({"candidates": ["takenbrand"]}),
            content_type="application/json",
        )
        payload = response.json()
        self.assertEqual(payload["results"][0]["status"], "available")

    @override_settings(DOMAIN_HARDENED_CHECK_ENABLED=True, DOMAIN_REAL_PROVIDER_ENABLED=True)
    @patch("domainamer.services.availability.urllib.request.urlopen")
    @patch("domainamer.services.availability.socket.create_connection")
    def test_real_provider_mode_success(self, mock_conn, mock_urlopen):
        mock_urlopen.return_value = FakeHttpResponse(404, '{"errorCode":404}')
        mock_conn.return_value = FakeSocketConnection("No match for domain \"FREE.COM\"")
        response = self.client.post(
            "/domainamer/recommend/",
            data=json.dumps({"candidates": ["free"]}),
            content_type="application/json",
        )
        payload = response.json()
        self.assertEqual(payload["results"][0]["status"], "available")
        self.assertGreater(len(payload["results"][0]["evidence"]), 0)

    @override_settings(DOMAIN_HARDENED_CHECK_ENABLED=True, DOMAIN_REAL_PROVIDER_ENABLED=True)
    @patch("domainamer.services.availability.urllib.request.urlopen")
    @patch("domainamer.services.availability.socket.create_connection")
    def test_real_provider_mode_conflict_returns_uncertain(self, mock_conn, mock_urlopen):
        mock_urlopen.return_value = FakeHttpResponse(
            200,
            '{"objectClassName":"domain","ldhName":"conflict.com"}',
        )
        mock_conn.return_value = FakeSocketConnection("No match for domain \"CONFLICT.COM\"")
        response = self.client.post(
            "/domainamer/recommend/",
            data=json.dumps({"candidates": ["conflict"]}),
            content_type="application/json",
        )
        payload = response.json()
        self.assertEqual(payload["results"][0]["status"], "uncertain")

    @override_settings(
        DOMAIN_HARDENED_CHECK_ENABLED=True,
        DOMAIN_REAL_PROVIDER_ENABLED=True,
        DOMAIN_SHADOW_MODE=True,
    )
    @patch("domainamer.services.availability.urllib.request.urlopen")
    @patch("domainamer.services.availability.socket.create_connection")
    def test_shadow_mode_with_real_providers_keeps_legacy_response(self, mock_conn, mock_urlopen):
        mock_urlopen.return_value = FakeHttpResponse(
            200,
            '{"objectClassName":"domain","ldhName":"taken.com"}',
        )
        mock_conn.return_value = FakeSocketConnection("Domain Name: TAKEN.COM")
        response = self.client.post(
            "/domainamer/recommend/",
            data=json.dumps({"candidates": ["taken"]}),
            content_type="application/json",
        )
        payload = response.json()
        self.assertEqual(payload["results"][0]["status"], "available")

    @override_settings(DOMAIN_HARDENED_CHECK_ENABLED=True, DOMAIN_HARDENED_FALLBACK_TO_LEGACY=True)
    def test_fallback_to_legacy_on_hardened_failure(self):
        with patch("domainamer.views._build_orchestrator", side_effect=RuntimeError("boom")):
            response = self.client.post(
                "/domainamer/recommend/",
                data=json.dumps({"candidates": ["anyname"]}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)


class WatchlistApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw-12345")
        self.other = User.objects.create_user(username="bob", password="pw-12345")

    def test_watchlist_requires_authentication(self):
        create_response = self.client.post(
            "/domainamer/watchlist/",
            data=json.dumps({"base_name": "quroom", "tlds": ["com"]}),
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 401)

    @override_settings(DOMAIN_HARDENED_CHECK_ENABLED=False)
    def test_watchlist_create_and_owner_scoped_list(self):
        self.client.force_login(self.user)
        create_response = self.client.post(
            "/domainamer/watchlist/",
            data=json.dumps({"base_name": "quroom", "tlds": ["com", "kr"]}),
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 201)
        payload = create_response.json()
        self.assertEqual(payload["base_name"], "quroom")
        self.assertEqual(payload["tlds"], ["com", "kr"])

        list_response = self.client.get("/domainamer/watchlist/")
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()
        self.assertEqual(len(list_payload["items"]), 1)

        self.client.logout()
        self.client.force_login(self.other)
        other_list = self.client.get("/domainamer/watchlist/")
        self.assertEqual(other_list.status_code, 200)
        self.assertEqual(len(other_list.json()["items"]), 0)

    @override_settings(DOMAIN_HARDENED_CHECK_ENABLED=False)
    def test_watchlist_duplicate_registration_is_rejected(self):
        self.client.force_login(self.user)
        first = self.client.post(
            "/domainamer/watchlist/",
            data=json.dumps({"base_name": "quroom", "tlds": ["kr", "com"]}),
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 201)

        second = self.client.post(
            "/domainamer/watchlist/",
            data=json.dumps({"base_name": "quroom", "tlds": ["com", "kr"]}),
            content_type="application/json",
        )
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["error"], "watch_duplicate")

    @override_settings(DOMAIN_HARDENED_CHECK_ENABLED=False, WATCHLIST_MAX_ITEMS_PER_USER=1)
    def test_watchlist_quota_is_enforced(self):
        self.client.force_login(self.user)
        first = self.client.post(
            "/domainamer/watchlist/",
            data=json.dumps({"base_name": "quroom", "tlds": ["com"]}),
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 201)
        second = self.client.post(
            "/domainamer/watchlist/",
            data=json.dumps({"base_name": "quroom2", "tlds": ["com"]}),
            content_type="application/json",
        )
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json()["error"], "watch_quota_exceeded")

    @override_settings(DOMAIN_HARDENED_CHECK_ENABLED=False)
    def test_watchlist_check_enqueue_and_job_status(self):
        self.client.force_login(self.user)
        self.client.post(
            "/domainamer/watchlist/",
            data=json.dumps({"base_name": "quroom", "tlds": ["com"]}),
            content_type="application/json",
        )
        enqueue = self.client.post("/domainamer/watchlist/check/", data="{}", content_type="application/json")
        self.assertEqual(enqueue.status_code, 202)
        job_id = enqueue.json()["job_id"]
        self.assertEqual(WatchlistCheckJob.objects.get(id=job_id).status, WatchlistCheckJob.STATUS_QUEUED)

        call_command("process_watchlist_jobs")

        status_response = self.client.get(f"/domainamer/watchlist/check-jobs/{job_id}/")
        self.assertEqual(status_response.status_code, 200)
        status_payload = status_response.json()
        self.assertEqual(status_payload["status"], WatchlistCheckJob.STATUS_SUCCEEDED)
        self.assertIn("checked_domains", status_payload["summary"])

    @override_settings(DOMAIN_HARDENED_CHECK_ENABLED=False, DOMAIN_UNAVAILABLE_DOMAINS=["quroom.com"])
    def test_watchlist_check_creates_alert_after_transition(self):
        self.client.force_login(self.user)
        self.client.post(
            "/domainamer/watchlist/",
            data=json.dumps({"base_name": "quroom", "tlds": ["com"]}),
            content_type="application/json",
        )

        first = self.client.post("/domainamer/watchlist/check/", data="{}", content_type="application/json")
        self.assertEqual(first.status_code, 202)
        first_job_id = first.json()["job_id"]
        call_command("process_watchlist_jobs")
        first_job = self.client.get(f"/domainamer/watchlist/check-jobs/{first_job_id}/").json()
        self.assertEqual(first_job["summary"]["alerts_created"], 0)

        with override_settings(DOMAIN_UNAVAILABLE_DOMAINS=[]):
            second = self.client.post("/domainamer/watchlist/check/", data="{}", content_type="application/json")
            self.assertEqual(second.status_code, 202)
            second_job_id = second.json()["job_id"]
            call_command("process_watchlist_jobs")
            second_job = self.client.get(f"/domainamer/watchlist/check-jobs/{second_job_id}/").json()
            self.assertEqual(second_job["summary"]["alerts_created"], 1)

        alerts = self.client.get("/domainamer/watchlist/alerts/")
        self.assertEqual(alerts.status_code, 200)
        self.assertEqual(len(alerts.json()["alerts"]), 1)
