"""Временная память диалогов локального демо."""

from typing import TypedDict


class DialogueTurn(TypedDict):
    question_id: str
    question: str
    reply: str


DIALOGUES: dict[str, list[DialogueTurn]] = {}
DIALOGUE_GENERATIONS: dict[str, int] = {}


def generation(agent_id: str) -> int:
    return DIALOGUE_GENERATIONS.get(agent_id, 0)


def append_turn(agent_id: str, turn: DialogueTurn, request_generation: int) -> bool:
    if generation(agent_id) != request_generation:
        return False
    DIALOGUES.setdefault(agent_id, []).append(turn)
    return True


def reset_dialogues() -> None:
    for agent_id in DIALOGUE_GENERATIONS.keys() | DIALOGUES.keys():
        DIALOGUE_GENERATIONS[agent_id] = generation(agent_id) + 1
    DIALOGUES.clear()
