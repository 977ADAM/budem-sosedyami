import unittest

from fakes import FakeChatModel

from app.application.agent_service import AgentService
from app.application.errors import ChatModelTimeout, NeighborNotFound
from app.infrastructure.fernet_codec import FernetConversationCodec
from app.infrastructure.neighbor_catalog import StaticNeighborRepository


class ChatWithNeighborTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.model = FakeChatModel()
        self.chat = AgentService(
            neighbors=StaticNeighborRepository(),
            model=self.model,
            codec=FernetConversationCodec("secret", ttl_seconds=60),
        )

    async def test_context_carries_the_conversation_between_calls(self) -> None:
        first = await self.chat("marina", "Привет", None)
        self.assertEqual(first.reply, "Ответ")
        system_prompt, _, _ = self.model.calls[-1]
        self.assertIn("Марина", system_prompt)

        second = await self.chat("marina", "А потом?", first.context)
        self.assertEqual(self.model.last_dialog, ["Привет", "Ответ", "А потом?"])

        await self.chat("marina", "И ещё", second.context)
        self.assertEqual(self.model.last_dialog, ["Привет", "Ответ", "А потом?", "Ответ", "И ещё"])

    async def test_unknown_neighbor_is_rejected_before_calling_the_model(self) -> None:
        with self.assertRaises(NeighborNotFound):
            await self.chat("nobody", "Привет", None)
        self.assertEqual(self.model.calls, [])

    async def test_failed_reply_leaves_the_previous_context_usable(self) -> None:
        context = (await self.chat("pavel", "Первое", None)).context
        self.model.error = ChatModelTimeout()
        with self.assertRaises(ChatModelTimeout):
            await self.chat("pavel", "Потерянное", context)

        self.model.error = None
        await self.chat("pavel", "Второе", context)
        self.assertEqual(self.model.last_dialog, ["Первое", "Ответ", "Второе"])
