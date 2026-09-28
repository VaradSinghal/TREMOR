"""
TREMOR — Drain3 template mining wrapper.

Responsibilities:
- Wrap drain3 for log template extraction
- Track template statistics (count, first_seen, last_seen, rarity)
- Identify new/rare templates after warm-up
- Persist drain3 state alongside baseline on shutdown

Owner: Mokshad (Phase 2)
"""

from __future__ import annotations

# TODO: Implement in Phase 2
# Key interfaces:
#   class TemplateMiner:
#       def __init__(self): ...
#       def add_message(self, message: str) -> str: ...  # returns template_id
#       def get_template(self, template_id: str) -> TemplateInfo: ...
#       def get_top_templates(self, n: int) -> list[TemplateInfo]: ...
#       def is_new(self, template_id: str) -> bool: ...
#       async def persist(self, path: str) -> None: ...
#       async def restore(self, path: str) -> None: ...
