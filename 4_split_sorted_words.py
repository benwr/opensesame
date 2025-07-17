from collections import defaultdict

by_cat = defaultdict(list)
with open("3_sorted_words.txt") as f:
    for i, line in enumerate(f):
        cat, word = line.strip().split()
        by_cat[cat].append((i, word))


last_in_cat = {
    "NORMAL": 86646,
    "NAME": 21000,
    "PLACE": 35000,
    "ACRONYM": 34000,
    "FOREIGN": 1100,
    "MISSPELLED": 6000,
    "UNKNOWN": 10000,
}

# Sort the words within each category
for cat, words in by_cat.items():
    for i, word in words:
        if i < last_in_cat[cat]:
            print(word)
