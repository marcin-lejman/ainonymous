import re
from presidio_analyzer import (
    AnalysisExplanation,
    Pattern,
    PatternRecognizer,
    RecognizerResult,
)


class PeselRecognizer(PatternRecognizer):
    PATTERNS = [
        Pattern(name="pesel_pattern", regex=r"\b\d{11}\b", score=0.4),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="PESEL",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=["pesel", "nr ewidencyjny", "numer ewidencyjny"],
        )

    @staticmethod
    def _checksum_valid(digits):
        weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
        checksum = sum(int(d) * w for d, w in zip(digits[:10], weights)) % 10
        checksum = (10 - checksum) % 10
        return checksum == int(digits[10])

    def analyze(self, text, entities, nlp_artifacts=None):
        results = super().analyze(text, entities, nlp_artifacts)
        text_lower = text.lower()
        for m in re.finditer(r"\b\d{11}\b", text):
            if self._checksum_valid(m.group()):
                continue
            window_start = max(0, m.start() - 50)
            window = text_lower[window_start:m.start()]
            if "pesel" in window or "ewidencyjny" in window:
                results.append(RecognizerResult(
                    entity_type="PESEL",
                    start=m.start(),
                    end=m.end(),
                    score=0.75,
                    analysis_explanation=AnalysisExplanation(
                        recognizer=self.__class__.__name__,
                        original_score=0.75,
                        pattern_name="pesel_context_fallback",
                        pattern=r"\b\d{11}\b",
                        validation_result=0.75,
                    ),
                ))
        return results

    def validate_result(self, pattern_text):
        if len(pattern_text) != 11 or not pattern_text.isdigit():
            return False
        return self._checksum_valid(pattern_text)


class NipRecognizer(PatternRecognizer):
    PATTERNS = [
        Pattern(name="nip_dashed", regex=r"\b\d{3}-\d{3}-\d{2}-\d{2}\b", score=0.7),
        Pattern(name="nip_plain", regex=r"\b\d{10}\b", score=0.4),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="NIP",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=["nip", "numer identyfikacji podatkowej", "identyfikacji podatkowej"],
        )

    @staticmethod
    def _checksum_valid(digits):
        weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
        checksum = sum(int(d) * w for d, w in zip(digits[:9], weights)) % 11
        if checksum == 10:
            return False
        return checksum == int(digits[9])

    def analyze(self, text, entities, nlp_artifacts=None):
        results = super().analyze(text, entities, nlp_artifacts)
        text_lower = text.lower()
        for m in re.finditer(r"\b\d{3}-\d{3}-\d{2}-\d{2}\b", text):
            digits = "".join(c for c in m.group() if c.isdigit())
            if self._checksum_valid(digits):
                continue
            window_start = max(0, m.start() - 30)
            window = text_lower[window_start:m.start()]
            if "nip" in window:
                results.append(RecognizerResult(
                    entity_type="NIP",
                    start=m.start(),
                    end=m.end(),
                    score=0.75,
                    analysis_explanation=AnalysisExplanation(
                        recognizer=self.__class__.__name__,
                        original_score=0.75,
                        pattern_name="nip_context_fallback",
                        pattern=r"\b\d{3}-\d{3}-\d{2}-\d{2}\b",
                        validation_result=0.75,
                    ),
                ))
        return results

    def validate_result(self, pattern_text):
        digits = "".join(c for c in pattern_text if c.isdigit())
        if len(digits) != 10:
            return False
        return self._checksum_valid(digits)


class RegonRecognizer(PatternRecognizer):
    PATTERNS = [
        Pattern(name="regon_9", regex=r"\b\d{9}\b", score=0.3),
        Pattern(name="regon_14", regex=r"\b\d{14}\b", score=0.3),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="REGON",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=["regon"],
        )

    @staticmethod
    def _checksum_valid(digits):
        if len(digits) == 9:
            weights = [8, 9, 2, 3, 4, 5, 6, 7]
            checksum = sum(int(d) * w for d, w in zip(digits[:8], weights)) % 11
            checksum = checksum if checksum != 10 else 0
            return checksum == int(digits[8])
        elif len(digits) == 14:
            weights = [2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8]
            checksum = sum(int(d) * w for d, w in zip(digits[:13], weights)) % 11
            checksum = checksum if checksum != 10 else 0
            return checksum == int(digits[13])
        return False

    def analyze(self, text, entities, nlp_artifacts=None):
        results = super().analyze(text, entities, nlp_artifacts)
        text_lower = text.lower()
        for m in re.finditer(r"\b\d{9}\b", text):
            if self._checksum_valid(m.group()):
                continue
            window_start = max(0, m.start() - 30)
            window = text_lower[window_start:m.start()]
            if "regon" in window:
                results.append(RecognizerResult(
                    entity_type="REGON",
                    start=m.start(),
                    end=m.end(),
                    score=0.75,
                    analysis_explanation=AnalysisExplanation(
                        recognizer=self.__class__.__name__,
                        original_score=0.75,
                        pattern_name="regon_context_fallback",
                        pattern=r"\b\d{9}\b",
                        validation_result=0.75,
                    ),
                ))
        return results

    def validate_result(self, pattern_text):
        if not pattern_text.isdigit():
            return False
        return self._checksum_valid(pattern_text)


