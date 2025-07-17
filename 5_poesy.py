import itertools
import math
import random
import re
import sys
from collections import defaultdict

VOWELS = {
    "AA","AE","AH","AO","AW","AY",
    "EH","ER","EY","IH","IY","OW","OY","UH","UW"
}
stressed_vowel = re.compile(r"^([A-Z]+)([0-2])$")

def parse_pron(phones):
    """Return (stress_pattern, rhyme_class) for a list of ARPABET tokens."""
    if not any(stressed_vowel.match(p) for p in phones):
        raise ValueError("No stressed vowel")
    # stress pattern (only vowels carry 0/1/2)
    stresses = tuple(int(m.group(2))
                     for p in phones
                     if (m := stressed_vowel.match(p)) and m.group(1) in VOWELS)

    # rhyme class = last primary-stressed vowel onward; if none, whole word
    last_primary = next(
        (i for i in range(len(phones)-1, -1, -1)
         if (m := stressed_vowel.match(phones[i])) and m.group(2) == "1"),
        0,
    )
    rhyme = tuple(phones[last_primary:])
    return stresses, rhyme

trochees = []
dactyls = []
singles = []
by_rhyme: defaultdict[tuple[tuple[str, ...], int], set[tuple[str, ...]]] = defaultdict(set)
by_pron = dict()

bad_words = set([
    "an", "he", "she", "than", "too", "that", "re", "ca",
] + list("abcdefghijklmnopqrstuvwxyz"))

sometimes_weak = set([
    "i", "a", "an", "as", "and", "my", "up", "it", "be", "been",
    "but", "he", "her", "him", "his", "just", "me", "or", "she",
    "than", "that", "this", "with", "what", "well", "then", "no",
    "not", "one", "by", "the", "them", "us", "we", "who", "you",
    "your", "as", "at", "for", "from", "of", "to", "some", "there",
    "am", "are", "can", "could", "do", "does", "had", "has", "have",
    "must", "shall", "should", "was", "where", "were", "whose",
    "will", "would", "these", "those", "all", "some", "any",
    "while", "on", "its", "so", "also", "is", "own", "which",
    "nor", "our", "their"
])

stronger_than_preceding = set([
    "free", "made", "thy",
])

wordlist: set[str] = set()
with open("4_filtered_words.txt") as f:
    for line in f:
        wordlist.add(line.strip())

with open("cmudict-0.7b", encoding="utf-8", errors="surrogateescape") as f:
    for line in f:
        if not line.strip() or line.startswith(";"):
            continue # skip comments/blank lines
        word, *pron = line.strip().split()
        pron = tuple(pron)
        word = word.lower()
        if word in bad_words:
            continue
        if word not in wordlist:
            continue
        try:
            stresses, rhyme = parse_pron(pron)
        except ValueError:
            continue
        by_pron[pron] = word
        try:
            main_stress = stresses.index(1)
        except Exception:
            continue
        if len(stresses) < 5 and len(word) < 10 and stresses not in [(0, 1), (2, 1), (0, 0, 1), (2, 0, 1), (0, 2, 1)]:
            by_rhyme[(rhyme, len(stresses))].add(tuple(pron))
        if main_stress != 0:
            continue
        if len(stresses) == 3:
            dactyls.append(word)
        if len(stresses) == 2:
            trochees.append(word)
        if len(stresses) == 1 and len(pron) < 4:
            singles.append(word)

trochees = set(trochees)
dactyls = set(dactyls)
singles = set(singles)

# syl_goal = 115_200
syl_goal = 460_800
rhymes_goal = 115_200


trochee_count = len(trochees)
dactyl_count = len(dactyls)

with open("all_bigrams.txt") as f:
    for i, line in enumerate(sorted(list(f)[4_000_000:], key=lambda x: len(x))):
        word1, word2 = line.strip().split()
        if word1 in sometimes_weak or word1 in bad_words or word2 in bad_words or word2 in stronger_than_preceding:
            continue
        if word1 in singles and word2 in singles and len(word1) + len(word2) < 10:
            if len(trochees) < syl_goal:
                trochees.add(f"{word1} {word2}")
            trochee_count += 1
        elif word1 in trochees and word2 in singles and len(word1) + len(word2) < 11:
            if len(dactyls) < syl_goal:
                dactyls.add(f"{word1} {word2}")
            dactyl_count += 1


