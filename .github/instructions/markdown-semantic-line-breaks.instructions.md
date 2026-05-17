---
applyTo: "**/*.md"
---

# Markdown Semantic Line Breaks

When creating or editing Markdown, use Semantic Line Breaks (SemBr).
Preserve rendered output and meaning while improving editability.

## Core Rules

- Break lines at sentence boundaries.
- Prefer additional breaks at clause boundaries marked by `,`, `;`, or `:`.
- Optionally break around links when it improves readability.
- Never break inside a word.
- Do not change heading, list, table, HTML, or code-block structure.
- Keep existing blank-line paragraph separation unless the task asks otherwise.

## Safety Constraints

- Do not rewrite text that appears inside fenced code blocks.
- Do not rewrite inline code spans.
- Do not alter YAML frontmatter keys or values.
- If a file has strict formatting requirements, prioritize those requirements.

## Output Style

- Keep text natural and readable.
- Avoid unnecessary rewording; line-level restructuring is preferred.
- Apply SemBr consistently across the entire Markdown file you modify.
