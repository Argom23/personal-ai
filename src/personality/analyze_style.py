from pathlib import Path
from collections import Counter
import json
import re
import statistics


INPUT_FILE = Path("data/processed/my_messages.jsonl")
OUTPUT_FILE = Path("data/processed/style_profile.json")


EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE
)


# Palabras comunes que no aportan mucho para detectar estilo.
STOPWORDS = {
    "que", "de", "la", "el", "y", "a", "en", "un", "una",
    "los", "las", "del", "al", "por", "para", "con", "se",
    "es", "me", "te", "le", "lo", "mi", "tu", "su", "yo",
    "si", "no"
}


def classify_message(text):
    """
    Clasifica mensajes multimedia/exportados por WhatsApp
    para que no contaminen el análisis lingüístico.
    """

    lower = text.lower().strip()

    # Stickers
    if "sticker" in lower and "omitted" in lower:
        return "sticker"

    # Audios / notas de voz
    if (
        "voice message" in lower
        or "audio omitted" in lower
        or "audio" in lower and "omitted" in lower
    ):
        return "voice"

    # Imágenes
    if (
        "image omitted" in lower
        or "photo omitted" in lower
    ):
        return "image"

    # Videos
    if "video omitted" in lower:
        return "video"

    # GIF
    if "gif omitted" in lower:
        return "gif"

    # Documentos
    if "document omitted" in lower:
        return "document"

    # Cualquier otro archivo multimedia
    if "media omitted" in lower:
        return "media"

    # Algunas versiones de WhatsApp generan frases como:
    # "This message was omitted..."
    if "omitted" in lower:
        return "media"

    return "text"


def load_messages():
    text_messages = []
    communication_types = Counter()

    with open(INPUT_FILE, "r", encoding="utf-8") as file:

        for line in file:
            data = json.loads(line)

            text = data["message"].strip()

            if not text:
                continue

            message_type = classify_message(text)

            communication_types[message_type] += 1

            # Solo analizamos lingüísticamente los mensajes de texto
            if message_type == "text":
                text_messages.append(text)

    return text_messages, communication_types


def tokenize(text):
    return re.findall(
        r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b",
        text.lower(),
        flags=re.UNICODE
    )


def get_emojis(text):
    found = EMOJI_PATTERN.findall(text)

    emojis = []

    for group in found:
        emojis.extend(list(group))

    return emojis


def analyze(messages, communication_types):
    total_text_messages = len(messages)
    total_all_messages = sum(communication_types.values())

    word_counts = []
    char_counts = []

    all_words = []
    meaningful_words = []
    all_emojis = []

    questions = 0
    exclamations = 0
    uppercase_messages = 0

    jaja_messages = 0
    xd_messages = 0

    one_word_messages = 0
    short_messages = 0
    long_messages = 0

    punctuation = Counter()

    for message in messages:

        words = tokenize(message)

        word_counts.append(len(words))
        char_counts.append(len(message))

        all_words.extend(words)

        meaningful_words.extend(
            word
            for word in words
            if word not in STOPWORDS
            and len(word) > 1
        )

        all_emojis.extend(get_emojis(message))

        lower = message.lower()

        if "?" in message:
            questions += 1

        if "!" in message:
            exclamations += 1

        letters = [
            c for c in message
            if c.isalpha()
        ]

        if letters:
            uppercase_ratio = (
                sum(
                    1
                    for c in letters
                    if c.isupper()
                )
                / len(letters)
            )

            if uppercase_ratio > 0.7:
                uppercase_messages += 1

        # Detecta:
        # jaja
        # jajaja
        # JAJAJA
        # jajajajaja
        if re.search(r"(ja){2,}", lower):
            jaja_messages += 1

        if "xd" in lower:
            xd_messages += 1

        if len(words) == 1:
            one_word_messages += 1

        if len(words) <= 5:
            short_messages += 1

        if len(words) >= 20:
            long_messages += 1

        for char in message:
            if char in ".,;:!?":
                punctuation[char] += 1

    word_frequency = Counter(all_words)
    meaningful_frequency = Counter(meaningful_words)
    emoji_frequency = Counter(all_emojis)

    communication_habits = {}

    for message_type, count in communication_types.items():

        communication_habits[message_type] = {
            "count": count,
            "rate": round(
                count / total_all_messages,
                4
            ) if total_all_messages else 0
        }

    profile = {
        "dataset": {
            "total_messages": total_all_messages,
            "text_messages": total_text_messages,
            "non_text_messages": (
                total_all_messages
                - total_text_messages
            )
        },

        "linguistic_style": {
            "average_words_per_message": round(
                statistics.mean(word_counts),
                2
            ) if word_counts else 0,

            "median_words_per_message": round(
                statistics.median(word_counts),
                2
            ) if word_counts else 0,

            "average_characters_per_message": round(
                statistics.mean(char_counts),
                2
            ) if char_counts else 0,

            "question_rate": round(
                questions / total_text_messages,
                4
            ) if total_text_messages else 0,

            "exclamation_rate": round(
                exclamations / total_text_messages,
                4
            ) if total_text_messages else 0,

            "uppercase_message_rate": round(
                uppercase_messages / total_text_messages,
                4
            ) if total_text_messages else 0,

            "jaja_rate": round(
                jaja_messages / total_text_messages,
                4
            ) if total_text_messages else 0,

            "xd_rate": round(
                xd_messages / total_text_messages,
                4
            ) if total_text_messages else 0,

            "one_word_message_rate": round(
                one_word_messages / total_text_messages,
                4
            ) if total_text_messages else 0,

            "short_message_rate": round(
                short_messages / total_text_messages,
                4
            ) if total_text_messages else 0,

            "long_message_rate": round(
                long_messages / total_text_messages,
                4
            ) if total_text_messages else 0,

            "top_words": word_frequency.most_common(50),

            "top_meaningful_words":
                meaningful_frequency.most_common(50),

            "top_emojis":
                emoji_frequency.most_common(30),

            "punctuation": dict(punctuation)
        },

        "communication_habits":
            communication_habits
    }

    return profile


