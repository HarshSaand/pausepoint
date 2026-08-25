from dataclasses import dataclass, field
from time import perf_counter

from .features import extract


WEIGHTS = {"authority": 0.14, "urgency": 0.18, "isolation": 0.24, "credential": 0.36, "payment": 0.34, "url": 0.08, "phone": 0.04, "amount": 0.08}


@dataclass
class ConversationEngine:
    history: list[dict] = field(default_factory=list)
    risk: float = 0.0
    peak_risk: float = 0.0

    def process(self, sender: str, text: str) -> dict:
        started = perf_counter()
        signals = extract(text)
        message_risk = min(1.0, sum(WEIGHTS[name] for name, present in signals.items() if present))
        self.risk = min(1.0, 0.72 * self.risk + message_risk)
        self.peak_risk = max(self.peak_risk, self.risk)

        stage = self._stage(signals)
        action = self._action(signals)
        turn = len(self.history) + 1
        evidence = [name for name, present in signals.items() if present]
        record = {"turn": turn, "sender": sender, "text": text, "risk": round(self.risk, 3), "stage": stage, "action": action, "evidence": evidence, "latency_ms": round((perf_counter() - started) * 1000, 3)}
        self.history.append(record)
        self.history = self.history[-8:]
        return record

    def _stage(self, signals: dict[str, bool]) -> str:
        if signals["credential"] or signals["payment"]:
            return "credential_or_payment"
        if signals["isolation"]:
            return "isolation"
        if signals["urgency"]:
            return "urgency"
        if signals["authority"]:
            return "authority"
        return "benign"

    def _action(self, signals: dict[str, bool]) -> str:
        explicit_request = signals["credential"] or signals["payment"]
        if self.risk >= 0.72 or (self.risk >= 0.55 and explicit_request):
            return "warn_and_verify"
        if self.risk >= 0.35:
            return "llm_review"
        return "monitor"
