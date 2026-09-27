from pathlib import Path
import json


INPUT_FILE = Path("data/processed/messages.jsonl")
OUTPUT_FILE = Path("data/processed/style_examples.jsonl")


MY_NAMES = {
    "Cesar Arce",
    "You",   
}


NOISE = [
    "omitted",
    "sticker",
    "media",
    "voice message",
    "image omitted",
    "video omitted",
    "audio omitted",
    "gif omitted",
    "document omitted",
]


def is_noise(text):
    text = text.lower()

    return any(
        noise in text
        for noise in NOISE
    )


def main():
    messages = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        for line in file:
            messages.append(
                json.loads(line)
            )

    examples = []

    for i in range(1, len(messages)):
        current = messages[i]
        previous = messages[i - 1]

        # No mezclar dos chats diferentes
        if current["source"] != previous["source"]:
            continue

        # Buscamos:
        #
        # Otra persona: mensaje
        # Yo: respuesta
        #
        if (
            previous["author"] not in MY_NAMES
            and current["author"] in MY_NAMES
        ):
            context = previous["message"].strip()
            response = current["message"].strip()

            if not context or not response:
                continue

            # Ignorar stickers, audios, imágenes, etc.
            if is_noise(context):
                continue

            if is_noise(response):
                continue

            # Evitar ejemplos exageradamente grandes
            if len(context) > 500:
                continue

            if len(response) > 300:
                continue

            examples.append(
                {
                    "source": current["source"],
                    "context": context,
                    "response": response,
                }
            )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        for example in examples:
            file.write(
                json.dumps(
                    example,
                    ensure_ascii=False
                )
                + "\n"
            )

    print()
    print("=== DATASET DE EJEMPLOS ===")
    print()
    print(
        f"Mensajes originales: {len(messages)}"
    )
    print(
        f"Ejemplos creados: {len(examples)}"
    )
    print(
        f"Guardado en: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()