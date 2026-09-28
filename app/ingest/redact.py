"""
TREMOR — PII redaction.

Responsibilities:
- Mask credit card numbers (Luhn-valid 13-19 digit sequences)
- Mask email addresses
- Mask bearer tokens (Authorization: Bearer ...)
- Mask API keys (common patterns)
- Applied BEFORE anything is stored or sent to AWS
- Fintech-grade hygiene — a differentiator

Owner: Mokshad (Phase 1)
"""

from __future__ import annotations

# TODO: Implement in Phase 1
# Key interfaces:
#   def redact(text: str) -> str: ...
#   def _mask_cards(text: str) -> str: ...
#   def _mask_emails(text: str) -> str: ...
#   def _mask_tokens(text: str) -> str: ...
