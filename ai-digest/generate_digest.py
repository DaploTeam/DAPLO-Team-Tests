#!/usr/bin/env python3
"""Weekly AI Digest Generator for Wiktor @ Daplo — saves to Notion"""

import openai
import datetime
import os
import notion_client

TODAY = datetime.date.today().isoformat()
AI_RESEARCH_PAGE_ID = "32b541d0-a83f-8037-84d2-c8d0bf7e4d07"

PROMPT = f"""Dzisiaj jest {TODAY}.

Przygotuj tygodniowy AI digest dla Wiktora — CTO małej (3-osobowej) firmy Daplo, która buduje automatyzacje AI dla agencji rekrutacyjnych w Polsce.

Profil firmy:
- Mały zespół, ograniczony budżet — szukamy narzędzi dostępnych przez API lub SaaS z rozsądną ceną
- Kluczowe obszary: parsowanie CV, komunikacja z kandydatami, generowanie opisów stanowisk, integracje z ATS, automatyzacja mailingu rekrutacyjnego
- Stack techniczny: Python, API, n8n/Make do workflow
- Rynek: Polska, ale narzędzia mogą być globalne

Przeszukaj internet i znajdź PRAWDZIWE newsy z ostatnich 7 dni. Skup się na:
- Nowe modele LLM i ich możliwości (szczególnie tańsze, szybkie modele API)
- Nowe narzędzia AI przydatne w rekrutacji i HR automation
- Ważne aktualizacje OpenAI, Anthropic, Google, Meta, Mistral
- Ciekawe open source projekty z GitHub (automatyzacja rekrutacji, NLP do CV, chatboty HR)

Oceniaj relevancję przez pryzmat: czy Daplo może to wdrożyć klientowi agencji rekrutacyjnej w ciągu tygodnia lub miesiąca?

Format odpowiedzi — TYLKO poniższe sekcje, zero wstępów:

# AI Digest — {TODAY}

## Narzędzia i modele

TABELA:
Nazwa | Co nowego | Relevancja dla Daplo | Akcja
(max 6-8 pozycji, tylko prawdziwe rzeczy z tego tygodnia)

## Główny sygnał tygodnia

[Jeden konkretny akapit — co zmienia perspektywę lub wymaga reakcji]

## Do sprawdzenia w przyszłym tygodniu

- [konkretne rzeczy, nie ogólniki]
"""

def parse_table(lines):
    """Parse markdown table lines into list of row lists."""
    rows = []
    for line in lines:
        if line.startswith("|---") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells:
            rows.append(cells)
    return rows

def build_notion_table(rows):
    """Build a Notion table block from rows."""
    if not rows:
        return None
    table_width = max(len(r) for r in rows)
    notion_rows = []
    for row in rows:
        cells = []
        for i in range(table_width):
            text = row[i] if i < len(row) else ""
            cells.append([{"type": "text", "text": {"content": text}}])
        notion_rows.append({
            "object": "block",
            "type": "table_row",
            "table_row": {"cells": cells}
        })
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": table_width,
            "has_column_header": True,
            "has_row_header": False,
            "children": notion_rows
        }
    }

def markdown_to_notion_blocks(text):
    blocks = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Heading 1
        if line.startswith("# "):
            blocks.append({"object": "block", "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})

        # Heading 2
        elif line.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}})

        # Table — collect all consecutive pipe lines
        elif line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = parse_table(table_lines)
            table_block = build_notion_table(rows)
            if table_block:
                blocks.append(table_block)
            continue

        # Bullet
        elif line.startswith("- "):
            blocks.append({"object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})

        # Paragraph
        elif line.strip():
            blocks.append({"object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}})

        i += 1
    return blocks

def main():
    # Generate digest with OpenAI (web search enabled)
    oai = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    print(f"Generating AI digest for {TODAY}...")

    response = oai.responses.create(
        model="gpt-4o",
        tools=[{"type": "web_search_preview"}],
        input=PROMPT,
    )
    content = response.output_text
    print("Generated. Saving to Notion...")

    # Save to Notion
    notion = notion_client.Client(auth=os.environ["NOTION_API_KEY"])
    blocks = markdown_to_notion_blocks(content)

    notion.pages.create(
        parent={"page_id": AI_RESEARCH_PAGE_ID},
        properties={"title": {"title": [{"type": "text", "text": {"content": TODAY}}]}},
        children=blocks[:100],
    )
    print(f"Done. Page '{TODAY}' created in AI Research.")

if __name__ == "__main__":
    main()
