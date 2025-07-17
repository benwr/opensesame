all_words: set[str] = set()
with open("cmudict-0.7b", errors="ignore") as f:
    for line in f:
        if not line.strip() or line.startswith(";"):
            continue
        word, *pron = line.strip().split()
        all_words.add(word.lower())

with open("1_words_common.txt") as f:
    for line in f:
        if not line.strip():
            continue
        word, *pron = line.strip().split()
        if word.lower() in all_words:
            print(word)
