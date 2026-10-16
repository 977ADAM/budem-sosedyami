import unittest

from app.domain.conversation import MAX_TURNS, Conversation, Turn


class ConversationTests(unittest.TestCase):
    def test_with_turn_returns_a_new_conversation(self) -> None:
        empty = Conversation("anton")
        updated = empty.with_turn(Turn("Привет", "Здравствуйте"))
        self.assertEqual(empty.turns, ())
        self.assertEqual(updated.turns, (Turn("Привет", "Здравствуйте"),))

    def test_old_turns_are_forgotten_in_blocks(self) -> None:
        conversation = Conversation("anton")
        for i in range(MAX_TURNS):
            conversation = conversation.with_turn(Turn(str(i), "ok"))
        self.assertEqual(len(conversation.turns), MAX_TURNS)

        conversation = conversation.with_turn(Turn("overflow", "ok"))
        self.assertEqual(len(conversation.turns), MAX_TURNS // 2)
        self.assertEqual(conversation.turns[-1].message, "overflow")

        first = conversation.turns[0]
        conversation = conversation.with_turn(Turn("next", "ok"))
        self.assertEqual(conversation.turns[0], first)
