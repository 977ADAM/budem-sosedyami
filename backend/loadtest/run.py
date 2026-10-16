"""Load generator: virtual users hold conversations and pass `context` back like a frontend.

    uv run python -m loadtest.run --url http://127.0.0.1:8100 --users 100 --turns 35
"""

from __future__ import annotations

import argparse
import asyncio
import random
import statistics
import time
from collections import Counter
from dataclasses import dataclass, field

import httpx

AGENTS = ("anton", "marina", "pavel", "vera")
QUESTIONS = (
    "Где ты бегаешь по утрам?",
    "Куда ходишь за кофе и сколько туда идти?",
    "Как вы проводите выходные с дочкой, есть ли рядом парк или сквер?",
    "Удобно ли отсюда добираться до центра на метро или автобусе?",
    "Что интересного есть рядом: галереи, кафе, мастерские?",
)


@dataclass
class Stats:
    latencies_ms: list[float] = field(default_factory=list)
    statuses: Counter = field(default_factory=Counter)
    context_bytes: list[int] = field(default_factory=list)
    latency_by_turn: dict[int, list[float]] = field(default_factory=dict)
    network_errors: Counter = field(default_factory=Counter)


async def user(client: httpx.AsyncClient, url: str, turns: int, think: float, stats: Stats) -> None:
    agent = random.choice(AGENTS)
    context = None
    for turn in range(turns):
        body = {"message": random.choice(QUESTIONS)}
        if context:
            body["context"] = context
        started = time.perf_counter()
        try:
            response = await client.post(f"{url}/api/agents/{agent}/chat", json=body)
        except httpx.HTTPError as exc:
            stats.network_errors[type(exc).__name__] += 1
            continue
        elapsed = (time.perf_counter() - started) * 1000
        stats.latencies_ms.append(elapsed)
        stats.latency_by_turn.setdefault(turn, []).append(elapsed)
        stats.statuses[response.status_code] += 1
        if response.status_code == 200:
            context = response.json()["context"]
            stats.context_bytes.append(len(context))
        if think:
            await asyncio.sleep(random.uniform(0, think))


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def report(stats: Stats, users: int, turns: int, elapsed: float) -> None:
    total = sum(stats.statuses.values())
    lat = stats.latencies_ms
    print(f"users={users} turns={turns} requests={total} time={elapsed:.1f}s rps={total / elapsed:.1f}")
    print(f"  statuses={dict(stats.statuses)} network_errors={dict(stats.network_errors)}")
    print(
        f"  latency ms: p50={percentile(lat, .5):.0f} p95={percentile(lat, .95):.0f} "
        f"p99={percentile(lat, .99):.0f} max={max(lat, default=0):.0f}"
    )
    if stats.context_bytes:
        print(
            f"  context bytes: median={statistics.median(stats.context_bytes):.0f} "
            f"max={max(stats.context_bytes)}"
        )
    first, last = stats.latency_by_turn.get(0, []), stats.latency_by_turn.get(turns - 1, [])
    if first and last:
        print(f"  median latency first turn={statistics.median(first):.0f}ms last turn={statistics.median(last):.0f}ms")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8100")
    parser.add_argument("--users", type=int, default=50)
    parser.add_argument("--turns", type=int, default=35)
    parser.add_argument("--think", type=float, default=0.0, help="max pause between messages, s")
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    stats = Stats()
    limits = httpx.Limits(max_connections=args.users, max_keepalive_connections=args.users)
    async with httpx.AsyncClient(timeout=args.timeout, limits=limits) as client:
        started = time.perf_counter()
        await asyncio.gather(
            *(user(client, args.url, args.turns, args.think, stats) for _ in range(args.users))
        )
        elapsed = time.perf_counter() - started
    report(stats, args.users, args.turns, elapsed)


if __name__ == "__main__":
    asyncio.run(main())
