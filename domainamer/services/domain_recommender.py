import re
from datetime import datetime, timezone
from typing import Callable, Iterable

from .availability import AvailabilityDecision

AvailabilityChecker = Callable[[str], bool]
AvailabilityResolver = Callable[[str], AvailabilityDecision]


def normalize_candidate(candidate: str) -> str:
    lowered = candidate.strip().lower()
    without_tld = re.sub(r"\.(com|kr|io|net|org)$", "", lowered)
    compact = re.sub(r"[\s\-]+", "", without_tld)
    return re.sub(r"[^a-z0-9]", "", compact)


def to_domain(candidate: str, tld: str = "com") -> str:
    normalized = normalize_candidate(candidate)
    return f"{normalized}.{tld}" if normalized else ""


def normalize_tld(tld: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(tld).lower().replace(".", ""))


def normalize_domain_entry(domain: str) -> str:
    raw = str(domain).strip().lower()
    if not raw:
        return ""
    if "." not in raw:
        return to_domain(raw)
    name, _, tld = raw.rpartition(".")
    normalized_name = normalize_candidate(name)
    normalized_tld = normalize_tld(tld)
    if not normalized_name or not normalized_tld:
        return ""
    return f"{normalized_name}.{normalized_tld}"


def default_availability_checker(domain: str) -> bool:
    # Default is permissive so callers can inject real WHOIS/registry checks later.
    return bool(domain)


def generate_alternatives(
    base_candidate: str,
    existing_domains: set[str],
    checker: AvailabilityChecker,
    preferred_tlds: Iterable[str] = ("com", "kr", "io"),
    limit: int = 3,
) -> list[str]:
    base = normalize_candidate(base_candidate)
    if not base:
        return []

    suffixes = ("go", "lab", "hq", "app", "now", "360")
    alternatives: list[str] = []
    seen = set(existing_domains)
    for tld in preferred_tlds:
        normalized_tld = normalize_tld(tld)
        if not normalized_tld:
            continue
        alt = f"{base}.{normalized_tld}"
        if alt in seen:
            continue
        if checker(alt):
            alternatives.append(alt)
            seen.add(alt)
        if len(alternatives) >= limit:
            return alternatives

    for suffix in suffixes:
        alt = f"{base}{suffix}.com"
        if alt in seen:
            continue
        if checker(alt):
            alternatives.append(alt)
            seen.add(alt)
        if len(alternatives) >= limit:
            return alternatives

    for number in range(1, limit * 5):
        alt = f"{base}{number}.com"
        if alt in seen:
            continue
        if checker(alt):
            alternatives.append(alt)
            seen.add(alt)
        if len(alternatives) >= limit:
            break

    return alternatives


def recommend_domains(
    candidates: Iterable[str],
    availability_checker: AvailabilityChecker | None = None,
    availability_resolver: AvailabilityResolver | None = None,
    preferred_tlds: Iterable[str] = ("com", "kr", "io"),
    alternatives_limit: int = 3,
) -> dict[str, list[dict[str, object]]]:
    checker = availability_checker or default_availability_checker
    now = datetime.now(timezone.utc).isoformat()
    seen_normalized: set[str] = set()
    seen_domains: set[str] = set()
    results: list[dict[str, object]] = []

    for candidate in candidates:
        domain = to_domain(candidate)
        normalized = normalize_candidate(candidate)
        if not normalized or not domain:
            continue

        if normalized in seen_normalized:
            alternatives = generate_alternatives(
                candidate,
                seen_domains,
                checker,
                preferred_tlds=preferred_tlds,
                limit=alternatives_limit,
            )
            results.append(
                {
                    "candidate": domain,
                    "status": "duplicate",
                    "reason": "duplicate_candidate",
                    "alternatives": alternatives,
                    "confidence": 1.0,
                    "evidence": [{"source": "normalization", "outcome": "duplicate"}],
                    "checked_at": now,
                }
            )
            seen_domains.update(alternatives)
            continue

        seen_normalized.add(normalized)
        if availability_resolver:
            decision = availability_resolver(domain)
            status = decision.status
            reason = decision.reason
            confidence = decision.confidence
            evidence = decision.evidence
            checked_at = decision.checked_at
        else:
            is_available = checker(domain)
            status = "available" if is_available else "unavailable"
            reason = None if is_available else "already_registered"
            confidence = 0.7 if is_available else 0.8
            evidence = [{"source": "legacy_checker", "outcome": status}]
            checked_at = now

        if status == "available":
            results.append(
                {
                    "candidate": domain,
                    "status": status,
                    "reason": reason,
                    "alternatives": [],
                    "confidence": confidence,
                    "evidence": evidence,
                    "checked_at": checked_at,
                }
            )
            seen_domains.add(domain)
            continue

        alternatives: list[str] = []
        if status == "unavailable":
            alternatives = generate_alternatives(
                candidate,
                seen_domains | {domain},
                checker,
                preferred_tlds=preferred_tlds,
                limit=alternatives_limit,
            )
        results.append(
            {
                "candidate": domain,
                "status": status,
                "reason": reason,
                "alternatives": alternatives,
                "confidence": confidence,
                "evidence": evidence,
                "checked_at": checked_at,
            }
        )
        seen_domains.add(domain)
        seen_domains.update(alternatives)

    return {"results": results}


def reroll_domain_alternatives(
    base_candidate: str,
    exclude_domains: Iterable[str],
    availability_checker: AvailabilityChecker | None = None,
    preferred_tlds: Iterable[str] = ("com", "kr", "io"),
    limit: int = 3,
) -> dict[str, object]:
    checker = availability_checker or default_availability_checker
    base_domain = to_domain(base_candidate)
    normalized_excludes = {item for item in (normalize_domain_entry(domain) for domain in exclude_domains) if item}
    seen_domains = set(normalized_excludes)
    if base_domain:
        seen_domains.add(base_domain)

    alternatives = generate_alternatives(
        base_candidate=base_candidate,
        existing_domains=seen_domains,
        checker=checker,
        preferred_tlds=preferred_tlds,
        limit=limit,
    )
    return {
        "candidate": base_domain,
        "excluded": sorted(normalized_excludes),
        "alternatives": alternatives,
    }
