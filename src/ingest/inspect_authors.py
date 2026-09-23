from pathlib import Path
from collections import Counter, defaultdict
import json

FILE = Path("data/processed/messages.jsonl")

authors = Counter()
sources = Counter()
authors_by_source = defaultdict(Counter)

with open(FILE, "r", encoding="utf-8") as file:
    for line in file:
        message = json.loads(line)

        author = message["author"]
        source = message["source"]

        authors[author] += 1
        sources[source] += 1
        authors_by_source[source][author] += 1


print("\n=== MENSAJES POR ARCHIVO ===\n")

for source, count in sources.items():
    print(f"{source}: {count} mensajes")

print("\n=== AUTORES POR ARCHIVO ===\n")

for source, source_authors in authors_by_source.items():
    print(source)

    for author, count in source_authors.most_common():
        print(f"  {author}: {count}")

    print()

print("=== TOTAL DE AUTORES ===\n")

for author, count in authors.most_common():
    print(f"{author}: {count} mensajes")