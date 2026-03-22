#!/usr/bin/env python3
"""Weekly AI Digest Generator for Wiktor @ Daplo — saves to Notion"""

import openai
import datetime
import os
import notion_client

TODAY = datetime.date.today().isoformat()
WEEK_AGO = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
AI_RESEARCH_PAGE_ID = "32b541d0-a83f-8037-84d2-c8d0bf7e4d07"

PROMPT = f"""Dzisiaj jest {TODAY}.

Przygotuj tygodniowy AI digest dla Wiktora — CTO małej (3-osobowej) firmy Daplo, która buduje automatyzacje AI dla agencji rekrutacyjnych w Polsce.

Profil firmy Daplo:
- Budujemy automatyzacje AI dla agencji rekrutacyjnych (parsowanie CV, komunikacja z kandydatami, opisy stanowisk, integracje z ATS, automatyzacja mailingu)
- Stack: Python, API, n8n/Make
- Mały zespół, ograniczony budżet — szukamy rzeczy dostępnych przez API lub SaaS z rozsądną ceną

Przeszukaj WYŁĄCZNIE poniższe źródła i znajdź narzędzia/modele wydane lub zaktualizowane między {WEEK_AGO} a {TODAY}:

ŹRÓDŁA (przeszukaj każde z osobna):
1. news.ycombinator.com — najszybsze informacje ze społeczności tech
2. huggingface.co/blog — nowe modele i biblioteki open source
3. openai.com/blog — oficjalne ogłoszenia OpenAI
4. anthropic.com/news — oficjalne ogłoszenia Anthropic
5. github.com/trending — najgorętsze repozytoria tygodnia (filtr: AI/ML)
6. techcrunch.com/category/artificial-intelligence — newsy ze świata AI
7. venturebeat.com/ai — AI focused tech news
8. the-decoder.com — szybkie newsy AI
9. mistral.ai/news — oficjalne ogłoszenia Mistral
10. ai.google.blog — ogłoszenia Google AI / DeepMind

ZASADY BEZWZGLĘDNE:
- Każde narzędzie MUSI mieć potwierdzoną datę premiery/aktualizacji z ostatnich 7 dni — jeśli nie możesz jej znaleźć w powyższych źródłach, pomiń
- Każde narzędzie MUSI mieć link do strony produktu, GitHub lub oficjalnej dokumentacji (nie do artykułu newsowego, nie do eventu)
- NIE DODAWAJ konferencji, wydarzeń, webinarów, szkoleń — tylko produkty i modele
- NIE WYMYŚLAJ — jeśli tydzień był spokojny, napisz mniej pozycji

Utwórz DWA ODDZIELNE zestawy danych w formacie tabelarycznym:

TABELA 1 — "Toolsy dla klientów Daplo" (narzędzia które możemy wdrożyć agencjom rekrutacyjnym):
Kolumny: Nazwa | Data premiery | Co nowego | Dlaczego wdrożyć u klienta | Link | Akcja

TABELA 2 — "Toolsy dla Daplo" (narzędzia które usprawnią naszą własną pracę jako firmy):
Kolumny: Nazwa | Data premiery | Co nowego | Jak usprawni pracę Daplo | Link | Akcja

Po tabelach:

## Główny sygnał tygodnia
[Jeden konkretny akapit — co zmienia perspektywę lub wymaga reakcji]

## Do sprawdzenia w przyszłym tygodniu
- [konkretne rzeczy]
"""

def parse_table(lines):
    rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if set(stripped.replace("|", "").replace("-", "").replace(" ", "")) == set():
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if any(cells):
            rows.append(cells)
    return rows

def build_notion_table(rows):
    if not rows:
        return None
    table_width = max(len(r) for r in rows)
    notion_rows = []
    for row in rows:
        cells = []
        for i in range(table_width):
            text = row[i] if i < len(row) else ""
            text = text.replace("**", "")
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

        if line.startswith("# "):
            blocks.append({"object": "block", "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:].replace("**", "")}}]}})

        elif line.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:].replace("**", "")}}]}})

        elif line.startswith("### "):
            blocks.append({"object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:].replace("**", "")}}]}})

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

        elif line.startswith("- "):
            blocks.append({"object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:].replace("**", "")}}]}})

        elif line.strip():
            blocks.append({"object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line.replace("**", "")}}]}})

        i += 1
    return blocks

def main():
    oai = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    print(f"Generating AI digest for {TODAY}...")

    response = oai.responses.create(
        model="gpt-5.4-mini",
        tools=[{"type": "web_search_preview"}],
        input=PROMPT,
    )
    content = response.output_text
    print("Generated. Saving to Notion...")

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
