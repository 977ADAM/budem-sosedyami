"""A fictional neighbor who may only talk about the facts in their profile."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Fact:
    question: str
    answer: str


@dataclass(frozen=True, slots=True)
class Neighbor:
    id: str
    name: str
    persona: str
    intro: str
    project: str
    district: str
    feature: str
    facts: tuple[Fact, ...]
