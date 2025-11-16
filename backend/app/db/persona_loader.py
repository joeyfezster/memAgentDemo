from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PersonaDefinition:
    email: str
    display_name: str
    persona_handle: str
    professional_role: str
    industry: str
    description: str
    typical_kpis: list[str]
    typical_motivations: list[str]
    quintessential_queries: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _persona_dir() -> Path:
    return _repo_root() / "docs" / "product" / "personas"


def _normalize_header(header: str) -> str:
    return header.strip().lower().replace("’", "'")


def _collect_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in lines:
        line = raw_line.rstrip()
        if line.startswith("## "):
            current = _normalize_header(line[3:])
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def _parse_heading(line: str) -> tuple[str, str, str]:
    content = line.split(":", 1)[1].strip()
    if "–" in content:
        name_part, rest = content.split("–", 1)
        name = name_part.strip()
        if "," in rest:
            role_part, industry_part = rest.rsplit(",", 1)
            return name, role_part.strip(), industry_part.strip()
        return name, rest.strip(), ""
    return content, "", ""


def _parse_background(lines: list[str]) -> str:
    entries = [line[2:].strip() for line in lines if line.strip().startswith("-")]
    return " ".join(entries)


def _parse_bullets(lines: list[str]) -> list[str]:
    values: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("-"):
            values.append(stripped[1:].strip())
    return values


def _parse_demo_handles(lines: list[str]) -> tuple[str | None, str | None]:
    values = [line[2:].strip() for line in lines if line.strip().startswith("-")]
    email = values[0] if values else None
    handle = values[1] if len(values) > 1 else None
    return email, handle


def _parse_sample_queries(lines: list[str]) -> list[str]:
    queries: list[str] = []
    current_title: str | None = None
    current_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_lines:
                queries.append(_compose_query(current_title, current_lines))
                current_title = None
                current_lines = []
            continue
        if stripped[0].isdigit() and "." in stripped:
            if current_lines:
                queries.append(_compose_query(current_title, current_lines))
                current_lines = []
            current_title = stripped.split(".", 1)[1].strip()
            continue
        if stripped.startswith(">"):
            current_lines.append(stripped[1:].strip())
        elif stripped.lower().startswith("expected output"):
            continue
        else:
            current_lines.append(stripped)
    if current_lines:
        queries.append(_compose_query(current_title, current_lines))
    return [query for query in queries if query]


def _compose_query(title: str | None, parts: list[str]) -> str:
    prompt = " ".join(parts).strip()
    if not prompt:
        return ""
    if title:
        return f"{title}: {prompt}"
    return prompt


def load_persona_definitions() -> list[PersonaDefinition]:
    records: list[PersonaDefinition] = []
    personas_dir = _persona_dir()
    if not personas_dir.exists():
        return records
    for file_path in personas_dir.glob("*.md"):
        definition = _parse_persona_file(file_path)
        if definition:
            records.append(definition)
    return records


def _parse_persona_file(file_path: Path) -> PersonaDefinition | None:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    heading_line = next((line for line in lines if line.startswith("# Persona:")), None)
    if not heading_line:
        return None
    name, role, industry = _parse_heading(heading_line)
    sections = _collect_sections(lines)
    demo_lines = sections.get(_normalize_header("Demo Handle"), [])
    email, handle = _parse_demo_handles(demo_lines)
    if not (email and handle):
        return None
    background = _parse_background(sections.get(_normalize_header("Background"), []))
    kpi_section = sections.get(_normalize_header("How He's Measured")) or sections.get(
        _normalize_header("How She's Measured")
    )
    motivations = _parse_bullets(sections.get(_normalize_header("Core Motivations"), []))
    queries = _parse_sample_queries(sections.get(_normalize_header("Sample Queries"), []))
    description = background or role
    typical_kpis = _parse_bullets(kpi_section or [])
    if not role:
        role = ""
    if not industry:
        industry = ""
    return PersonaDefinition(
        email=email,
        display_name=name,
        persona_handle=handle,
        professional_role=role,
        industry=industry,
        description=description,
        typical_kpis=typical_kpis,
        typical_motivations=motivations,
        quintessential_queries=queries,
    )
