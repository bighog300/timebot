import re
from typing import Any

VAR_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def render_simple_template(content: str | None, variables: dict[str, Any]) -> tuple[str, list[str]]:
    if not content:
        return '', []
    missing: list[str] = []

    def repl(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        if key not in variables or variables.get(key) is None:
            missing.append(key)
            return ''
        return str(variables.get(key))

    rendered = VAR_RE.sub(repl, content)
    return rendered, sorted(set(missing))


def render_campaign_content(template: Any, campaign: Any, override_vars: dict[str, Any] | None = None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(getattr(template, 'variables_json', None), dict):
        merged.update(template.variables_json)
    if isinstance(getattr(campaign, 'variables_json', None), dict):
        merged.update(campaign.variables_json)
    if isinstance(override_vars, dict):
        merged.update(override_vars)

    subject, m1 = render_simple_template(getattr(campaign, 'subject_override', None) or template.subject, merged)
    preheader, m2 = render_simple_template(getattr(campaign, 'preheader_override', None) or getattr(template, 'preheader', '') or '', merged)
    html_body, m3 = render_simple_template(template.html_body, merged)
    text_body, m4 = render_simple_template(getattr(template, 'text_body', '') or '', merged)
    return {'subject': subject, 'preheader': preheader or None, 'html_body': html_body, 'text_body': text_body, 'missing_variables': sorted(set(m1 + m2 + m3 + m4))}
