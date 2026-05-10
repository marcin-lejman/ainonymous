"""
Evaluation script for the anonymization pipeline.

Compares Presidio + custom recognizer output against ground truth annotations.
Reports precision, recall, and F1 per entity type and overall.

Usage:
    python eval.py                    # run all contracts in test_suite/
    python eval.py contract_03        # run a single contract
    python eval.py --verbose          # show every match/miss detail
"""

import json
import sys
from pathlib import Path

from analyzer import build_analyzer


def load_ground_truth(json_path):
    """Load expected entities from annotation file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["entities"]


def find_entity_in_text(text, entity_text):
    """Find all occurrences of entity_text in text, return list of (start, end)."""
    positions = []
    start = 0
    while True:
        idx = text.find(entity_text, start)
        if idx < 0:
            break
        positions.append((idx, idx + len(entity_text)))
        start = idx + 1
    return positions


def normalize_type(entity_type):
    """Map various type names to canonical forms for comparison."""
    mapping = {
        "PERSON": "PERSON",
        "LOCATION": "LOCATION",
        "ORGANIZATION": "ORGANIZATION",
        "EMAIL_ADDRESS": "EMAIL_ADDRESS",
        "PHONE_NUMBER": "PHONE_NUMBER",
        "PESEL": "PESEL",
        "NIP": "NIP",
        "REGON": "REGON",
        "KRS": "KRS",
        "IBAN_CODE": "IBAN_CODE",
        "CREDIT_CARD": "IBAN_CODE",  # Presidio sometimes tags IBANs as credit cards
        "CONTEXTUAL": "CONTEXTUAL",
        "URL": "URL",
        "DATE_TIME": "DATE_TIME",
    }
    return mapping.get(entity_type, entity_type)


def spans_overlap(span_a, span_b):
    """Check if two (start, end) spans overlap."""
    return not (span_a[1] <= span_b[0] or span_a[0] >= span_b[1])


def evaluate_contract(contract_path, json_path, analyzer, verbose=False):
    """Evaluate a single contract. Returns (true_positives, false_positives, false_negatives) dicts by type."""
    with open(contract_path, "r", encoding="utf-8") as f:
        text = f.read()

    expected = load_ground_truth(json_path)

    # Run analyzer
    results = analyzer.analyze(text=text, language="pl")

    # Build detected entities list
    detected = []
    for r in results:
        detected.append({
            "text": text[r.start:r.end],
            "type": normalize_type(r.entity_type),
            "start": r.start,
            "end": r.end,
            "score": r.score,
        })

    # Build expected spans
    expected_spans = []
    for ent in expected:
        if ent["type"] == "CONTEXTUAL":
            continue  # Skip contextual — those are for the LLM pass
        positions = find_entity_in_text(text, ent["text"])
        if not positions:
            if verbose:
                print(f"  ⚠️  Ground truth text not found: '{ent['text'][:50]}' ({ent['type']})")
            # Try to still count it as a false negative
            expected_spans.append({
                "text": ent["text"],
                "type": normalize_type(ent["type"]),
                "start": -1,
                "end": -1,
                "matched": False,
            })
        else:
            for start, end in positions:
                expected_spans.append({
                    "text": ent["text"],
                    "type": normalize_type(ent["type"]),
                    "start": start,
                    "end": end,
                    "matched": False,
                })

    # Match detected against expected
    detected_matched = [False] * len(detected)

    for ei, exp in enumerate(expected_spans):
        if exp["start"] < 0:
            continue
        for di, det in enumerate(detected):
            if detected_matched[di]:
                continue
            if normalize_type(det["type"]) == exp["type"] and spans_overlap(
                (det["start"], det["end"]), (exp["start"], exp["end"])
            ):
                exp["matched"] = True
                detected_matched[di] = True
                break

    # Also try matching by type + text overlap for cases where spans differ slightly
    for ei, exp in enumerate(expected_spans):
        if exp["matched"] or exp["start"] < 0:
            continue
        for di, det in enumerate(detected):
            if detected_matched[di]:
                continue
            if normalize_type(det["type"]) == exp["type"]:
                # Check if detected text is substring of expected or vice versa
                if det["text"] in exp["text"] or exp["text"] in det["text"]:
                    exp["matched"] = True
                    detected_matched[di] = True
                    break

    # Tally results per type
    tp = {}  # true positives
    fp = {}  # false positives
    fn = {}  # false negatives

    for exp in expected_spans:
        t = exp["type"]
        if exp["matched"]:
            tp[t] = tp.get(t, 0) + 1
        else:
            fn[t] = fn.get(t, 0) + 1
            if verbose:
                print(f"  ❌ MISSED  {t:17} '{exp['text'][:50]}'")

    for di, det in enumerate(detected):
        if not detected_matched[di]:
            t = normalize_type(det["type"])
            fp[t] = fp.get(t, 0) + 1
            if verbose:
                print(f"  ➕ EXTRA   {t:17} '{det['text'][:50]}' (score: {det['score']:.2f})")

    for exp in expected_spans:
        if exp["matched"] and verbose:
            print(f"  ✅ FOUND   {exp['type']:17} '{exp['text'][:50]}'")

    return tp, fp, fn


def print_report(all_tp, all_fp, all_fn):
    """Print a summary table of precision, recall, F1 per entity type."""
    all_types = sorted(set(list(all_tp.keys()) + list(all_fp.keys()) + list(all_fn.keys())))

    print()
    print(f"{'Entity Type':20} {'TP':>4} {'FP':>4} {'FN':>4} {'Prec':>7} {'Recall':>7} {'F1':>7}")
    print("─" * 65)

    total_tp = total_fp = total_fn = 0

    for t in all_types:
        tp = all_tp.get(t, 0)
        fp = all_fp.get(t, 0)
        fn = all_fn.get(t, 0)
        total_tp += tp
        total_fp += fp
        total_fn += fn

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0

        prec_bar = "█" * int(prec * 10) + "░" * (10 - int(prec * 10))
        rec_bar = "█" * int(rec * 10) + "░" * (10 - int(rec * 10))

        print(f"{t:20} {tp:4} {fp:4} {fn:4} {prec:6.1%} {rec:6.1%} {f1:6.1%}")

    print("─" * 65)
    prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
    print(f"{'TOTAL':20} {total_tp:4} {total_fp:4} {total_fn:4} {prec:6.1%} {rec:6.1%} {f1:6.1%}")
    print()


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    print("Loading analyzer...")
    analyzer = build_analyzer()

    test_dir = Path("test_suite")

    if args:
        # Run specific contract(s)
        contracts = []
        for name in args:
            txt = test_dir / f"{name}.txt"
            js = test_dir / f"{name}_expected.json"
            if txt.exists() and js.exists():
                contracts.append((txt, js))
            else:
                print(f"Not found: {txt} or {js}")
    else:
        # Run all contracts
        contracts = []
        for txt in sorted(test_dir.glob("contract_*.txt")):
            js = test_dir / f"{txt.stem}_expected.json"
            if js.exists():
                contracts.append((txt, js))

    if not contracts:
        print("No contracts found in test_suite/")
        return

    all_tp, all_fp, all_fn = {}, {}, {}

    for txt_path, json_path in contracts:
        print(f"\n{'='*60}")
        print(f"📄 {txt_path.name}")
        print(f"{'='*60}")

        tp, fp, fn = evaluate_contract(txt_path, json_path, analyzer, verbose=verbose)

        for t, v in tp.items():
            all_tp[t] = all_tp.get(t, 0) + v
        for t, v in fp.items():
            all_fp[t] = all_fp.get(t, 0) + v
        for t, v in fn.items():
            all_fn[t] = all_fn.get(t, 0) + v

        # Per-contract mini summary
        c_tp = sum(tp.values())
        c_fp = sum(fp.values())
        c_fn = sum(fn.values())
        c_prec = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 0
        c_rec = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 0
        print(f"  Summary: {c_tp} found, {c_fn} missed, {c_fp} extra  (recall: {c_rec:.0%})")

    print(f"\n{'='*60}")
    print("OVERALL RESULTS")
    print(f"{'='*60}")
    print_report(all_tp, all_fp, all_fn)


if __name__ == "__main__":
    main()
