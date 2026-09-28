"""
TREMOR — Drain3 template mining wrapper.

Responsibilities:
- Wrap drain3 for log template extraction (ids, numbers, UUIDs, IPs masked)
- Track template statistics (count, first_seen, last_seen, rarity, sample)
- Identify new/rare templates after warm-up
- Per-service, per-second counts so detectors can ask "how often did template X
  appear in the last N seconds"
- Persist drain3 state alongside baseline on shutdown

Owner: Mokshad (Phase 2)
"""

from __future__ import annotations

import asyncio
import json
import os
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from drain3 import TemplateMiner as _Drain3Miner
from drain3.masking import MaskingInstruction
from drain3.template_miner_config import TemplateMinerConfig

if TYPE_CHECKING:
    from app.clock import Clock

STATE_VERSION = 1
GLOBAL_SERVICE = "_global"

# Order matters: the most specific patterns run first so that e.g. the digits
# inside a UUID or an IP are not masked as <NUM> before the whole token is.
_MASKS: tuple[tuple[str, str], ...] = (
    (r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", "UUID"),
    (r"\b0x[0-9a-fA-F]+\b", "HEX"),
    (r"\b(?=[0-9a-fA-F]*\d)[0-9a-fA-F]{12,}\b", "HEX"),
    (r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b", "IP"),
    (r"\b(?:txn|req|acct|ord|usr|sess|kid|pay|ch|re)_[A-Za-z0-9]+\b", "ID"),
    (r"((?<=[^A-Za-z0-9_])|^)[-+]?\d+(?:\.\d+)?(?:ms|s)?((?=[^A-Za-z0-9_])|$)", "NUM"),
)


@dataclass(frozen=True, slots=True)
class TemplateInfo:
    """Snapshot of one mined template.

    ``count`` is cumulative unless the query that produced this snapshot was
    filtered by service/window, in which case it is the count within that filter.
    ``rarity`` is always global: cumulative count / all messages seen.
    """

    id: int
    template: str
    count: int
    first_seen: float
    last_seen: float
    sample: str
    rarity: float


@dataclass(slots=True)
class _Stats:
    count: int
    first_seen: float
    last_seen: float
    sample: str
    novel_at: float | None = None


@dataclass(slots=True)
class _Bucket:
    second: int
    counts: Counter[int]


class _MemoryPersistence:
    """Duck-typed drain3 persistence handler holding state in memory.

    Only attached to the drain3 miner for the duration of a save/load, so drain3
    never snapshots (or reads the wall clock for snapshot timing) on the hot path.
    """

    def __init__(self, state: bytes | None = None) -> None:
        self.state = state

    def save_state(self, state: bytes) -> None:
        self.state = state

    def load_state(self) -> bytes | None:
        return self.state


def _build_config(sim_th: float, depth: int, max_clusters: int) -> Any:
    config = TemplateMinerConfig()
    config.drain_sim_th = sim_th
    config.drain_depth = depth
    config.drain_max_clusters = max_clusters
    config.masking_instructions = [MaskingInstruction(p, name) for p, name in _MASKS]
    config.mask_prefix = "<"
    config.mask_suffix = ">"
    config.snapshot_compress_state = True
    config.profiling_enabled = False
    return config


class TemplateMiner:
    """Mine log templates with drain3 and track novelty and windowed counts.

    Deterministic: the same messages in the same order always yield the same
    template ids. Never reads wall time; timestamps come from ``ts`` (event time)
    or the injected clock.
    """

    def __init__(
        self,
        clock: Clock,
        *,
        warmup_seconds: int = 300,
        rarity_threshold: float = 0.001,
        novelty_ttl_s: int = 300,
        max_clusters: int = 1000,
        max_window_s: int = 300,
        sim_th: float = 0.4,
        depth: int = 4,
    ) -> None:
        """Create a miner.

        Args:
            clock: Time source used when ``add_message`` gets no ``ts``.
            warmup_seconds: Templates first seen within this many seconds of the
                first message are "known", never "new".
            rarity_threshold: After warm-up, a template whose share of all prior
                messages is below this is treated as new when it shows up again.
            novelty_ttl_s: How long a template stays new after becoming new.
            max_clusters: Memory cap on templates (drain3 LRU eviction).
            max_window_s: Longest window supported by the windowed counters.
            sim_th: drain3 similarity threshold.
            depth: drain3 prefix-tree depth.
        """
        self._clock = clock
        self._warmup_seconds = warmup_seconds
        self._rarity_threshold = rarity_threshold
        self._novelty_ttl_s = novelty_ttl_s
        self._max_clusters = max_clusters
        self._max_window_s = max_window_s
        self._config = _build_config(sim_th, depth, max_clusters)
        self._drain = _Drain3Miner(persistence_handler=None, config=self._config)

        self._stats: dict[int, _Stats] = {}
        self._service_counts: dict[str, Counter[int]] = {}
        self._windows: dict[str, deque[_Bucket]] = {}
        self._total = 0
        self._warmup_end: float | None = None
        self._current_s = 0

    # ── Ingest ────────────────────────────────────────────────────────

    def add_message(
        self, message: str, *, service: str = GLOBAL_SERVICE, ts: float | None = None
    ) -> int:
        """Mine one (already redacted) message and return its template id.

        Args:
            message: Log message body, after PII redaction.
            service: Service that emitted the message; scopes the windowed counts.
            ts: Event time. Defaults to ``clock.now()``.
        """
        event_ts = self._clock.now() if ts is None else ts
        if self._warmup_end is None:
            self._warmup_end = event_ts + self._warmup_seconds
        self._advance(int(event_ts))

        result = self._drain.add_log_message(message)
        template_id = int(result["cluster_id"])

        stats = self._stats.get(template_id)
        if stats is None:
            stats = _Stats(count=0, first_seen=event_ts, last_seen=event_ts, sample=message)
            self._stats[template_id] = stats
            if len(self._stats) > self._max_clusters:
                self._prune_evicted()

        self._update_novelty(stats, event_ts)

        stats.count += 1
        stats.last_seen = max(stats.last_seen, event_ts)
        stats.sample = message
        self._total += 1
        self._service_counts.setdefault(service, Counter())[template_id] += 1
        self._count_in_bucket(service, int(event_ts), template_id)
        return template_id

    def tick(self) -> None:
        """Advance to ``clock.now()`` and evict window buckets that fell out of range."""
        self._advance(int(self._clock.now()))
        cutoff = self._current_s - self._max_window_s
        for service, buckets in list(self._windows.items()):
            while buckets and buckets[0].second <= cutoff:
                buckets.popleft()
            if not buckets:
                del self._windows[service]

    # ── Queries ───────────────────────────────────────────────────────

    @property
    def total_messages(self) -> int:
        """Number of messages mined so far."""
        return self._total

    def get_template(self, template_id: int) -> TemplateInfo:
        """Return the current snapshot of a template.

        Raises:
            KeyError: If the id is unknown or was evicted by the memory cap.
        """
        return self._info(template_id, self._stats[template_id].count)

    def get_top_templates(
        self, n: int, *, service: str | None = None, window_s: int | None = None
    ) -> list[TemplateInfo]:
        """Return the ``n`` most frequent templates, ties broken by lowest id.

        With ``service`` and/or ``window_s``, ranking (and ``count``) uses only
        messages from that service and/or within the last ``window_s`` seconds.
        """
        if window_s is not None:
            counts = self._window_counts(window_s, service)
        elif service is not None:
            counts = self._service_counts.get(service, Counter())
        else:
            counts = Counter({tid: s.count for tid, s in self._stats.items()})
        ranked = sorted(
            ((tid, c) for tid, c in counts.items() if c > 0 and tid in self._stats),
            key=lambda item: (-item[1], item[0]),
        )
        return [self._info(tid, c) for tid, c in ranked[:n]]

    def is_new(self, template_id: int, now: float | None = None) -> bool:
        """Whether a template is currently considered new.

        New means it became novel (first seen after warm-up, or reappeared after
        warm-up while rarer than ``rarity_threshold``) within the last
        ``novelty_ttl_s`` seconds.
        """
        stats = self._stats.get(template_id)
        if stats is None or stats.novel_at is None:
            return False
        at = self._now() if now is None else now
        return at - stats.novel_at <= self._novelty_ttl_s

    def count_in_window(
        self, template_id: int, window_s: int, *, service: str | None = None
    ) -> int:
        """How many times a template appeared in the last ``window_s`` seconds."""
        return self._window_counts(window_s, service).get(template_id, 0)

    def new_templates_in_window(
        self, window_s: int, *, service: str | None = None
    ) -> dict[int, int]:
        """Counts over the last ``window_s`` seconds, for templates that are new now.

        Returns ``{template_id: count}``; intended for the new-pattern detector.
        """
        now = self._now()
        counts = self._window_counts(window_s, service)
        return {tid: c for tid, c in sorted(counts.items()) if c > 0 and self.is_new(tid, now)}

    # ── Persistence ───────────────────────────────────────────────────

    async def persist(self, path: str) -> None:
        """Atomically write drain3 state plus template statistics to ``path``.

        Windowed counts are transient and not persisted.
        """
        payload = json.dumps(self._snapshot(), sort_keys=True).encode("utf-8")
        await asyncio.to_thread(_atomic_write, Path(path), payload)

    async def restore(self, path: str) -> None:
        """Replace in-memory state with a snapshot written by ``persist``.

        Only load files this process wrote: drain3 state is jsonpickle-encoded.

        Raises:
            ValueError: If the file has an unsupported version.
        """
        raw = await asyncio.to_thread(Path(path).read_bytes)
        self._load(json.loads(raw))

    # ── Internals ─────────────────────────────────────────────────────

    def _now(self) -> float:
        return max(self._clock.now(), float(self._current_s))

    def _advance(self, second: int) -> None:
        if second > self._current_s:
            self._current_s = second

    def _update_novelty(self, stats: _Stats, event_ts: float) -> None:
        if self._warmup_end is None or event_ts < self._warmup_end:
            return
        if stats.count == 0:
            stats.novel_at = event_ts
            return
        currently_new = (
            stats.novel_at is not None and event_ts - stats.novel_at <= self._novelty_ttl_s
        )
        prior_rarity = stats.count / self._total if self._total else 0.0
        if not currently_new and prior_rarity < self._rarity_threshold:
            stats.novel_at = event_ts

    def _count_in_bucket(self, service: str, second: int, template_id: int) -> None:
        buckets = self._windows.setdefault(service, deque())
        if second <= self._current_s - self._max_window_s:
            return  # too old to be inside any supported window
        if not buckets or second > buckets[-1].second:
            buckets.append(_Bucket(second, Counter({template_id: 1})))
            return
        # Late event: walk back from the newest bucket (lateness is small).
        for i in range(len(buckets) - 1, -1, -1):
            if buckets[i].second == second:
                buckets[i].counts[template_id] += 1
                return
            if buckets[i].second < second:
                buckets.insert(i + 1, _Bucket(second, Counter({template_id: 1})))
                return
        buckets.appendleft(_Bucket(second, Counter({template_id: 1})))

    def _window_counts(self, window_s: int, service: str | None) -> Counter[int]:
        if window_s > self._max_window_s:
            raise ValueError(f"window_s={window_s} exceeds max_window_s={self._max_window_s}")
        cutoff = int(self._now()) - window_s
        services = [service] if service is not None else sorted(self._windows)
        total: Counter[int] = Counter()
        for svc in services:
            for bucket in reversed(self._windows.get(svc, ())):
                if bucket.second <= cutoff:
                    break
                total.update(bucket.counts)
        return total

    def _prune_evicted(self) -> None:
        live = {int(k) for k in self._drain.drain.id_to_cluster}
        for tid in [t for t in self._stats if t not in live]:
            del self._stats[tid]
            for counts in self._service_counts.values():
                counts.pop(tid, None)

    def _info(self, template_id: int, count: int) -> TemplateInfo:
        stats = self._stats[template_id]
        cluster = self._drain.drain.id_to_cluster.get(template_id)
        template = str(cluster.get_template()) if cluster is not None else stats.sample
        return TemplateInfo(
            id=template_id,
            template=template,
            count=count,
            first_seen=stats.first_seen,
            last_seen=stats.last_seen,
            sample=stats.sample,
            rarity=stats.count / self._total if self._total else 0.0,
        )

    def _snapshot(self) -> dict[str, Any]:
        handler = _MemoryPersistence()
        self._drain.persistence_handler = handler
        try:
            self._drain.save_state("tremor.persist")
        finally:
            self._drain.persistence_handler = None
        drain_state = handler.state or b""
        return {
            "version": STATE_VERSION,
            "drain_state": drain_state.decode("ascii"),  # drain3 emits base64(zlib(jsonpickle))
            "total": self._total,
            "warmup_end": self._warmup_end,
            "current_s": self._current_s,
            "templates": [
                {
                    "id": tid,
                    "count": s.count,
                    "first_seen": s.first_seen,
                    "last_seen": s.last_seen,
                    "sample": s.sample,
                    "novel_at": s.novel_at,
                }
                for tid, s in sorted(self._stats.items())
            ],
            "service_counts": {
                svc: {str(tid): c for tid, c in sorted(counts.items())}
                for svc, counts in sorted(self._service_counts.items())
            },
        }

    def _load(self, data: dict[str, Any]) -> None:
        version = data.get("version")
        if version != STATE_VERSION:
            raise ValueError(f"unsupported template state version: {version!r}")
        handler = _MemoryPersistence(str(data["drain_state"]).encode("ascii"))
        drain = _Drain3Miner(persistence_handler=handler, config=self._config)
        drain.persistence_handler = None
        self._drain = drain
        self._total = int(data["total"])
        warmup_end = data["warmup_end"]
        self._warmup_end = None if warmup_end is None else float(warmup_end)
        self._current_s = int(data["current_s"])
        self._stats = {
            int(t["id"]): _Stats(
                count=int(t["count"]),
                first_seen=float(t["first_seen"]),
                last_seen=float(t["last_seen"]),
                sample=str(t["sample"]),
                novel_at=None if t["novel_at"] is None else float(t["novel_at"]),
            )
            for t in data["templates"]
        }
        self._service_counts = {
            str(svc): Counter({int(tid): int(c) for tid, c in counts.items()})
            for svc, counts in data["service_counts"].items()
        }
        self._windows = {}


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(payload)
    os.replace(tmp, path)
