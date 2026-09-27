"""Azure DevOps work item lookup (stdlib-only, no extra dependency)."""

from __future__ import annotations

import base64
import html
import json
import re
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_VERSION = "7.1"

_TAG_RE = re.compile(r"<[^>]+>")
_LI_RE = re.compile(r"<li[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL)
_BLOCK_BREAK_RE = re.compile(r"</(?:p|div)\s*>|<br\s*/?>", re.IGNORECASE)


def html_to_text(raw: str | None) -> str:
    """Best-effort ADO rich-text field -> plain text, preserving <li> as
    markdown-style bullets so decompose() can pick them up."""
    if not raw:
        return ""
    text = _LI_RE.sub(lambda m: f"\n- {m.group(1)}\n", raw)
    text = _BLOCK_BREAK_RE.sub("\n", text)
    text = _TAG_RE.sub("", text)
    text = html.unescape(text)

    out: list[str] = []
    blank = False
    for line in (ln.rstrip() for ln in text.splitlines()):
        if line.strip():
            out.append(line)
            blank = False
        elif not blank:
            out.append("")
            blank = True
    return "\n".join(out).strip()


@dataclass(frozen=True)
class AdoTicket:
    id: int
    title: str
    text: str  # combined title + description + acceptance criteria, plain text


def fetch_ticket(org_project: str, ticket_id: int, *, pat: str) -> AdoTicket:
    org, _, project = org_project.partition("/")
    if not org or not project:
        raise ValueError(f"expected an 'org/project' constant, got {org_project!r}")

    url = (
        f"https://dev.azure.com/{org}/{project}/_apis/wit/workitems/{ticket_id}"
        f"?$expand=all&api-version={API_VERSION}"
    )
    token = base64.b64encode(f":{pat}".encode()).decode()
    request = Request(url, headers={"Authorization": f"Basic {token}", "Accept": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read())
    except HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"ADO request failed ({e.code}) for work item {ticket_id}: {body}") from e

    fields = payload["fields"]
    title = fields.get("System.Title", "")
    description = html_to_text(fields.get("System.Description"))
    acceptance = html_to_text(fields.get("Microsoft.VSTS.Common.AcceptanceCriteria"))

    text = "\n\n".join(p for p in (title, description, acceptance) if p)
    return AdoTicket(id=ticket_id, title=title, text=text)
