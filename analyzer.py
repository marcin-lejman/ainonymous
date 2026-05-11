from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from polish_recognizers import (
    PeselRecognizer,
    NipRecognizer,
    RegonRecognizer,
    KrsRecognizer,
    PolishIbanRecognizer,
    PolishPhoneRecognizer,
)

# Polish legal terms that spaCy frequently misclassifies as PERSON or ORGANIZATION.
# These are common nouns/roles in contracts, not named entities.
POLISH_LEGAL_STOPWORDS = {
    # Roles tagged as PERSON
    "Wynajmującej", "Wynajmującego", "Wynajmujący", "Wynajmującą",
    "Najemcy", "Najemca", "Najemcą",
    "Kupującej", "Kupującego", "Kupująca", "Kupujący",
    "Sprzedającego", "Sprzedającej", "Sprzedający",
    "Obdarowanego", "Obdarowanemu", "Obdarowany",
    "Mocodawcy", "Mocodawca", "Mocodawcą",
    "Pełnomocnika", "Pełnomocnik",
    "Darczyńcy", "Darczyńca",
    "Zleceniobiorcy", "Zleceniobiorca", "Zleceniobiorcy",
    "Zleceniodawcy", "Zleceniodawca",
    "Zamawiającego", "Zamawiający", "Zamawiającą",
    "Wykonawcy", "Wykonawca", "Wykonawcą",
    "Pożyczkodawcy", "Pożyczkodawca",
    "Pożyczkobiorcy", "Pożyczkobiorca",
    "Otrzymującej", "Otrzymującego", "Otrzymująca",
    "Zawarta", "Zawarto",
    "A.", "B.", "C.", "D.",
    # Organizations tagged as ORGANIZATION
    "Zarządu", "Zarząd",
    "Stron", "Strony", "Stronom",
    "Stronę Ujawniającą", "Stronie Otrzymującej",
    "Stronę Ujawniającą Stronie Otrzymującej",
    "Strony Ujawniającej",
    "Pracodawcą", "Pracodawcy", "Pracodawca",
    "Zleceniodawcy",
    "Zamawiającego",
    "KRS",  # the abbreviation itself, not a number
    "ZUS", "PIT", "CIT", "VAT",
    "UJ",
    "ZACHOWANIU",
    "Lokalu", "Lokal",
}

# Fragments that indicate a false-positive LOCATION
LOCATION_STOPWORDS = {
    "PEŁNOMOCNICTWO", "LOKALU MIESZKALNEGO", "LOKALU UŻYTKOWEGO",
    "PL",  # country code prefix in IBAN, not a location
}


def build_analyzer():
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [
            {
                "lang_code": "pl",
                "model_name": "pl_core_news_lg",
            },
            {
                "lang_code": "en",
                "model_name": "en_core_web_lg",
            },
        ],
        "ner_model_configuration": {
            "model_to_presidio_entity_mapping": {
                "persName": "PERSON",
                "placeName": "LOCATION",
                "geogName": "LOCATION",
                "orgName": "ORGANIZATION",
                "PER": "PERSON",
                "LOC": "LOCATION",
                "GPE": "LOCATION",
                "ORG": "ORGANIZATION",
                "PERSON": "PERSON",
                "LOCATION": "LOCATION",
                "ORGANIZATION": "ORGANIZATION",
            },
        },
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()

    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["en", "pl"],
    )

    analyzer.registry.add_recognizer(PeselRecognizer())
    analyzer.registry.add_recognizer(NipRecognizer())
    analyzer.registry.add_recognizer(RegonRecognizer())
    analyzer.registry.add_recognizer(KrsRecognizer())
    analyzer.registry.add_recognizer(PolishIbanRecognizer())
    analyzer.registry.add_recognizer(PolishPhoneRecognizer())

    return analyzer


def _extend_locations_with_numbers(results, text):
    """Extend LOCATION entities to include trailing street/apartment numbers."""
    import re
    from presidio_analyzer import RecognizerResult
    extended = []
    for r in results:
        if r.entity_type != "LOCATION":
            extended.append(r)
            continue
        end = r.end
        remaining = text[end:end + 20]
        m = re.match(r"(\s+\d+(?:[/]\d+)?(?:\s+m\.\s*\d+)?)", remaining)
        if m:
            extended.append(RecognizerResult(
                entity_type=r.entity_type,
                start=r.start,
                end=end + m.end(),
                score=r.score,
                analysis_explanation=r.analysis_explanation,
            ))
        else:
            extended.append(r)
    return extended


