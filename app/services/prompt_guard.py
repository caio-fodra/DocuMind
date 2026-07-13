#definição de guardrails contra prompt injection
#sanitize_sentences() descarta frasese que são instruções injetadas
#redact() redige tokens que parecem segredos (ex.: FAKE-SECRET-123) caso escapem da etapa anterior

from __future__ import annotations

import re
import unicodedata

REDACTION_PLACEHOLDER = "[redigido]"

_INJECTION_MARKERS = [
    r"ignore\w*\b.*instruc",          # "ignore todas as instruções (anteriores)"
    r"instrucoes anteriores",
    r"desconsider",                    # desconsidere / desconsiderar
    r"revel",                          # revele / revelar / revelada
    r"divulg",                         # divulgue / divulgar
    r"sempre responda",
    r"informac\w* confidenc",          # "informações confidenciais"
    r"sem restric",                    # "sem restrições"
    r"regras de visibilidade",
    r"chave secreta",
    r"senha secreta",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_MARKERS))

#token com cara de segredo/chave: maiúsculas com hífens (ex.: FAKE-SECRET-123). Só é
#redigido quando contém dígito, para reduzir falso-positivo em siglas comuns (PDF, DOCX).
_SECRET_TOKEN_RE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch)).lower()


def is_injection(text: str) -> bool:
    return _INJECTION_RE.search(_normalize(text)) is not None


def sanitize_sentences(sentences: list[str]) -> list[str]:
    return [s for s in sentences if not is_injection(s)]


def redact(text: str) -> str:

    def _replace(match: re.Match[str]) -> str:
        token = match.group(0)
        return REDACTION_PLACEHOLDER if any(ch.isdigit() for ch in token) else token

    return _SECRET_TOKEN_RE.sub(_replace, text)