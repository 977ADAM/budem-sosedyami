import unittest

from app.domain.conversation import Conversation, Turn
from app.infrastructure.fernet_codec import FernetConversationCodec


class FernetConversationCodecTests(unittest.TestCase):
    def setUp(self) -> None:
        self.codec = FernetConversationCodec("secret", ttl_seconds=60)
        self.conversation = Conversation("anton", (Turn("Привет", "Здравствуйте"),))

    def test_round_trip_hides_the_text(self) -> None:
        token = self.codec.seal(self.conversation)
        self.assertNotIn("Привет", token)
        self.assertEqual(self.codec.unseal(token, "anton"), self.conversation)

    def test_unusable_tokens_give_an_empty_conversation(self) -> None:
        token = self.codec.seal(self.conversation)
        cases = {
            "missing": (None, "anton"),
            "foreign neighbor": (token, "vera"),
            "tampered": (token[:-4] + "AAAA", "anton"),
            "garbage": ("garbage", "anton"),
            "other secret": (FernetConversationCodec("other", 60).seal(self.conversation), "anton"),
        }
        for name, (candidate, neighbor_id) in cases.items():
            with self.subTest(name):
                self.assertEqual(self.codec.unseal(candidate, neighbor_id), Conversation(neighbor_id))

    def test_expired_token_gives_an_empty_conversation(self) -> None:
        token = self.codec.seal(self.conversation)
        expired = FernetConversationCodec("secret", ttl_seconds=-1)
        self.assertEqual(expired.unseal(token, "anton"), Conversation("anton"))