def _merge_entity_sequences(results, text):
    """Merge adjacent ORG/PERSON entities that form a single company or firm name."""
    from presidio_analyzer import RecognizerResult
    import re as _re

    mergeable_types = {"ORGANIZATION", "PERSON"}
    candidates = [r for r in results if r.entity_type in mergeable_types]
    others = [r for r in results if r.entity_type not in mergeable_types]
    if len(candidates) <= 1:
        return results
    candidates.sort(key=lambda r: r.start)
    sequences: list[list] = [[candidates[0]]]
    for curr in candidates[1:]:
        prev = sequences[-1][-1]
        raw_gap = text[prev.end:curr.start]
        gap = raw_gap.strip()
        # Same-type ORG+ORG with whitespace gap
        if prev.entity_type == "ORGANIZATION" and curr.entity_type == "ORGANIZATION":
            if len(raw_gap) <= 3 and (gap == "" or gap in ("i", "-", "&", "·")):
                sequences[-1].append(curr)
                continue
        # Cross-type: only "i" or "&", NOT "-" (em dash separator)
        if prev.entity_type != curr.entity_type:
            if gap in ("i", "&") and "-" not in raw_gap:
                sequences[-1].append(curr)
                continue
        # PERSON+PERSON with "i"
        if prev.entity_type == "PERSON" and curr.entity_type == "PERSON":
            if gap == "i":
                sequences[-1].append(curr)
                continue
        sequences.append([curr])

    merged_results = []
    absorbed = set()
    for seq in sequences:
        if len(seq) == 1:
            merged_results.append(seq[0])
            continue
        has_org = any(r.entity_type == "ORGANIZATION" for r in seq)
        if has_org:
            merged_results.append(RecognizerResult(
                entity_type="ORGANIZATION",
                start=seq[0].start,
                end=seq[-1].end,
                score=max(r.score for r in seq),
                analysis_explanation=seq[0].analysis_explanation,
            ))
            for r in seq:
                if r.entity_type == "PERSON":
                    absorbed.add((r.start, r.end))
        else:
            merged_results.extend(seq)

    # Extend merged ORGs to absorb trailing company suffixes
    company_suffix = _re.compile(
        r"[-\w]*\s*(?:spółka\s+cywilna|sp(?:ółka)?\.?\s*(?:z\s*o\.?\s*o\.?|j\.|k\.|p\.)|"
        r"s\.?\s*c\.?|S\.?\s*A\.?|sp(?:ółka)?\.?\s+komandytowa|spółka\s+partnerska)",
        _re.IGNORECASE
    )
    final_results = []
    for r in merged_results:
        if r.entity_type == "ORGANIZATION":
            remaining = text[r.end:r.end + 60]
            m = company_suffix.match(remaining)
            if m:
                r = RecognizerResult(
                    entity_type="ORGANIZATION",
                    start=r.start,
                    end=r.end + m.end(),
                    score=r.score,
                    analysis_explanation=r.analysis_explanation,
                )
        final_results.append(r)

    return [r for r in others if (r.start, r.end) not in absorbed] + final_results


def post_process(results, text):
    """Filter and resolve collisions in analyzer results."""
    # Filter stopwords FIRST, before merging
    pre_filtered = []
    for r in results:
        entity_text = text[r.start:r.end].strip()
        if r.entity_type in ("PERSON", "ORGANIZATION") and entity_text in POLISH_LEGAL_STOPWORDS:
            continue
        if r.entity_type == "ORGANIZATION" and (entity_text.startswith("\u201e") or entity_text.startswith('"')):
            clean = entity_text.strip('\u201e\u201d"')
            if clean in POLISH_LEGAL_STOPWORDS:
                continue
        if r.entity_type == "LOCATION" and entity_text in LOCATION_STOPWORDS:
            continue
        if r.entity_type == "PERSON" and len(entity_text) <= 2:
            continue
        if r.entity_type == "LOCATION" and len(entity_text) <= 3:
            continue
        if r.entity_type == "PERSON" and any(c.isdigit() for c in entity_text):
            continue

        # Filter URL entities (we don't need to anonymize domains)
        if r.entity_type == "URL":
            continue

        # Filter DATE_TIME (not PII in legal contracts)
        if r.entity_type == "DATE_TIME":
            continue

        pre_filtered.append(r)

    # Now merge and extend
    results = _merge_entity_sequences(pre_filtered, text)
    results = _extend_locations_with_numbers(results, text)

    # Resolve NIP vs KRS vs PHONE collisions on the same span.
    result_map = {}
    for r in results:
        key = (r.start, r.end)
        if key not in result_map:
            result_map[key] = []
        result_map[key].append(r)

    deduped = []
    for key, group in result_map.items():
        if len(group) == 1:
            deduped.append(group[0])
            continue

        types = {r.entity_type for r in group}

        # KRS starting with 0000 wins over NIP (0000 prefix is a strong KRS signal,
        # even if the number happens to pass NIP checksum)
        if "KRS" in types and "NIP" in types:
            entity_text = text[key[0]:key[1]]
            if entity_text.startswith("0000"):
                deduped.extend(r for r in group if r.entity_type == "KRS")
                continue

        # NIP wins over KRS and PHONE_NUMBER on same span (when not 0000-prefixed)
        if "NIP" in types and ("KRS" in types or "PHONE_NUMBER" in types):
            deduped.extend(r for r in group if r.entity_type == "NIP")
            continue

        # PESEL wins over everything on same span
        if "PESEL" in types:
            deduped.extend(r for r in group if r.entity_type == "PESEL")
            continue

        # IBAN_CODE wins over CREDIT_CARD on same/overlapping span
        if "IBAN_CODE" in types and "CREDIT_CARD" in types:
            deduped.extend(r for r in group if r.entity_type == "IBAN_CODE")
            continue

        # Default: keep highest score
        best = max(group, key=lambda r: r.score)
        deduped.append(best)

    return deduped


def analyze(text, language="pl"):
    """Full analysis pipeline: run analyzer + post-process."""
    analyzer = build_analyzer()
    results = analyzer.analyze(text=text, language=language)
    return post_process(results, text)
