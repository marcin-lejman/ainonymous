from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from polish_recognizers import (
    PeselRecognizer,
    NipRecognizer,
    RegonRecognizer,
    KrsRecognizer,
    PolishIbanRecognizer,
    PolishPhoneRecognizer,
    PolishIdCardRecognizer,
    PolishAddressRecognizer,
    PolishZipCityRecognizer,
    PolishCompanyRecognizer,
)

import re as _re

# Polish legal role stems — we check if a single-word PERSON/ORG entity
# starts with any of these stems. This is much more robust than listing
# every declension of every legal role.
_LEGAL_ROLE_STEMS = [
    "Wynajmując", "Najemca", "Najemcy", "Najemcą",
    "Kupując", "Sprzedając",
    "Obdarowan", "Mocodawc", "Pełnomocnik", "Darczyńc",
    "Zleceniobiorc", "Zleceniodawc",
    "Zamawiając", "Wykonawc",
    "Pożyczkodawc", "Pożyczkobiorc",
    "Otrzymując",
    "Pracodawc",
    "Poręczyciel", "Cesjonariusz", "Cedent",
    "Dzierżawc", "Komisant", "Komitent",
    "Użyczając", "Biorąc",
    "Licencjodawc", "Licencjobiorc",
    "Mediator",
]

def _is_legal_role(text: str) -> bool:
    """Check if text is a Polish legal role label (any declension)."""
    text = text.strip()
    # Multi-word phrases that are role labels
    if text in (
        "Stronę Ujawniającą", "Stronie Otrzymującej",
        "Stronę Ujawniającą Stronie Otrzymującej",
        "Strony Ujawniającej",
    ):
        return True
    # Single words: check against stems
    if " " in text:
        return False
    return any(text.startswith(stem) for stem in _LEGAL_ROLE_STEMS)

# Exact-match stopwords for things that aren't role labels but cause FPs
ENTITY_STOPWORDS = {
    "A.", "B.", "C.", "D.",
    "Zarządu", "Zarząd", "Zarządowi",
    "Stron", "Strony", "Stronom", "Stronami",
    "KRS", "ZUS", "PIT", "CIT", "VAT", "UJ",
    "ZACHOWANIU", "Lokalu", "Lokal", "Zawarta", "Zawarto",
}

LOCATION_STOPWORDS = {
    "PEŁNOMOCNICTWO", "LOKALU MIESZKALNEGO", "LOKALU UŻYTKOWEGO", "PL",
}

_analyzer_instance = None