def print_summary(profile):

    dataset = profile["dataset"]
    style = profile["linguistic_style"]
    habits = profile["communication_habits"]

    print("\n=== DATASET ===\n")

    print(
        f"Mensajes totales: "
        f"{dataset['total_messages']}"
    )

    print(
        f"Mensajes de texto: "
        f"{dataset['text_messages']}"
    )

    print(
        f"Mensajes multimedia/sistema: "
        f"{dataset['non_text_messages']}"
    )

    print("\n=== PERFIL LINGÜÍSTICO ===\n")

    print(
        f"Promedio palabras/mensaje: "
        f"{style['average_words_per_message']}"
    )

    print(
        f"Mediana palabras/mensaje: "
        f"{style['median_words_per_message']}"
    )

    print(
        f"Promedio caracteres/mensaje: "
        f"{style['average_characters_per_message']}"
    )

    print(
        f"Preguntas: "
        f"{style['question_rate'] * 100:.2f}%"
    )

    print(
        f"JAJA: "
        f"{style['jaja_rate'] * 100:.2f}%"
    )

    print(
        f"XD: "
        f"{style['xd_rate'] * 100:.2f}%"
    )

    print(
        f"Mensajes de una palabra: "
        f"{style['one_word_message_rate'] * 100:.2f}%"
    )

    print(
        f"Mensajes cortos (<=5 palabras): "
        f"{style['short_message_rate'] * 100:.2f}%"
    )

    print(
        f"Mensajes largos (>=20 palabras): "
        f"{style['long_message_rate'] * 100:.2f}%"
    )

    print("\n=== PALABRAS CARACTERÍSTICAS ===\n")

    for word, count in style[
        "top_meaningful_words"
    ][:20]:
        print(f"{word}: {count}")

    print("\n=== EMOJIS ===\n")

    for emoji, count in style[
        "top_emojis"
    ][:15]:
        print(f"{emoji}: {count}")

    print("\n=== HÁBITOS DE COMUNICACIÓN ===\n")

    for message_type, data in habits.items():

        print(
            f"{message_type}: "
            f"{data['count']} "
            f"({data['rate'] * 100:.2f}%)"
        )


def main():

    messages, communication_types = load_messages()

    print(
        f"Analizando "
        f"{len(messages)} mensajes de texto..."
    )

    profile = analyze(
        messages,
        communication_types
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

        json.dump(
            profile,
            file,
            ensure_ascii=False,
            indent=4
        )

    print_summary(profile)

    print(
        f"\nPerfil guardado en: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()