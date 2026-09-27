from pathlib import Path
import json


INPUT_FILE = Path("data/processed/style_profile.json")
OUTPUT_FILE = Path("data/processed/style_prompt.txt")


def percentage(value):
    return round(value * 100, 1)


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        profile = json.load(file)

    style = profile["linguistic_style"]
    habits = profile["communication_habits"]

    lines = []

    lines.append("ESTILO DE ESCRITURA DEL USUARIO")
    lines.append("")

    avg_words = style["average_words_per_message"]
    short_rate = percentage(style["short_message_rate"])
    one_word_rate = percentage(style["one_word_message_rate"])
    long_rate = percentage(style["long_message_rate"])

    lines.append(
        f"- Escribe mensajes cortos: promedio de {avg_words} palabras."
    )

    lines.append(
        f"- Aproximadamente {short_rate}% de sus mensajes "
        f"tienen 5 palabras o menos."
    )

    lines.append(
        f"- Aproximadamente {one_word_rate}% son mensajes "
        f"de una sola palabra."
    )

    if long_rate < 5:
        lines.append(
            "- Los mensajes largos son poco frecuentes."
        )

    question_rate = percentage(style["question_rate"])

    lines.append(
        f"- Usa preguntas en aproximadamente {question_rate}% "
        f"de sus mensajes."
    )

    exclamation_rate = percentage(
        style["exclamation_rate"]
    )

    if exclamation_rate < 1:
        lines.append(
            "- Casi nunca utiliza signos de exclamación."
        )

    jaja_rate = percentage(style["jaja_rate"])

    if jaja_rate > 1:
        lines.append(
            f"- Usa expresiones tipo JAJA en aproximadamente "
            f"{jaja_rate}% de sus mensajes."
        )

    xd_rate = percentage(style["xd_rate"])

    if xd_rate > 0:
        lines.append(
            f"- Utiliza XD ocasionalmente "
            f"({xd_rate}% de los mensajes)."
        )

    uppercase_rate = percentage(
        style["uppercase_message_rate"]
    )

    if uppercase_rate > 1:
        lines.append(
            "- A veces utiliza mayúsculas para enfatizar."
        )

    lines.append("")
    lines.append("VOCABULARIO CARACTERÍSTICO")
    lines.append("")

    top_words = style["top_meaningful_words"][:15]

    characteristic_words = [
        word
        for word, count in top_words
    ]

    lines.append(
        "- Palabras y expresiones frecuentes: "
        + ", ".join(characteristic_words)
        + "."
    )

    emojis = style["top_emojis"][:10]

    if emojis:
        emoji_list = [
            emoji
            for emoji, count in emojis
        ]

        lines.append(
            "- Emojis frecuentes: "
            + " ".join(emoji_list)
        )

    lines.append("")
    lines.append("HÁBITOS DE COMUNICACIÓN")
    lines.append("")

    for message_type, data in habits.items():

        if message_type == "text":
            continue

        rate = percentage(data["rate"])

        if rate >= 0.5:
            lines.append(
                f"- Usa {message_type} en aproximadamente "
                f"{rate}% de sus mensajes."
            )

    lines.append("")
    lines.append("INSTRUCCIONES DE IMITACIÓN")
    lines.append("")

    lines.append(
        "- Mantener un tono informal y natural."
    )

    lines.append(
        "- No escribir mensajes excesivamente largos "
        "a menos que el contexto académico lo requiera."
    )

    lines.append(
        "- Mantener las expresiones características "
        "sin forzarlas en cada respuesta."
    )

    lines.append(
        "- No exagerar emojis, JAJA ni muletillas."
    )

    lines.append(
        "- En preguntas de física o matemática, priorizar "
        "la claridad y exactitud aunque el estilo sea informal."
    )

    prompt = "\n".join(lines)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(prompt)

    print(prompt)

    print(
        f"\nPerfil textual guardado en: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()