"""
Prepare training data for Nebius fine-tuning.

Reads every *.jsonl file under training/data/raw/, validates each example,
strips everything except the `conversation` field (the only field Nebius
fine-tuning consumes), and writes a shuffled train/val split to
training/data/processed/.
"""

import glob
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

RAW_DIR = Path(__file__).parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent / "data" / "processed"
VAL_FRACTION = 0.1
SHUFFLE_SEED = 42


def load_examples(raw_dir: Path):
    examples = []
    skipped = Counter()
    decoder = json.JSONDecoder()

    for path in sorted(glob.glob(str(raw_dir / "*.jsonl"))):
        text = Path(path).read_text()
        idx, length = 0, len(text)

        while idx < length:
            while idx < length and text[idx].isspace():
                idx += 1
            if idx >= length:
                break

            try:
                obj, end = decoder.raw_decode(text, idx)
            except json.JSONDecodeError:
                # Entries may be pretty-printed across multiple lines, so a
                # single malformed line doesn't tell us where the next valid
                # entry starts; resync at the next blank line.
                skipped["invalid_json"] += 1
                next_blank = text.find("\n\n", idx)
                idx = next_blank if next_blank != -1 else length
                continue
            idx = end

            conversation = obj.get("conversation")
            if not conversation or len(conversation) < 2:
                skipped["missing_or_short_conversation"] += 1
                continue

            if any("role" not in turn or "content" not in turn for turn in conversation):
                skipped["malformed_turn"] += 1
                continue

            examples.append({
                "conversation": conversation,
                "primary_category": obj.get("primary_category", "general"),
                "difficulty": obj.get("difficulty", "medium"),
            })

    return examples, skipped


def dedup(examples):
    seen = {}
    unique = []
    duplicates = 0

    for ex in examples:
        key = hashlib.sha256(
            json.dumps(ex["conversation"], sort_keys=True).encode()
        ).hexdigest()
        if key in seen:
            duplicates += 1
            continue
        seen[key] = True
        unique.append(ex)

    return unique, duplicates


def split(examples, val_fraction, seed):
    shuffled = examples[:]
    random.Random(seed).shuffle(shuffled)
    val_count = max(1, round(len(shuffled) * val_fraction)) if shuffled else 0
    return shuffled[val_count:], shuffled[:val_count]


def write_jsonl(path, examples):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for ex in examples:
            f.write(json.dumps({"conversation": ex["conversation"]}) + "\n")


def main():
    examples, skipped = load_examples(RAW_DIR)
    print(f"Loaded {len(examples)} valid examples from {RAW_DIR}")
    if skipped:
        print(f"Skipped: {dict(skipped)}")

    examples, duplicates = dedup(examples)
    if duplicates:
        print(f"Warning: removed {duplicates} exact-duplicate example(s)")

    train, val = split(examples, VAL_FRACTION, SHUFFLE_SEED)
    write_jsonl(PROCESSED_DIR / "train.jsonl", train)
    write_jsonl(PROCESSED_DIR / "val.jsonl", val)
    print(f"Wrote {len(train)} train / {len(val)} val examples to {PROCESSED_DIR}")

    by_category = Counter(ex["primary_category"] for ex in examples)
    by_difficulty = Counter(ex["difficulty"] for ex in examples)
    print(f"By category: {dict(by_category)}")
    print(f"By difficulty: {dict(by_difficulty)}")


if __name__ == "__main__":
    main()
