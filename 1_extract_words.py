import csv

with open("words_219k_m1970.tsv", errors="ignore") as f:
    reader = csv.reader(f, delimiter="\t")
    headers = next(reader)
    for row in reader:
        word = row[headers.index("word")]
        print(word)
