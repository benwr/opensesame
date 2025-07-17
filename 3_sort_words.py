import os
import sys

from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

# ---------- Tunables ----------
MODEL           = "gpt-4o-mini"       # any chat-capable model works
RATE_LIMIT_S    = 0.001                # seconds between calls (simple back-off)
MAX_WORKERS = 48
RETRY_ATTEMPTS = 5
RETRY_BACKOFF = 2.0
SYSTEM_MSG      = (
    "You're part of a system for sorting words into categories. The categories are:"
    " - NAME (e.g. 'john', 'mckinley', 'jesus', ...) \n"
    " - PLACE (e.g. 'france', 'doha', 'chengdu', ...) \n"
    " - ACRONYM (e.g. 'http', 'usa', 'darpa', ...)\n"
    " - FOREIGN (e.g. 'bonjour', 'shao', 'los', ...)\n"
    " - MISSPELLED (e.g. 'stollen', 'wahine', 'teh', ...)\n"
    " - NORMAL (e.g. 'food', 'ran', 'clearly', 'missing', 'forward', ...)\n"
    " - UNKNOWN (anything else)\n"
    "You will be given a word in lowercase, and you must categorize it into one "
    "of these categories. Respond with exactly one of the category names above "
    "(NAME, PLACE, ACRONYM, FOREIGN, MISSPELLED, NORMAL, UNKNOWN), and "
    "no other text."
)
# ---------- End tunables ----------

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def categorize(word: str) -> str:
    result = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": word},
        ],
        max_tokens=4,
        temperature=1.0,
    ).choices[0].message.content.strip().upper()

    if result == "UNKNOWN":
        result = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_MSG},
                {"role": "user", "content": word},
            ],
            max_tokens=4,
            temperature=1.0,
        ).choices[0].message.content.strip().upper()

    return result

if len(sys.argv) > 1:
    infn = sys.argv[1]
else:
    infn = "2_pronounceable_words.txt"
with open(infn) as f:
    words = [line.strip() for line in f.readlines()]

def main() -> None:
    results = [""] * len(words)  # preserve output order

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_to_idx = {
            pool.submit(categorize, w): i for i, w in enumerate(words)
        }

        for fut in as_completed(future_to_idx):
            idx = future_to_idx[fut]
            if idx % 500 == 0:
                print(idx, file=sys.stderr)
            word = words[idx]
            try:
                results[idx] = fut.result()
            except Exception as exc:                                   # noqa: BLE001
                print(f"# error on {word!r}: {exc}", file=sys.stderr)

    # Emit results in original order
    for word, cat in zip(words, results, strict=True):
        print(cat, word)
        if cat not in ["NAME", "PLACE", "ACRONYM", "FOREIGN", "MISSPELLED", "UNKNOWN","NORMAL"]:
            print(cat, word, file=sys.stderr)


if __name__ == "__main__":
    main()
