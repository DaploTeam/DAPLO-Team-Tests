#!/usr/bin/env python3
"""Weekly AI Digest Generator for Wiktor @ Daplo — saves to Notion"""

import openai
import datetime
import os
import notion_client

TODAY = datetime.date.today().isoformat()
AI_RESEARCH_PAGE_ID = "32b541d0-a83f-8037-84d2-c8d0bf7e4d07"

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

def markdown_to_notion_blocks(text):
    """Convert plain markdown text to Notion paragraph blocks."""
    blocks = []
    for line in text.split("\n"):
        if line.startswith("# "):
            blocks.append({"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})
        elif line.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}})
        elif line.startswith("- "):
            blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})
        elif line.startswith("|"):
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}})
        elif line.strip():
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}})
    return blocks

def main():
    # Generate digest with OpenAI
    oai = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    print(f"Generating AI digest for {TODAY}...")
    response = oai.chat.completions.create(
        model="gpt-4o",
        max_tokens=2048,
        messages=[{"role": "user", "content": PROMPT}],
    )
    content = response.choices[0].message.content
    print("Generated. Saving to Notion...")

    # Save to Notion
    notion = notion_client.Client(auth=os.environ["NOTION_API_KEY"])
    blocks = markdown_to_notion_blocks(content)

    notion.pages.create(
        parent={"page_id": AI_RESEARCH_PAGE_ID},
        properties={"title": {"title": [{"type": "text", "text": {"content": TODAY}}]}},
        children=blocks[:100],  # Notion API limit: 100 blocks per request
    )
    print(f"Done. Page '{TODAY}' created in AI Research.")

if __name__ == "__main__":
    main()
