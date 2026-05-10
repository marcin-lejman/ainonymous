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

POLISH_LEGAL_STOPWORDS = {
    "Wynajmującej", "Wynajmującego", "Wynajmujący", "Wynajmującą",
    "Najemcy", "Najemca", "Najemcą",
    "Kupującej", "Kupującego", "Kupująca", "Kupujący",
    "Sprzedającego", "Sprzedającej", "Sprzedający",
    "Obdarowanego", "Obdarowanemu", "Obdarowany",
    "Mocodawcy", "Mocodawca", "Mocodawcą",
    "Pełnomocnika", "Pełnomocnik",
    "Darczyńcy", "Darczyńca",
    "Zleceniobiorcy", "Zleceniobiorca",
    "Zleceniodawcy", "Zleceniodawca",
    "Zamawiającego", "Zamawiający", "Zamawiającą",
    "Wykonawcy", "Wykonawca", "Wykonawcą",
    "Pożyczkodawcy", "Pożyczkodawca",
    "Pożyczkobiorcy", "Pożyczkobiorca",
    "Otrzymującej", "Otrzymującego", "Otrzymująca",
    "Zawarta", "Zawarto",
    "A.", "B.", "C.", "D.",
    "Zarządu", "Zarząd",
    "Stron", "Strony", "Stronom",
    "Stronę Ujawniającą", "Stronie Otrzymującej",
    "Stronę Ujawniającą Stronie Otrzymującej",
    "Strony Ujawniającej",
    "Pracodawcą", "Pracodawcy", "Pracodawca",
    "KRS", "ZUS", "PIT", "CIT", "VAT", "UJ",
    "ZACHOWANIU", "Lokalu", "Lokal",
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

    _analyzer_instance = analyzer
    return analyzer


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

        # Match optional space + number + optional /number or m. number
        m = re.match(r"(\s+\d+(?:[/]\d+)?(?:\s+m\.\s*\d+)?)", remaining)
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


def _merge_adjacent_orgs(results, text):
    """Merge ORGANIZATION entities that are adjacent or separated only by whitespace.

    spaCy often splits 'ByteForge Sp.' and 'z o.o.' into two entities.
    This merges them into one.
    """
    from presidio_analyzer import RecognizerResult
    orgs = [r for r in results if r.entity_type == "ORGANIZATION"]
    others = [r for r in results if r.entity_type != "ORGANIZATION"]

    if len(orgs) <= 1:
        return results

    orgs.sort(key=lambda r: r.start)
    merged = [orgs[0]]

    for curr in orgs[1:]:
        prev = merged[-1]
        gap = text[prev.end:curr.start]
        # Merge if gap is only whitespace (up to 3 chars)
        if len(gap) <= 3 and gap.strip() == "":
            merged[-1] = RecognizerResult(
                entity_type="ORGANIZATION",
                start=prev.start,
                end=curr.end,
                score=max(prev.score, curr.score),
                analysis_explanation=prev.analysis_explanation,
            )
        else:
            merged.append(curr)

    return others + merged


def post_process(results, text):
    # Merge adjacent ORG entities (e.g. "ByteForge Sp." + "z o.o.")
    results = _merge_adjacent_orgs(results, text)
    # Extend locations to include street numbers
    results = _extend_locations_with_numbers(results, text)

    filtered = []
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
        if r.entity_type in ("URL", "DATE_TIME"):
            continue
        filtered.append(r)

    result_map = {}
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

    return deduped


def analyze_text(text, language="pl"):
    analyzer = get_analyzer()
    results = analyzer.analyze(text=text, language=language)
    return post_process(results, text)
