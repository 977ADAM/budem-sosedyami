import unittest
import warnings
from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage, SystemMessage

from app.chat_graph import build_chat_graph, invoke_chat


class ChatGraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_node_receives_config_and_prompts_the_selected_agent(self) -> None:
        model = AsyncMock()
        model.ainvoke = AsyncMock(return_value=AIMessage(content="Ответ соседа."))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            graph = build_chat_graph(model)
            reply = await invoke_chat(graph, "anton", "Где кофе?", [])

        self.assertEqual(reply, "Ответ соседа.")
        self.assertFalse(
            [item for item in caught if "config" in str(item.message)],
            "LangGraph should accept the RunnableConfig annotation",
        )
        messages = model.ainvoke.await_args.args[0]
        self.assertIsInstance(messages[0], SystemMessage)
        self.assertIn("Антон", messages[0].content)
        self.assertEqual(messages[-1].content, "Где кофе?")
