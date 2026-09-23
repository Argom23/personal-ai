from pathlib import Path
import re
import json
import unicodedata


RAW_DIR = Path("data/raw")
OUTPUT_FILE = Path("data/processed/messages.jsonl")


# Android / formato clásico:
# 12/18/19, 7:29 PM - Cesar: hola
PATTERN_NORMAL = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s*"
    r"(.+?)\s*-\s*"
    r"([^:]+):\s*"
    r"(.*)$"
)


# iPhone / formato con corchetes:
#
# [7/1/26, 9:44:51 PM] - Cesar: hola
#
# o
#
# [7/1/26, 9:44:51 PM] Cesar: hola
PATTERN_BRACKET = re.compile(
    r"^\[\s*"
    r"(\d{1,2}/\d{1,2}/\d{2,4}),\s*"
    r"(.+?)"
    r"\]\s*"
    r"(?:-\s*)?"
    r"([^:]+):\s*"
    r"(.*)$"
)


def normalize_line(line):
    line = unicodedata.normalize("NFKC", line)

    invisible_chars = [
        "\u200e",
        "\u200f",
        "\u202a",
        "\u202b",
        "\u202c",
        "\u202d",
        "\u202e",
        "\ufeff",
    ]

    for char in invisible_chars:
        line = line.replace(char, "")

    line = line.replace("\u00a0", " ")
    line = line.replace("\u202f", " ")

    return line.strip()


def parse_message(line):
    line = normalize_line(line)

    match = PATTERN_NORMAL.match(line)

    if match:
        return match.groups()

    match = PATTERN_BRACKET.match(line)

    if match:
        return match.groups()

    return None


def parse_file(path):
    messages = []
    current = None
    ignored_system_lines = 0

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        errors="replace"
    ) as file:

        for raw_line in file:
            line = raw_line.rstrip("\r\n")

            parsed = parse_message(line)

            if parsed:
                date, time, author, message = parsed

                current = {
                    "source": path.name,
                    "date": date.strip(),
                    "time": time.strip(),
                    "author": author.strip(),
                    "message": message.strip(),
                }

                messages.append(current)

            else:
                normalized = normalize_line(line)

                # Si empieza con fecha pero no tiene autor:mensaje,
                # probablemente es un evento del sistema:
                # llamadas, cifrado, cambios de grupo, etc.
                if (
                    normalized.startswith("[")
                    and "]" in normalized
                    and ":" not in normalized.split("]", 1)[1]
                ):
                    ignored_system_lines += 1
                    current = None
                    continue

                # Mensaje de varias líneas
                if current is not None and normalized:
                    current["message"] += "\n" + normalized

    return messages, ignored_system_lines


def main():
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    all_messages = []

    for txt_file in RAW_DIR.glob("*.txt"):
        print(f"Procesando: {txt_file.name}")

        messages, ignored = parse_file(txt_file)

        print(
            f"  -> {len(messages)} mensajes encontrados"
        )

        if ignored:
            print(
                f"  -> {ignored} eventos del sistema ignorados"
            )

        all_messages.extend(messages)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        for message in all_messages:
            file.write(
                json.dumps(
                    message,
                    ensure_ascii=False
                )
                + "\n"
            )

    print()
    print(f"Mensajes totales: {len(all_messages)}")
    print(f"Guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()