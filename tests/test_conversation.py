import unittest
from companion.conversation import context_history


class ConversationTests(unittest.TestCase):
    def test_current_request_not_duplicated(self):
        state = {"conversation": [{"role": "user", "content": "warm"},
                                  {"role": "assistant", "content": "applied"},
                                  {"role": "user", "content": "less"}]}
        self.assertEqual([m["content"] for m in context_history(state)], ["warm", "applied"])

    def test_context_is_bounded_and_keeps_recent_messages(self):
        state = {"conversation": [{"role": "assistant", "content": str(i) * 7000} for i in range(32)]}
        result = context_history(state)
        self.assertLessEqual(sum(len(m["content"]) for m in result), 24000)
        self.assertTrue(result[-1]["content"].startswith("31"))

    def test_old_runtime_without_history(self):
        self.assertEqual(context_history({}), [])
