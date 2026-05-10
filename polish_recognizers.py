from presidio_analyzer import Pattern, PatternRecognizer


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
            name="nip_pattern",
            regex=r"\b\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b|\b\d{10}\b",
            score=0.4,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="NIP",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=["nip", "numer identyfikacji podatkowej"],
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
    PATTERNS = [
        Pattern(name="krs_pattern", regex=r"\b\d{10}\b", score=0.2),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="KRS",
            patterns=self.PATTERNS,
            supported_language="pl",
            context=["krs", "krajowy rejestr sądowy", "rejestr przedsiębiorców"],
        )
