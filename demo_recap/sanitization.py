from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .models import DemoContact

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
URL_RE = re.compile(r"\b(?:https?://|www\.)[^\s<>()\[\]{}]+", re.IGNORECASE)
MULTISPACE_RE = re.compile(r"\s+")

PERSON_PART_STOPWORDS = {
    "admin",
    "administrator",
    "analyst",
    "champion",
    "director",
    "engineer",
    "finance",
    "lead",
    "manager",
    "marketing",
    "operations",
    "owner",
    "procurement",
    "security",
    "sponsor",
    "success",
    "technical",
    "technology",
    "user",
}

ORG_GENERIC_WORDS = {
    "academy",
    "association",
    "bank",
    "clinic",
    "clinics",
    "co",
    "college",
    "company",
    "corp",
    "corporation",
    "district",
    "foundation",
    "group",
    "health",
    "inc",
    "institute",
    "lab",
    "labs",
    "llc",
    "ltd",
    "school",
    "schools",
    "services",
    "studios",
    "systems",
    "university",
}

LOCATION_GENERIC_WORDS = {"remote", "call", "video", "zoom", "meet", "meeting", "office"}
CONTACT_CANDIDATE_STOPWORDS = PERSON_PART_STOPWORDS | {"client", "customer", "demo", "external", "internal", "support"}


@dataclass(frozen=True)
class RedactionRule:
    value: str
    placeholder: str


def normalize_known_value(value: str) -> str:
    value = value.strip()
    value = MULTISPACE_RE.sub(" ", value)
    return value.strip(" \t\n\r:;,.<>[]{}()")


def _is_useful_known_value(value: str) -> bool:
    normalized = normalize_known_value(value)
    return len(normalized) >= 2 and any(ch.isalpha() for ch in normalized)


def _dedupe_rules(rules: Iterable[RedactionRule]) -> list[RedactionRule]:
    seen: set[tuple[str, str]] = set()
    deduped: list[RedactionRule] = []
    for rule in rules:
        normalized = normalize_known_value(rule.value)
        if not _is_useful_known_value(normalized):
            continue
        key = (normalized.casefold(), rule.placeholder)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(RedactionRule(normalized, rule.placeholder))
    return sorted(deduped, key=lambda item: len(item.value), reverse=True)


def _without_contact_noise(value: str) -> str:
    without_email = EMAIL_RE.sub(" ", value)
    without_url = URL_RE.sub(" ", without_email)
    without_angle_residue = re.sub(r"[<>]", " ", without_url)
    without_labels = re.sub(
        r"\b(?:name|email|e-mail|mail|phone|role|title|contact|attendee)\s*:\s*",
        " ",
        without_angle_residue,
        flags=re.IGNORECASE,
    )
    return normalize_known_value(without_labels)


def _significant_words(value: str, min_len: int = 3) -> list[str]:
    return [word for word in re.findall(r"[A-Za-z][A-Za-z'’-]+", value) if len(word) >= min_len]


def _looks_like_contact_name_candidate(value: str) -> bool:
    words = [word.casefold() for word in _significant_words(value)]
    if not words:
        return False
    if any(word in ORG_GENERIC_WORDS for word in words):
        return False
    return any(word not in CONTACT_CANDIDATE_STOPWORDS for word in words)


def _name_like_prefix(value: str) -> str:
    # Many attendee lines are written as "Name - role" or "Name (role)".
    # Keep the full deterministic candidate too, but also add this prefix so a
    # later body mention like "Name asked..." is still redacted.
    prefix = re.split(r"\s[-–—]\s|\(|,", value, maxsplit=1)[0]
    return normalize_known_value(prefix)