def get_analyzer():
    global _analyzer_instance
    if _analyzer_instance is not None:
        return _analyzer_instance

    configuration = {
        "nlp_engine_name": "spacy",
        "models": [
            {"lang_code": "pl", "model_name": "pl_core_news_lg"},
            {"lang_code": "en", "model_name": "en_core_web_lg"},
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
    analyzer.registry.add_recognizer(PolishIdCardRecognizer())
    analyzer.registry.add_recognizer(PolishAddressRecognizer())
    analyzer.registry.add_recognizer(PolishZipCityRecognizer())
    analyzer.registry.add_recognizer(PolishCompanyRecognizer())

    _analyzer_instance = analyzer
    return analyzer


_FULL_LEGAL_FORM_RE = _re.compile(
    r"\s+(?:"
    r"spółk[aęąi]\s+z\s+ograniczon[aą]\s+odpowiedzialnością"
    r"|sp(?:ółka)?\.?\s*(?:z\s*o\.?\s*o\.?|j\.|k\.|p\.)"
    r"|s\.?\s*c\.?"
    r"|s\.\s*a\.?|s\.?\s*a\."  # S.A. — require at least one dot
    r"|sp(?:ółka)?\.?\s+komandytow[aą]"
    r"|spółk[aęąi]\s+cywiln[aąej]"
    r"|spółk[aęąi]\s+partnersk[aąiej]"
    r")",
    _re.IGNORECASE,
)


def _reclassify_person_with_legal_form(results, text):
    """Reclassify PERSON entities as ORGANIZATION when followed by a company legal form.

    e.g. "NovaLokum spółka z ograniczoną odpowiedzialnością" → one ORG entity.
    """
    from presidio_analyzer import RecognizerResult

    updated = []
    for r in results:
        if r.entity_type != "PERSON":
            updated.append(r)
            continue

        remaining = text[r.end:r.end + 80]
        m = _FULL_LEGAL_FORM_RE.match(remaining)
        if m:
            updated.append(RecognizerResult(
                entity_type="ORGANIZATION",
                start=r.start,
                end=r.end + m.end(),
                score=max(r.score, 0.85),
                analysis_explanation=r.analysis_explanation,
            ))
        else:
            updated.append(r)
    return updated


def _extend_locations_with_zip(results, text):
    """Extend LOCATION entities backward to include a preceding zip code (XX-XXX)."""
    from presidio_analyzer import RecognizerResult

    extended = []
    for r in results:
        if r.entity_type != "LOCATION":
            extended.append(r)
            continue

        lookback = text[max(0, r.start - 10):r.start]
        m = _re.search(r"\d{2}-\d{3}\s*$", lookback)
        if m:
            new_start = max(0, r.start - 10) + m.start()
            extended.append(RecognizerResult(
                entity_type=r.entity_type,
                start=new_start,
                end=r.end,
                score=r.score,
                analysis_explanation=r.analysis_explanation,
            ))
        else:
            extended.append(r)
    return extended


def _extend_locations_with_numbers(results, text):
    """Extend LOCATION entities to include trailing street/apartment numbers.

    e.g. if spaCy detects "Długiej" but the text says "Długiej 15",
    extend the entity to cover "Długiej 15".
    Handles patterns like: 15, 42/8, 102/7, 23 m. 15
    """
    import re
    extended = []
    for r in results:
        if r.entity_type != "LOCATION":
            extended.append(r)
            continue

        end = r.end
        remaining = text[end:end + 20]  # look ahead up to 20 chars

        # Match optional space + number + optional /number + optional apartment (m./lok./lokal)
        m = re.match(r"([ \t]+\d+[a-zA-Z]?(?:[/]\d+)?(?:[ \t]+(?:m\.|lok\.|lokal)[ \t]*\d+)?)", remaining)
        if m:
            # Create a new result with extended end
            from presidio_analyzer import RecognizerResult
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
    """Merge adjacent ORG/PERSON entities that form a single company or firm name.

    Handles cases like:
    - "ByteForge Sp." (ORG) + "z o.o." (ORG) → one ORG
    - "Kancelaria" (ORG) + "Kosowicz" (PERSON) + "i" + "Piechota-Młot" (PERSON) +
      "spółka cywilna" (ORG) → one ORG

    Strategy: sort all ORG and PERSON entities by position, then merge sequences
    where entities are separated by short gaps (whitespace, "i", connectors).
    A sequence becomes ORG if it contains at least one ORG entity.
    """
    from presidio_analyzer import RecognizerResult
    import re

    mergeable_types = {"ORGANIZATION", "PERSON"}
    candidates = [r for r in results if r.entity_type in mergeable_types]
    others = [r for r in results if r.entity_type not in mergeable_types]

    if len(candidates) <= 1:
        return results

    candidates.sort(key=lambda r: r.start)

    # Build sequences of adjacent entities
    sequences: list[list] = [[candidates[0]]]

    for curr in candidates[1:]:
        prev = sequences[-1][-1]
        raw_gap = text[prev.end:curr.start]
        gap = raw_gap.strip()

        # Same-type merging: ORG+ORG with whitespace gap (e.g. "Sp." + "z o.o.")
        if prev.entity_type == "ORGANIZATION" and curr.entity_type == "ORGANIZATION":
            if len(raw_gap) <= 3 and (gap == "" or gap in ("i", "-", "&", "·")):
                sequences[-1].append(curr)
                continue

        # Cross-type merging: ORG+PERSON or PERSON+ORG only with "i" or "&" connector
        # (e.g. "Kosowicz i Piechota" in a firm name)
        # NOT "-" which is commonly used as em dash separator ("Zarządu - Martę")
        if prev.entity_type != curr.entity_type:
            if gap in ("i", "&") and "-" not in raw_gap:
                sequences[-1].append(curr)
                continue

        # PERSON+PERSON with "i" (co-founders: "Kosowicz i Piechota")
        if prev.entity_type == "PERSON" and curr.entity_type == "PERSON":
            if gap == "i":
                sequences[-1].append(curr)
                continue

        sequences.append([curr])

    merged_results = []
    absorbed = set()  # track IDs of entities absorbed into merges

    for seq in sequences:
        if len(seq) == 1:
            merged_results.append(seq[0])
            continue

        has_org = any(r.entity_type == "ORGANIZATION" for r in seq)

        if has_org:
            # Merge entire sequence into one ORG
            merged_results.append(RecognizerResult(
                entity_type="ORGANIZATION",
                start=seq[0].start,
                end=seq[-1].end,
                score=max(r.score for r in seq),
                analysis_explanation=seq[0].analysis_explanation,
            ))
            # Mark all PERSON entities in this sequence as absorbed
            for r in seq:
                if r.entity_type == "PERSON":
                    absorbed.add((r.start, r.end))
        else:
            # All PERSON — keep individually
            merged_results.extend(seq)

    # Extend merged ORGs to absorb trailing text up to and including a company legal form.
    # Handles: "ByteForge Sp." + " z o.o.", "Borys" + " i Partnerzy sp.p.",
    # "Kosowicz" + " i Piechota-Młot spółka cywilna", etc.
    import re
    LEGAL_FORMS = (
        r"sp(?:ółka)?\.?\s*(?:z\s*o\.?\s*o\.?|j\.|k\.|p\.)"
        r"|s\.?\s*c\.?"
        r"|s\.\s*a\.?|s\.?\s*a\."  # S.A. — require at least one dot to avoid matching "sa"
        r"|sp(?:ółka)?\.?\s+komandytowa"
        r"|spółka\s+cywilna"
        r"|spółka\s+partnerska"
        r"|z\s*o\.?\s*o\.?"
    )
    company_suffix = re.compile(
        r"(?:[\s\-][-\w\s]{0,30}?)?\s*(?:" + LEGAL_FORMS + r")",
        re.IGNORECASE
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
    # Filter stopwords FIRST, before merging (so "Zarządu" doesn't get merged with adjacent PERSON)
    pre_filtered = []
    for r in results:
        entity_text = text[r.start:r.end].strip()
        if r.entity_type in ("PERSON", "ORGANIZATION") and (
            entity_text in ENTITY_STOPWORDS or _is_legal_role(entity_text)
        ):
            continue
        if r.entity_type == "ORGANIZATION" and (entity_text.startswith("\u201e") or entity_text.startswith('"')):
            clean = entity_text.strip('\u201e\u201d"')
            if clean in ENTITY_STOPWORDS or _is_legal_role(clean):
                continue
        if r.entity_type == "LOCATION" and entity_text in LOCATION_STOPWORDS:
            continue
        if r.entity_type == "PERSON" and len(entity_text) <= 2:
            continue
        if r.entity_type == "LOCATION" and len(entity_text) <= 3:
            continue
        if r.entity_type == "PERSON" and any(c.isdigit() for c in entity_text):
            continue
        if r.entity_type in ("URL", "DATE_TIME"):
            continue
        pre_filtered.append(r)

    # Reclassify PERSON→ORG when followed by legal forms, then merge and extend
    pre_filtered = _reclassify_person_with_legal_form(pre_filtered, text)
    results = _merge_entity_sequences(pre_filtered, text)
    results = _extend_locations_with_numbers(results, text)
    results = _extend_locations_with_zip(results, text)

    result_map = {}
    filtered = results
    for r in filtered:
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
        entity_text = text[key[0]:key[1]]

        if "KRS" in types and "NIP" in types and entity_text.startswith("0000"):
            deduped.extend(r for r in group if r.entity_type == "KRS")
            continue
        if "NIP" in types and ("KRS" in types or "PHONE_NUMBER" in types):
            deduped.extend(r for r in group if r.entity_type == "NIP")
            continue
        if "PESEL" in types:
            deduped.extend(r for r in group if r.entity_type == "PESEL")
            continue
        if "IBAN_CODE" in types and "CREDIT_CARD" in types:
            deduped.extend(r for r in group if r.entity_type == "IBAN_CODE")
            continue

        best = max(group, key=lambda r: r.score)
        deduped.append(best)

    # Final pass: remove entities whose span falls entirely inside a larger ID_CARD span
    id_spans = [(r.start, r.end) for r in deduped if r.entity_type == "ID_CARD"]
    if id_spans:
        deduped = [
            r for r in deduped
            if r.entity_type == "ID_CARD" or not any(
                s <= r.start and r.end <= e for s, e in id_spans
            )
        ]

    return deduped


def analyze_text(text, language="pl"):
    analyzer = get_analyzer()
    results = analyzer.analyze(text=text, language=language)
    return post_process(results, text)
