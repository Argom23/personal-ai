from pathlib import Path
import json


INPUT_FILE = Path("data/processed/messages.jsonl")
OUTPUT_FILE = Path("data/processed/my_messages.jsonl")

# Cambiá esto exactamente por tu nombre tal como aparece en inspect_authors.py
MY_NAMES = {
    "Cesar Arce",
    "You",
}


def main():
    total = 0
    mine = 0

    with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

        for line in infile:
            message = json.loads(line)
            total += 1

            if message["author"] in MY_NAMES:
                outfile.write(
                    json.dumps(
                        message,
                        ensure_ascii=False
                    ) + "\n"
                )
                mine += 1

    print(f"Mensajes totales: {total}")
    print(f"Mensajes tuyos: {mine}")
    print(f"Guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()