def extract_contact_name_candidates(with_text: str) -> list[str]:
    """Extract deterministic contact-name candidates from the raw WITH answer.

    The WITH answer itself is not altered. Candidates are derived from the first
    pipe-delimited segment on each line, then cleaned of obvious email/URL/label
    noise. This keeps role fragments such as "Help Desk Lead" from becoming
    contact-name rules.
    """
    candidates: list[str] = []
    for line in with_text.splitlines():
        piece = line.split("|", maxsplit=1)[0]
        cleaned = _without_contact_noise(piece)
        if not cleaned or not _looks_like_contact_name_candidate(cleaned):
            continue
        candidates.append(cleaned)
        prefix = _name_like_prefix(cleaned)
        if prefix and prefix != cleaned and _looks_like_contact_name_candidate(prefix):
            candidates.append(prefix)
    return [rule.value for rule in _dedupe_rules(RedactionRule(item, "[CONTACT]") for item in candidates)]


def _person_component_rules(name: str, placeholder: str) -> list[RedactionRule]:
    rules: list[RedactionRule] = []
    for word in _significant_words(name, min_len=3):
        if word.casefold() in PERSON_PART_STOPWORDS:
            continue
        rules.append(RedactionRule(word, placeholder))
    return rules


def _organization_component_rules(name: str) -> list[RedactionRule]:
    rules: list[RedactionRule] = []
    for word in _significant_words(name, min_len=4):
        if word.casefold() in ORG_GENERIC_WORDS:
            continue
        rules.append(RedactionRule(word, "[ORG]"))
    return rules


def _location_component_rules(location: str) -> list[RedactionRule]:
    rules: list[RedactionRule] = []
    for part in re.split(r"[,/;]", location):
        normalized = normalize_known_value(part)
        if not normalized or normalized.casefold() in LOCATION_GENERIC_WORDS:
            continue
        if len(normalized) >= 3:
            rules.append(RedactionRule(normalized, "[LOCATION]"))
    return rules


def build_redaction_rules(
    *,
    organization_name: str,
    lead_name: str,
    location: str,
    with_text: str,
    contacts: Iterable[DemoContact] = (),
) -> list[RedactionRule]:
    structured_contact_names = [contact.name for contact in contacts if contact.name.strip()]
    contact_names = [*structured_contact_names, *extract_contact_name_candidates(with_text)]
    rules: list[RedactionRule] = [
        RedactionRule(organization_name, "[ORG]"),
        RedactionRule(lead_name, "[LEAD]"),
        RedactionRule(location, "[LOCATION]"),
    ]
    rules.extend(_organization_component_rules(organization_name))
    rules.extend(_person_component_rules(lead_name, "[LEAD]"))
    rules.extend(_location_component_rules(location))
    for contact_name in contact_names:
        rules.append(RedactionRule(contact_name, "[CONTACT]"))
        rules.extend(_person_component_rules(contact_name, "[CONTACT]"))
    return _dedupe_rules(rules)


def sanitize_text(text: str, rules: Iterable[RedactionRule]) -> str:
    """Deterministically redact known identifiers from text.

    Redaction is intentionally simple and inspectable: first replace emails and
    URLs, then replace explicit known values case-insensitively, longest first.
    """
    sanitized = EMAIL_RE.sub("[EMAIL]", text or "")
    sanitized = URL_RE.sub("[URL]", sanitized)
    for rule in _dedupe_rules(rules):
        sanitized = _literal_phrase_pattern(rule.value).sub(rule.placeholder, sanitized)
    return sanitized


def find_unredacted_known_values(text: str, rules: Iterable[RedactionRule]) -> list[str]:
    findings: list[str] = []
    for rule in _dedupe_rules(rules):
        if _literal_phrase_pattern(rule.value).search(text):
            findings.append(rule.value)
    return findings


def _literal_phrase_pattern(value: str) -> re.Pattern[str]:
    parts = [re.escape(part) for part in re.split(r"\s+", value.strip()) if part]
    body = r"\s+".join(parts)
    if not body:
        return re.compile(r"a^")
    return re.compile(rf"(?<![A-Za-z0-9_]){body}(?![A-Za-z0-9_])", re.IGNORECASE)


def find_basic_identifier_patterns(text: str) -> list[str]:
    findings: list[str] = []
    if EMAIL_RE.search(text):
        findings.append("email address")
    if URL_RE.search(text):
        findings.append("URL")
    return findings
