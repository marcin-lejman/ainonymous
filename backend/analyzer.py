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


def post_process(results, text):
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
