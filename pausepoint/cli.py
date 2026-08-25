import argparse
import json
from pathlib import Path

from .engine import ConversationEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a conversation as a message stream")
    parser.add_argument("--conversation", type=Path, required=True)
    args = parser.parse_args()

    engine = ConversationEngine()
    with args.conversation.open(encoding="utf-8") as handle:
        for line in handle:
            message = json.loads(line)
            result = engine.process(message["sender"], message["text"])
            print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
