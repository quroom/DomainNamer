import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import DomainAlertEvent, DomainWatchItem, WatchlistCheckJob
from .services.availability import (
    AvailabilityConfig,
    AvailabilityOrchestrator,
    IpPool,
    RdapProvider,
    RuleBasedProvider,
    WhoisProvider,
)
from .services.domain_recommender import (
    normalize_candidate,
    recommend_domains,
    recommend_domains_from_service,
    reroll_domain_alternatives,
)

_ORCHESTRATOR = None
_ORCHESTRATOR_KEY = None


@require_GET
@ensure_csrf_cookie
def home_view(request):
    return render(request, "domainamer/app.html")


@require_GET
@ensure_csrf_cookie
def playground_view(request):
    return render(request, "domainamer/playground.html")


def _parse_candidates(request):
    content_type = request.content_type or ""
    if "application/json" in content_type:
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return None
        candidates = payload.get("candidates", [])
    else:
        candidates = request.POST.getlist("candidates")
        if not candidates:
            raw = request.POST.get("candidates", "")
            candidates = [item for item in re_split(raw) if item]

    cleaned = [str(candidate).strip() for candidate in candidates if str(candidate).strip()]
    return cleaned


def _parse_watch_payload(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None, None

    base_name = normalize_candidate(str(payload.get("base_name", "")))
    tlds = payload.get("tlds")
    if tlds is None:
        tlds = list(getattr(settings, "DOMAIN_DEFAULT_WATCH_TLDS", ["com", "kr"]))
    elif isinstance(tlds, str):
        tlds = [part.strip() for part in tlds.split(",")]
    elif not isinstance(tlds, list):
        return None, None

    cleaned_tlds: list[str] = []
    for tld in tlds:
        normalized = "".join(ch for ch in str(tld).lower() if ch.isalnum())
        if normalized and normalized not in cleaned_tlds:
            cleaned_tlds.append(normalized)

    if not base_name or not cleaned_tlds:
        return None, None
    return base_name, cleaned_tlds


def _canonical_tlds(tlds: list[str]) -> str:
    return ",".join(sorted(set(tlds)))


def _require_auth(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth_required"}, status=401)
    return None


def re_split(raw: str) -> list[str]:
    return [item.strip() for item in raw.replace("\n", ",").split(",")]


def _build_orchestrator() -> AvailabilityOrchestrator:
    blocked = set(getattr(settings, "DOMAIN_UNAVAILABLE_DOMAINS", []))
    timeout_domains = set(getattr(settings, "DOMAIN_TIMEOUT_DOMAINS", []))
    rate_limited_domains = set(getattr(settings, "DOMAIN_RATE_LIMITED_DOMAINS", []))
    ips = getattr(settings, "DOMAIN_CHECK_IP_POOL", ["10.0.0.1", "10.0.0.2", "10.0.0.3"])

    use_real = getattr(settings, "DOMAIN_REAL_PROVIDER_ENABLED", False)
    if use_real:
        providers = [
            RdapProvider(
                name="rdap-a",
                source_quality=0.95,
                endpoint_template=getattr(
                    settings,
                    "DOMAIN_RDAP_ENDPOINT_TEMPLATE",
                    "https://rdap.org/domain/{domain}",
                ),
                timeout_ms=getattr(settings, "AVAILABILITY_PROVIDER_TIMEOUT_MS", 1200),
            ),
            WhoisProvider(
                name="whois-b",
                source_quality=0.90,
                timeout_ms=getattr(settings, "AVAILABILITY_PROVIDER_TIMEOUT_MS", 1200),
                default_server=getattr(
                    settings,
                    "DOMAIN_WHOIS_SERVER",
                    "whois.verisign-grs.com",
                ),
            ),
        ]
    else:
        providers = [
            RuleBasedProvider(
                name="rdap-a",
                source_quality=0.95,
                blocked_domains=blocked,
                timeout_domains=timeout_domains,
                rate_limited_domains=rate_limited_domains,
            ),
            RuleBasedProvider(name="whois-b", source_quality=0.90, blocked_domains=blocked),
            RuleBasedProvider(name="dns-c", source_quality=0.85, blocked_domains=blocked),
        ]

    config = AvailabilityConfig(
        timeout_ms=getattr(settings, "AVAILABILITY_PROVIDER_TIMEOUT_MS", 1200),
        budget_timeout_ms=getattr(settings, "AVAILABILITY_BUDGET_TIMEOUT_MS", 1800),
        quorum_min=getattr(settings, "AVAILABILITY_QUORUM_MIN", 2),
        uncertain_confidence_cap=getattr(settings, "AVAILABILITY_UNCERTAIN_CONFIDENCE_CAP", 0.49),
        confidence_weight_agreement=getattr(settings, "CONFIDENCE_WEIGHT_AGREEMENT", 0.45),
        confidence_weight_source=getattr(settings, "CONFIDENCE_WEIGHT_SOURCE", 0.20),
        confidence_weight_health=getattr(settings, "CONFIDENCE_WEIGHT_HEALTH", 0.15),
        confidence_weight_freshness=getattr(settings, "CONFIDENCE_WEIGHT_FRESHNESS", 0.10),
        confidence_weight_error=getattr(settings, "CONFIDENCE_WEIGHT_ERROR", 0.10),
        fallback_to_legacy=getattr(settings, "DOMAIN_HARDENED_FALLBACK_TO_LEGACY", True),
        shadow_mode=getattr(settings, "DOMAIN_SHADOW_MODE", False),
        max_attempts_per_provider=getattr(settings, "AVAILABILITY_MAX_ATTEMPTS_PER_PROVIDER", 3),
    )
    ip_pool = IpPool(
        ips=ips,
        cooldown_base_sec=getattr(settings, "IP_POOL_COOLDOWN_BASE_SEC", 60),
        cooldown_max_sec=getattr(settings, "IP_POOL_COOLDOWN_MAX_SEC", 600),
    )
    return AvailabilityOrchestrator(providers=providers, ip_pool=ip_pool, config=config)


def _get_orchestrator() -> AvailabilityOrchestrator:
    global _ORCHESTRATOR, _ORCHESTRATOR_KEY
    key = (
        getattr(settings, "DOMAIN_REAL_PROVIDER_ENABLED", False),
        getattr(settings, "DOMAIN_RDAP_ENDPOINT_TEMPLATE", ""),
        getattr(settings, "DOMAIN_WHOIS_SERVER", ""),
        tuple(getattr(settings, "DOMAIN_UNAVAILABLE_DOMAINS", [])),
        tuple(getattr(settings, "DOMAIN_TIMEOUT_DOMAINS", [])),
        tuple(getattr(settings, "DOMAIN_RATE_LIMITED_DOMAINS", [])),
        tuple(getattr(settings, "DOMAIN_CHECK_IP_POOL", [])),
        getattr(settings, "AVAILABILITY_PROVIDER_TIMEOUT_MS", 1200),
        getattr(settings, "AVAILABILITY_QUORUM_MIN", 2),
        getattr(settings, "AVAILABILITY_MAX_ATTEMPTS_PER_PROVIDER", 3),
        getattr(settings, "IP_POOL_COOLDOWN_BASE_SEC", 60),
        getattr(settings, "IP_POOL_COOLDOWN_MAX_SEC", 600),
    )
    if _ORCHESTRATOR is None or _ORCHESTRATOR_KEY != key:
        _ORCHESTRATOR = _build_orchestrator()
        _ORCHESTRATOR_KEY = key
    return _ORCHESTRATOR


@require_POST
def recommend_domains_view(request):
    candidates = _parse_candidates(request)
    if candidates is None:
        return JsonResponse({"error": "invalid_json"}, status=400)
    if not candidates:
        return JsonResponse({"error": "candidates_required"}, status=400)

    use_hardened = getattr(settings, "DOMAIN_HARDENED_CHECK_ENABLED", True)
    shadow_mode = getattr(settings, "DOMAIN_SHADOW_MODE", False)
    fallback = getattr(settings, "DOMAIN_HARDENED_FALLBACK_TO_LEGACY", True)
    preferred_tlds = tuple(getattr(settings, "DOMAIN_PREFERRED_TLDS", ["com", "kr", "io"]))

    if not use_hardened:
        return JsonResponse(recommend_domains(candidates, preferred_tlds=preferred_tlds))

    try:
        orchestrator = _get_orchestrator()
        hardened_payload = recommend_domains(
            candidates,
            availability_resolver=orchestrator.check,
            preferred_tlds=preferred_tlds,
        )
    except Exception:
        if fallback:
            return JsonResponse(recommend_domains(candidates, preferred_tlds=preferred_tlds))
        raise

    if shadow_mode:
        # Shadow mode computes hardened checks for telemetry while preserving legacy response.
        return JsonResponse(recommend_domains(candidates, preferred_tlds=preferred_tlds))
    return JsonResponse(hardened_payload)


@require_POST
def reroll_recommendation_view(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    base_candidate = str(payload.get("candidate", "")).strip()
    if not base_candidate:
        return JsonResponse({"error": "candidate_required"}, status=400)
    exclude = payload.get("exclude", [])
    if not isinstance(exclude, list):
        return JsonResponse({"error": "exclude_must_be_list"}, status=400)

    preferred_tlds = tuple(getattr(settings, "DOMAIN_PREFERRED_TLDS", ["com", "kr", "io"]))
    limit = int(payload.get("limit", 3))
    if limit < 1:
        limit = 1
    if limit > 20:
        limit = 20

    result = reroll_domain_alternatives(
        base_candidate=base_candidate,
        exclude_domains=exclude,
        preferred_tlds=preferred_tlds,
        limit=limit,
    )
    return JsonResponse(result)


@require_POST
def service_recommendation_view(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    service_name = str(payload.get("service_name", "")).strip()
    service_description = str(payload.get("service_description", "")).strip()
    if not service_name and not service_description:
        return JsonResponse({"error": "service_input_required"}, status=400)

    preferred_tlds = tuple(getattr(settings, "DOMAIN_PREFERRED_TLDS", ["com", "kr", "io"]))
    use_hardened = getattr(settings, "DOMAIN_HARDENED_CHECK_ENABLED", True)
    fallback = getattr(settings, "DOMAIN_HARDENED_FALLBACK_TO_LEGACY", True)

    if not use_hardened:
        data = recommend_domains_from_service(
            service_name=service_name,
            service_description=service_description,
            preferred_tlds=preferred_tlds,
        )
        return JsonResponse(data)

    try:
        orchestrator = _get_orchestrator()
        data = recommend_domains_from_service(
            service_name=service_name,
            service_description=service_description,
            availability_resolver=orchestrator.check,
            preferred_tlds=preferred_tlds,
        )
        return JsonResponse(data)
    except Exception:
        if fallback:
            data = recommend_domains_from_service(
                service_name=service_name,
                service_description=service_description,
                preferred_tlds=preferred_tlds,
            )
            return JsonResponse(data)
        raise


@require_http_methods(["GET", "POST"])
def watchlist_view(request):
    auth_error = _require_auth(request)
    if auth_error:
        return auth_error

    if request.method == "GET":
        items = DomainWatchItem.objects.filter(owner=request.user).order_by("-updated_at")
        payload = {
            "items": [
                {
                    "id": item.id,
                    "base_name": item.base_name,
                    "tlds": item.tlds,
                    "is_active": item.is_active,
                    "last_statuses": item.last_statuses,
                    "last_checked_at": item.last_checked_at.isoformat() if item.last_checked_at else None,
                }
                for item in items
            ]
        }
        return JsonResponse(payload)

    base_name, tlds = _parse_watch_payload(request)
    if not base_name or not tlds:
        return JsonResponse({"error": "invalid_watch_payload"}, status=400)
    canonical_tlds = _canonical_tlds(tlds)

    max_items = int(getattr(settings, "WATCHLIST_MAX_ITEMS_PER_USER", 20))
    active_count = DomainWatchItem.objects.filter(owner=request.user, is_active=True).count()
    if active_count >= max_items:
        return JsonResponse({"error": "watch_quota_exceeded", "max_items": max_items}, status=429)

    if DomainWatchItem.objects.filter(
        owner=request.user,
        base_name=base_name,
        canonical_tlds=canonical_tlds,
    ).exists():
        return JsonResponse({"error": "watch_duplicate"}, status=409)

    watch = DomainWatchItem.objects.create(
        owner=request.user,
        base_name=base_name,
        tlds=tlds,
        canonical_tlds=canonical_tlds,
    )
    return JsonResponse(
        {
            "id": watch.id,
            "base_name": watch.base_name,
            "tlds": watch.tlds,
            "is_active": watch.is_active,
        },
        status=201,
    )


@require_POST
def watchlist_check_view(request):
    auth_error = _require_auth(request)
    if auth_error:
        return auth_error

    job = WatchlistCheckJob.objects.create(owner=request.user, status=WatchlistCheckJob.STATUS_QUEUED)
    return JsonResponse(
        {
            "job_id": job.id,
            "status": job.status,
        }
    , status=202)


@require_GET
def watchlist_alerts_view(request):
    auth_error = _require_auth(request)
    if auth_error:
        return auth_error

    events = DomainAlertEvent.objects.filter(watch_item__owner=request.user).order_by("-created_at")
    return JsonResponse(
        {
            "alerts": [
                {
                    "id": event.id,
                    "watch_item_id": event.watch_item_id,
                    "domain": event.domain,
                    "previous_status": event.previous_status,
                    "current_status": event.current_status,
                    "checked_at": event.checked_at.isoformat(),
                    "created_at": event.created_at.isoformat(),
                }
                for event in events
            ]
        }
    )


@require_GET
def watchlist_check_job_status_view(request, job_id: int):
    auth_error = _require_auth(request)
    if auth_error:
        return auth_error

    try:
        job = WatchlistCheckJob.objects.get(id=job_id, owner=request.user)
    except WatchlistCheckJob.DoesNotExist:
        return JsonResponse({"error": "job_not_found"}, status=404)

    return JsonResponse(
        {
            "id": job.id,
            "status": job.status,
            "summary": job.summary,
            "error_message": job.error_message,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "created_at": job.created_at.isoformat(),
        }
    )
