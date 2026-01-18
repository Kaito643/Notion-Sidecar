import sys
import argparse
from typing import List, Dict, Any

from src.config import config
from src.notion_client import NotionClient
from src.gemini_agent import GeminiAgent
from src.utils import setup_logger, print_colored

# Set up logging first
logger = setup_logger("Main")

def main() -> None:
    # 1. Parse Args
    parser = argparse.ArgumentParser(description="Notion Sidecar Agent")
    parser.add_argument("--debug", action="store_true", help="Run system diagnostics and exit")
    args = parser.parse_args()

    # 1.1 Run Diagnostics if requested
    if args.debug:
        from src.diagnostics import Diagnostics
        Diagnostics().run_all()
        return

    # 2. Validate Config
    if not config.validate():
        sys.exit(1)

    # 3. Initialize Clients
    try:
        print_colored("[INFO] Initializing Notion Client...", "cyan")
        notion = NotionClient()
        
        print_colored("[INFO] Initializing Gemini Agent...", "cyan")
        agent = GeminiAgent()
        
        print_colored("[SUCCESS] System Ready. Connected to Notion Page.", "green")
        print_colored(f"Target Page ID: {config.PAGE_ID}", "blue")
        print_colored("-" * 48, "white")
        print("Type 'exit' to quit, 'refresh' to reload content.\n")
        
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
                break
                
            if user_input.lower() == "refresh":
                print_colored("[INFO] Refreshing page state...", "blue")
                continue

            # 4.1 Fetch Current State
            print("[INFO] Reading page content...", end="\r")
            blocks = notion.get_page_blocks(config.PAGE_ID)
            if not blocks:
                print_colored("[WARNING] Page is empty or could not be read.", "yellow")
                # We continue anyway to allow the agent to potentially APPEND to an empty page
            else:
                print(f"[INFO] Read {len(blocks)} blocks.       ")

            # 4.2 Agent Reasoning
            print("[INFO] Processing...", end="\r")
            decision = agent.analyze_and_act(user_input, blocks)
            
            action = decision.get("action")
            text = decision.get("text", "")
            
            # 4.3 Execution
            if action == "UPDATE":
                idx = decision.get("target_block_index")
                if idx is not None and 0 <= idx < len(blocks):
                    target_block = blocks[idx]
                    target_id = target_block['id']
                    target_type = decision.get("block_type", target_block['type'])
                    
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
                success = notion.append_block(config.PAGE_ID, text, block_type=block_type)
                
                if success:
                    print_colored("[SUCCESS] Appended successfully.", "green")
                else:
                    print_colored("[ERROR] Append failed.", "red")

            elif action == "DELETE":
                idx = decision.get("target_block_index")
                if idx is not None and 0 <= idx < len(blocks):
                    target_block = blocks[idx]
                    target_id = target_block['id']
                    
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
                    target_id = target_block['id']
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
            print_colored("\n[INFO] Exiting application...", "yellow")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
