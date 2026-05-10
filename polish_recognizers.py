from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts


class PeselRecognizer(PatternRecognizer):
    PATTERNS = [
        Pattern(
            name="pesel_pattern",
            regex=r"\b\d{11}\b",
            score=0.4,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="PESEL",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=["pesel", "nr ewidencyjny", "numer ewidencyjny"],
        )

    def validate_result(self, pattern_text):
        if len(pattern_text) != 11 or not pattern_text.isdigit():
            return False
        weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
        checksum = sum(int(d) * w for d, w in zip(pattern_text[:10], weights)) % 10
        checksum = (10 - checksum) % 10
        return checksum == int(pattern_text[10])


class NipRecognizer(PatternRecognizer):
    PATTERNS = [
        Pattern(
            name="nip_dashed",
            regex=r"\b\d{3}-\d{3}-\d{2}-\d{2}\b",
            score=0.7,  # dashed format is strong signal
        ),
        Pattern(
            name="nip_plain",
            regex=r"\b\d{10}\b",
            score=0.4,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="NIP",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=["nip", "numer identyfikacji podatkowej", "identyfikacji podatkowej"],
        )

    def validate_result(self, pattern_text):
        digits = "".join(c for c in pattern_text if c.isdigit())
        if len(digits) != 10:
            return False
        weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
        checksum = sum(int(d) * w for d, w in zip(digits[:9], weights)) % 11
        if checksum == 10:
            return False
        return checksum == int(digits[9])


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

    def validate_result(self, pattern_text):
        digits = pattern_text
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


class KrsRecognizer(PatternRecognizer):
    """KRS numbers are 10 digits, typically starting with 0000.
    Without checksum, we require the word KRS nearby (context) and
    boost numbers starting with 0000."""
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
    """Recognizes Polish IBAN numbers in various formats:
    PL 61 1090 1014 0000 0712 1981 2874
    PL61109010140000071219812874
    61 1090 1014 0000 0712 1981 2874
    """
    PATTERNS = [
        Pattern(
            name="iban_pl_spaced",
            regex=r"\bPL\s?\d{2}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\b",
            score=0.9,
        ),
        Pattern(
            name="iban_pl_compact",
            regex=r"\bPL\s?\d{26}\b",
            score=0.9,
        ),
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
    """Catches Polish phone number formats that Presidio's default misses:
    +48 12 634 22 87   (landline with country code)
    12 634 22 87       (landline without country code)
    48-601-234-567     (mobile dashed with country code)
    0048 512 345 678   (mobile with 00 prefix)
    +48 58 620 11 47   (landline)
    """
    PATTERNS = [
        # +48 or 0048 followed by 9 digits in groups
        Pattern(
            name="pl_phone_intl",
            regex=r"(?:\+48|0048)\s?\d{2,3}[\s-]?\d{3}[\s-]?\d{2,3}[\s-]?\d{0,2}\b",
            score=0.5,
        ),
        # Dashed format: 48-601-234-567
        Pattern(
            name="pl_phone_dashed",
            regex=r"\b48-\d{3}-\d{3}-\d{3}\b",
            score=0.6,
        ),
        # Landline without country code: 12 634 22 87
        Pattern(
            name="pl_phone_landline",
            regex=r"\b\d{2}\s\d{3}\s\d{2}\s\d{2}\b",
            score=0.3,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="PHONE_NUMBER",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=[
                "tel", "tel.", "telefon", "telefonu", "telefoniczn",
                "kontakt", "mobile", "komórk", "numer telefonu",
            ],
        )
