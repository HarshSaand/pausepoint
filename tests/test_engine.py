import unittest

from pausepoint.engine import ConversationEngine
from pausepoint.features import extract, normalise


class PausePointTest(unittest.TestCase):
    def test_otp_obfuscation_is_normalised(self):
        self.assertIn("otp", normalise("Send the O.T.P now"))
        self.assertTrue(extract("Send the O.T.P now")["credential"])

    def test_risk_builds_across_turns(self):
        engine = ConversationEngine()
        first = engine.process("contact", "I am from your bank's fraud team")
        second = engine.process("contact", "Act immediately and do not tell anyone")
        third = engine.process("contact", "Read me the OTP")
        self.assertLess(first["risk"], second["risk"])
        self.assertLess(second["risk"], third["risk"])
        self.assertEqual(third["action"], "warn_and_verify")

    def test_benign_message_stays_in_monitoring(self):
        result = ConversationEngine().process("friend", "Are we still meeting for lunch?")
        self.assertEqual(result["stage"], "benign")
        self.assertEqual(result["action"], "monitor")


if __name__ == "__main__":
    unittest.main()