# stressed_attack = set(list(sorted(trochees.union(dactyls), key=len))[:115200])
stressed_attack = trochees

def is_subsequence(sub_seq, main_seq):
    """
    Checks if 'sub_seq' is a subsequence of 'main_seq'.

    A subsequence is formed by deleting zero or more elements from the main sequence
    without changing the order of the remaining elements.

    Args:
        sub_seq: The potential subsequence (e.g., a string or a list).
        main_seq: The main sequence (e.g., a string or a list).

    Returns:
        True if 'sub_seq' is a subsequence of 'main_seq', False otherwise.
    """
    i = 0  # Pointer for sub_seq
    j = 0  # Pointer for main_seq

    while i < len(sub_seq) and j < len(main_seq):
        if sub_seq[i] == main_seq[j]:
            i += 1  # Move sub_seq pointer if a match is found
        j += 1      # Always move main_seq pointer

    return i == len(sub_seq)  # True if all characters of sub_seq were found in order
rhyming_pairs = []
for (rhyme, syl_count), rhyme_class in by_rhyme.items():
    words = set(by_pron[p] for p in rhyme_class if p in by_pron)
    if len(words) > 1:
        for a, b in itertools.permutations(words, 2):
            if is_subsequence(a, b) or is_subsequence(b, a):
                continue
            rhyming_pairs.append((a, b))
rhyming_pairs = list(sorted(rhyming_pairs, key=lambda a: len(a[0]) + len(a[1])))
rhyme_count = len(rhyming_pairs)
rhyming_pairs = rhyming_pairs[:rhymes_goal]

print(trochee_count, dactyl_count, rhyme_count, file=sys.stderr)

# print(len(trochees), len(dactyls), len(stressed_attack), len(rhyming_pairs), file=sys.stderr)

def sample(*sources):
    bits = 0
    result = []
    for source in sources:
        l = list(source)
        bits += math.log2(len(l))
        result.append(random.sample(l, 1)[0])
    return (result, bits)


if len(sys.argv) > 1:
    if len(sys.argv) > 2:
        if sys.argv[2] == "all":
            num = "all"
        else:
            num = int(sys.argv[2])
    else:
        num = 1
    if sys.argv[1] == "rhyme":
        if num == "all":
            print("\n".join(f"{a}/{b}" for a, b in sorted(set(rhyming_pairs))))
        else:
            print(random.sample(rhyming_pairs, num))
    elif sys.argv[1] == "single":
        if num == "all":
            print("\n".join(singles))
        else:
            print("\n".join(random.sample(list(singles), num)))
    elif sys.argv[1] == "trochee":
        if num == "all":
            print("\n".join(trochees))
        else:
            print("\n".join(random.sample(list(trochees), num)))
    elif sys.argv[1] == "dactyl":
        if num == "all":
            print("\n".join(dactyls))
        else:
            print("\n".join(random.sample(list(dactyls), num)))
    elif sys.argv[1] == "foot":
        if num == "all":
            print("\n".join(stressed_attack))
        else:
            print("\n".join(random.sample(list(stressed_attack), num)))
    elif sys.argv[1] == "poem":
        print(len(trochees), len(dactyls), len(rhyming_pairs), file=sys.stderr)
        for i in range(num if num != "all" else 1):
            (a, b, c, d, rhyme1), bits = sample(dactyls, trochees, dactyls, trochees, rhyming_pairs)
            print(bits, file=sys.stderr)
            print(a, b, rhyme1[0])
            print(c, d, rhyme1[1])
            # print(foot2, rhymes1[1])
            # print(foot4, rhymes2[1])
else:
    print("\n".join(f"{a}/{b}" for a, b in sorted(rhyming_pairs)))
