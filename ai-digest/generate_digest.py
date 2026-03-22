#!/usr/bin/env python3
"""Weekly AI Digest Generator for Wiktor @ Daplo"""

import anthropic
import datetime
import os
import pathlib

TODAY = datetime.date.today().isoformat()
OUTPUT_DIR = pathlib.Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"ai-digest-{TODAY}.md"

PROMPT = f"""Dzisiaj jest {TODAY}.

Przygotuj tygodniowy AI digest dla CTO firmy zajmującej się automatyzacją AI dla agencji rekrutacyjnych w Polsce.

Podsumuj najważniejsze AI toole i newsy z ostatnich 7 dni. Skup się na:
- Nowe modele LLM i ich możliwości
- Nowe narzędzia AI (szczególnie przydatne w automatyzacji procesów HR/rekrutacji)
- Ważne aktualizacje istniejących narzędzi (OpenAI, Anthropic, Google, Meta, Mistral)
- Nowe open source projekty AI z GitHub Trending

Format — TYLKO to, żaden wstęp ani podsumowanie:

# AI Digest — {TODAY}

## Narzędzia i modele

| Nazwa | Co nowego | Relevancja dla HR automation | Akcja |
|---|---|---|---|
| ... | ... | tak/nie/może | try/watch/ignore |

## Główny sygnał tygodnia

[Jeden akapit — najważniejszy trend lub zmiana tego tygodnia]

## Do sprawdzenia w przyszłym tygodniu

- ...
"""

def main():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    print(f"Generating AI digest for {TODAY}...")
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": PROMPT}],
    )
    content = message.content[0].text
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"Saved: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