class KrsRecognizer(PatternRecognizer):
    PATTERNS = [
        Pattern(name="krs_0000", regex=r"\b0000\d{6}\b", score=0.4),
        Pattern(name="krs_generic", regex=r"\b\d{10}\b", score=0.01),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="KRS",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=["krs", "krajowy rejestr sądowy", "rejestr przedsiębiorców"],
        )


class PolishIbanRecognizer(PatternRecognizer):
    PATTERNS = [
        Pattern(
            name="iban_pl_spaced",
            regex=r"\bPL\s?\d{2}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\b",
            score=0.9,
        ),
        Pattern(name="iban_pl_compact", regex=r"\bPL\s?\d{26}\b", score=0.9),
        Pattern(
            name="iban_no_prefix_spaced",
            regex=r"\b\d{2}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\b",
            score=0.3,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="IBAN_CODE",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=[
                "rachunek", "konto", "nr rachunku", "numer rachunku",
                "rachunek bankowy", "nr konta", "iban", "przelew",
                "wpłat", "wpłata",
            ],
        )


class PolishPhoneRecognizer(PatternRecognizer):
    PATTERNS = [
        # +48 or 0048 followed by 9 digits in groups
        Pattern(
            name="pl_phone_intl",
            regex=r"(?:\+48|0048)\s?\d{2,3}[\s-]?\d{3}[\s-]?\d{2,3}[\s-]?\d{0,2}\b",
            score=0.5,
        ),
        # 48-601-234-567
        Pattern(name="pl_phone_dashed", regex=r"\b48-\d{3}-\d{3}-\d{3}\b", score=0.6),
        # Landline: 12 634 22 87
        Pattern(name="pl_phone_landline", regex=r"\b\d{2}\s\d{3}\s\d{2}\s\d{2}\b", score=0.3),
        # Mobile no country code: 601 234 567 (Polish mobile starts with 5-8)
        Pattern(name="pl_phone_mobile_9", regex=r"\b[5-8]\d{2}\s\d{3}\s\d{3}\b", score=0.3),
        # Mobile compact: 601234567
        Pattern(name="pl_phone_mobile_compact", regex=r"\b[5-8]\d{8}\b", score=0.2),
        # With parens: (12) 345 67 89
        Pattern(name="pl_phone_parens", regex=r"\(\d{2}\)\s?\d{3}\s?\d{2}\s?\d{2}", score=0.4),
        # Dashed 9-digit: 601-234-567
        Pattern(name="pl_phone_dashed_9", regex=r"\b[5-8]\d{2}-\d{3}-\d{3}\b", score=0.4),
        # Dashed landline: 12-345-67-89
        Pattern(name="pl_phone_dashed_landline", regex=r"\b\d{2}-\d{3}-\d{2}-\d{2}\b", score=0.3),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="PHONE_NUMBER",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=[
                "tel", "tel.", "telefon", "telefonu", "telefoniczn",
                "kontakt", "mobile", "komórk", "numer telefonu",
                "fax", "faks",
            ],
        )


class PolishIdCardRecognizer(PatternRecognizer):
    """Recognizes Polish national ID card (dowód osobisty) numbers.

    Format: 3 letters + 6 digits (e.g. ABA300000)
    Letters: A-Z excluding O and Q (24 letters)
    Checksum: 4th character (first digit) is calculated using weights 7,3,1
    on all 9 characters mapped to values (A=10, B=11, ..., Z=35, 0-9 as-is).

    Also catches numbers near context words like "dowód" even with invalid checksum.
    """
    PATTERNS = [
        # Combined format: ABA300000
        Pattern(
            name="id_card_combined",
            regex=r"\b[A-NP-Z]{3}\d{6}\b",
            score=0.3,
        ),
        # Split format: seria AVR nr 582914 / seria AVR numer 582914
        Pattern(
            name="id_card_split",
            regex=r"\bseria\s+[A-NP-Z]{3}\s+(?:nr|numer)\s+\d{6}\b",
            score=0.7,
        ),
        # Split without "seria": AVR nr 582914 / AVR 582914 (near context)
        Pattern(
            name="id_card_series_nr",
            regex=r"\b[A-NP-Z]{3}\s+(?:nr\s+)?\d{6}\b",
            score=0.2,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="ID_CARD",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=[
                "dowód", "dowodu", "dowodem", "dowód osobisty", "dowodu osobistego",
                "seria i numer", "seria", "legitymując", "tożsamoś",
                "dokument tożsamości",
            ],
        )

    @staticmethod
    def _char_value(c):
        if c.isdigit():
            return int(c)
        return ord(c) - ord('A') + 10

    @staticmethod
    def _checksum_valid(id_number):
        if len(id_number) != 9:
            return False
        weights = [7, 3, 1, 7, 3, 1, 7, 3, 1]
        try:
            total = sum(
                PolishIdCardRecognizer._char_value(c) * w
                for c, w in zip(id_number, weights)
            )
            return total % 10 == 0
        except (ValueError, IndexError):
            return False

    def analyze(self, text, entities, nlp_artifacts=None):
        results = super().analyze(text, entities, nlp_artifacts)
        # Context fallback: catch ID card numbers near "dowód" even without valid checksum
        text_lower = text.lower()
        for m in re.finditer(r"\b[A-NP-Z]{3}\d{6}\b", text):
            if self._checksum_valid(m.group()):
                continue  # already caught by pattern + validation
            window_start = max(0, m.start() - 60)
            window = text_lower[window_start:m.start()]
            if any(kw in window for kw in ("dowód", "dowodu", "dowodem", "legitymując", "tożsamoś", "seria")):
                results.append(RecognizerResult(
                    entity_type="ID_CARD",
                    start=m.start(),
                    end=m.end(),
                    score=0.75,
                    analysis_explanation=AnalysisExplanation(
                        recognizer=self.__class__.__name__,
                        original_score=0.75,
                        pattern_name="id_card_context_fallback",
                        pattern=r"\b[A-NP-Z]{3}\d{6}\b",
                        validation_result=0.75,
                    ),
                ))
        return results

    def validate_result(self, pattern_text):
        # Accept any structurally valid ID card format.
        # Checksum validation happens at score level (valid checksum = higher score),
        # but we don't reject on checksum alone since documents often contain
        # fictional or mistyped numbers.
        return True


class PolishAddressRecognizer(PatternRecognizer):
    """Catches Polish addresses that spaCy NER misses.

    Detects patterns like:
    - ul. Marszałkowska 12/4
    - os. Tysiąclecia 14 m. 3
    - al. Jana Pawła II 45/2
    - pl. Wolności 7/12
    - Rynek 14/3
    - ul. bpa Wł. Bandurskiego 12/3
    - ul. Generała Władysława Sikorskiego 88 m. 4
    """
    # Polish address prefixes — abbreviated and declined forms
    _PREFIX = r"(?:ul\.|ulicy|ulicą|ulic[eę]|os\.|osiedl[eua]|al\.|alei|aleją|ale[ię]|pl\.|placu|plac|Rynek|rynku)"
    # Street name: one or more capitalized words, possibly with abbreviated titles
    _PL_UPPER = r"A-ZĄĆĘŁŃÓŚŹŻ"
    _PL_LOWER = r"a-ząćęłńóśźż"
    _STREET = r"(?:\s+(?:[" + _PL_UPPER + r"][" + _PL_LOWER + r"]+\.?|[A-Z]\.))+"
    # Building number with optional apartment (m./lok./lokal)
    _NUMBER = r"\s+\d+[a-zA-Z]?(?:/\d+)?(?:\s+(?:m\.|lok\.|lokal)\s*\d+)?"

    PATTERNS = [
        # Full address: prefix + street name + number
        Pattern(
            name="pl_address_full",
            regex=_PREFIX + _STREET + _NUMBER,
            score=0.7,
        ),
        # Rynek (no prefix needed): Rynek 14/3
        Pattern(
            name="pl_address_rynek",
            regex=r"\bRynek\s+\d+(?:/\d+)?",
            score=0.6,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="LOCATION",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=[
                "zamieszkał", "siedzib", "adres", "położon", "przy",
                "zameldowan", "korespondencj",
            ],
        )


class PolishZipCityRecognizer(PatternRecognizer):
    """Catches zip code + city patterns that spaCy misses.

    Detects: 21-500 Biała Podlaska, 42-600 Tarnowskie Góry, etc.
    Polish zip codes are always XX-XXX format.
    """
    PATTERNS = [
        # Zip + 1-3 word city name
        Pattern(
            name="pl_zip_city",
            regex=r"\b\d{2}-\d{3}\s+[A-ZŁŚŻŹĆŃÓ][a-złśżźćńó]+(?:[- ][A-ZŁŚŻŹĆŃÓ][a-złśżźćńó]+){0,2}\b",
            score=0.4,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="LOCATION",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=[
                "zamieszkał", "siedzib", "adres", "położon",
                "kod pocztowy", "miejscowość",
            ],
        )
