import argparse
import sys

from src.config import config
from src.gemini_agent import GeminiAgent
from src.notion_client import NotionClient
from src.utils import clear_screen, print_colored, setup_logger

# Set up logging first
logger = setup_logger("Main")


def main() -> None:
    # 1. Parse Args
    parser = argparse.ArgumentParser(description="Notion Sidecar Agent")
    parser.add_argument("--diagnostics", action="store_true", help="Run diagnostics and exit")
    parser.add_argument("--debug", action="store_true", help="Enable verbose error logging")
    parser.add_argument("--select-model", action="store_true", help="Select Gemini model")
    args = parser.parse_args()

    # 1.1 Run Diagnostics if requested
    # 1.1 Run Diagnostics if requested
    if args.diagnostics:
        from src.diagnostics import Diagnostics

        Diagnostics().run_all()
        return

    # Outer Application Loop
    while True:
        clear_screen()
        # 2. Interactive Menu
        # Run by default unless specific args are present (like diagnostics)
        # Reload config to ensure we have latest env vars before validation
        config.reload()

        current_model = ""

        from src.menu import InteractiveMenu

        menu = InteractiveMenu()
        run_agent, selected_model = menu.run()

        if not run_agent:
            # User chose exit in menu
            sys.exit(0)

        current_model = selected_model

        # 3. Initialize Clients
        try:
            print_colored("[INFO] Initializing Notion Client...", "cyan")
            notion = NotionClient()

            print_colored("[INFO] Initializing Gemini Agent...", "cyan")
            agent = GeminiAgent(model_name=current_model, debug=args.debug)

            print_colored("[SUCCESS] System Ready. Connected to Notion Page.", "green")
            print_colored(f"Target Page ID: {config.page_id}", "blue")

        except Exception as e:
            logger.critical(f"Initialization failed: {e}")
            sys.exit(1)

        # 4. Main REPL Loop
        while True:
            try:
                user_input = input("\nCommand: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit", "q"]:
                    print_colored("[INFO] Exiting application...", "yellow")
                    sys.exit(0)

                if user_input.lower() == "back":
                    print_colored("[INFO] Returning to menu...", "yellow")
                    # inner loop breaks, outer loop continues -> calls clear_screen() -> menu
                    break  # Break inner loop to return to outer loop (Menu)

                if user_input.lower() == "help":
                    print_colored("\nAvailable Commands:", "cyan")
                    print("  <text>    : Send instructions to Agent")
                    print("  refresh   : Reload page content")
                    print("  back      : Return to configuration menu")
                    print("  exit      : Exit application")
                    continue

                if user_input.lower() == "refresh":
                    print_colored("[INFO] Refreshing page state...", "blue")
                    continue

                # 4.1 Fetch Current State
                print("[INFO] Reading page content...", end="\r")
                blocks = notion.get_page_blocks(config.page_id)
                if not blocks:
                    print_colored("[WARNING] Page is empty or could not be read.", "yellow")
                    # We continue anyway to allow the agent to potentially APPEND to an empty page
                else:
                    print(f"[INFO] Read {len(blocks)} blocks.       ")

                # 4.2 Agent Reasoning
                print("[INFO] Processing...", end="\r")
                try:
                    decision = agent.analyze_and_act(user_input, blocks)

                    action = decision.get("action")
                    text = decision.get("text", "")
                except Exception as e:
                    if args.debug:
                        print_colored(f"\n[ERROR] Model execution failed: {e}", "red")
                    else:
                        print_colored("\n[ERROR] Execution failed. Use --debug for info.", "red")

                    print_colored("[INFO] You can switch to a different model.", "yellow")

                    from src.utils import select_gemini_model

                    new_model = select_gemini_model()

                    if new_model:
                        agent = GeminiAgent(model_name=new_model, debug=args.debug)
                        print_colored(f"[SUCCESS] Switched to model: {new_model}", "green")
                        print_colored("Please retry your command.", "white")
                    else:
                        print_colored("[WARNING] No model selected. Retrying next time.", "yellow")
                    continue

                # 4.3 Execution
                if action == "UPDATE":
                    idx = decision.get("target_block_index")
                    if idx is not None and 0 <= idx < len(blocks):
                        target_block = blocks[idx]
                        target_id = target_block["id"]
                        target_type = decision.get("block_type", target_block["type"])

                        print_colored(f"[INFO] Updating block [{idx}]...", "cyan")
                        success = notion.update_block(target_id, text, block_type=target_type)

                        if success:
                            print_colored("[SUCCESS] Update successful.", "green")
                        else:
                            print_colored("[ERROR] Update failed.", "red")
                    else:
                        print_colored(f"[ERROR] Invalid block index: {idx}", "red")

                elif action == "APPEND":
                    print_colored("[INFO] Appending new block...", "cyan")
                    block_type = decision.get("block_type", "paragraph")
                    success = notion.append_block(config.page_id, text, block_type=block_type)

                    if success:
                        print_colored("[SUCCESS] Appended successfully.", "green")
                    else:
                        print_colored("[ERROR] Append failed.", "red")

                elif action == "DELETE":
                    idx = decision.get("target_block_index")
                    if idx is not None and 0 <= idx < len(blocks):
                        target_block = blocks[idx]
                        target_id = target_block["id"]

                        print_colored(f"[INFO] Deleting block [{idx}]...", "cyan")
                        success = notion.delete_block(target_id)

                        if success:
                            print_colored("[SUCCESS] Block deleted.", "green")
                        else:
                            print_colored("[ERROR] Delete failed.", "red")
                    else:
                        print_colored(f"[ERROR] Invalid block index for DELETE: {idx}", "red")

                elif action == "INSERT":
                    idx = decision.get("target_block_index")
                    if idx is not None and 0 <= idx < len(blocks):
                        target_block = blocks[idx]
                        target_id = target_block["id"]
                        block_type = decision.get("block_type", "paragraph")

                        print_colored(f"[INFO] Inserting block after [{idx}]...", "cyan")
                        success = notion.insert_block_after(target_id, text, block_type=block_type)

                        if success:
                            print_colored("[SUCCESS] Block inserted.", "green")
                        else:
                            print_colored("[ERROR] Insert failed.", "red")
                    else:
                        print_colored(f"[ERROR] Invalid block index for INSERT: {idx}", "red")

                elif action == "CHAT":
                    print_colored(f"\n[AGENT] {text}", "white")

                else:
                    print_colored(f"[WARNING] Unknown action: {action}", "yellow")

            except KeyboardInterrupt:
                print_colored("\n[INFO] Returning to menu...", "yellow")
                break  # Return to menu on Ctrl+C from main loop
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
