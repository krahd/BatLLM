"""
main_conversation_cli.py
========================

Entry point for running the interactive ConversationCLI with the BatLLM model.
"""

from tests.conversation_cli import ConversationCLI



def main() -> None:
    """Start the interactive chat session."""
    try:
        cli = ConversationCLI()
        cli.run()

    except KeyboardInterrupt:
        print("[info] ConversationCLI interrupted by user (Ctrl+C).")

    except EOFError:
        print("[info] ConversationCLI received EOF; exiting.")


if __name__ == "__main__":
    main()
