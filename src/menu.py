import os
from typing import Tuple

from src.config import config
from src.utils import (
    clear_screen,
    extract_page_id,
    print_colored,
    select_gemini_model,
    update_env_file,
)


class InteractiveMenu:
    def __init__(self) -> None:
        self.running = True

    def display_status(self) -> None:
        """Show current configuration status"""
        print_colored("\n=== Configuration Status ===", "white")
        print("")

        def print_row(
            label: str, env_key: str, command: str, preview: str = "", secret: bool = False
        ) -> None:
            value = os.getenv(env_key)
            if value:
                status_icon = "[OK]"
                if secret:
                    preview_text = "********"
                else:
                    preview_text = f"{preview or value}"

                # Green for OK
                print_colored(f"{label:<15} {status_icon} {preview_text:<40}", "green")
            else:
                status_icon = "[MISSING]"
                # Red for MISSING
                print_colored(f"{label:<15} {status_icon} {'':<40}", "red")

        # Notion Token (Secret)
        print_row("Notion API", "NOTION_TOKEN", "notion-api", secret=True)

        # Gemini API (Secret)
        print_row("Gemini API", "GEMINI_API_KEY", "gemini-api", secret=True)

        # Notion Page
        # Construct a link if only ID is available
        page_id = os.getenv("PAGE_ID", "")
        if page_id:
            page_link = f"https://notion.so/{page_id}"
        else:
            page_link = ""

        print_row("Notion Page", "PAGE_ID", "notion-link", preview=page_link)

        # Model
        current_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        print_colored(f"{'Gemini Model':<15} [OK] {current_model:<40}", "cyan")

        print_colored("-" * 65, "white")

        # Check if ready
        if os.getenv("NOTION_TOKEN") and os.getenv("GEMINI_API_KEY") and os.getenv("PAGE_ID"):
            print_colored("System Ready!", "green")
        else:
            print_colored("Configuration missing.", "yellow")

    def run(self) -> Tuple[bool, str]:
        """
        Run the interactive menu loop.
        Returns: (should_run_agent, selected_model_name)
        """
        print_colored("\nWelcome to Notion Sidecar Agent Setup", "cyan")

        self.display_status()

        while self.running:
            try:
                user_input = input("\nSetup > ").strip()
                parts = user_input.split()
                if not parts:
                    continue

                command = parts[0].lower()
                args = parts[1:]

                if command in ["exit", "quit", "q"]:
                    print_colored("Exiting setup.", "yellow")
                    return False, ""

                elif command == "go":
                    if config.validate(print_errors=True):
                        clear_screen()
                        return True, config.gemini_model
                    else:
                        print_colored("Cannot start: Missing configuration.", "red")

                elif command == "status":
                    self.display_status()

                elif command == "help":
                    print_colored("\nAvailable Commands:", "cyan")
                    print("  set <attr> <val>  : Set config (e.g. model, notion-link)")
                    print("  unset <attr>      : Clear config")
                    print("  status            : Show current status")
                    print("  go                : Start the agent")
                    print("  exit              : Exit application")
                    print("  help              : Show this message")
                    print("\nInteractive:")
                    print("  model             : Select model from list")
                    print("  notion-link       : Paste Notion link interactively")
                    print("  gemini-api        : Enter Gemini API key interactively")
                    print("  notion-api        : Enter Notion Token interactively")

                # Handle SET command
                elif command == "set":
                    if len(args) < 2:
                        print_colored("Usage: set <attribute> <value>", "yellow")
                        continue

                    target = args[0].lower()
                    value = " ".join(args[1:])  # Rejoin rest of args as value

                    if target == "notion-link":
                        page_id = extract_page_id(value)
                        if page_id and update_env_file("PAGE_ID", page_id):
                            print_colored(f"Page ID set: {page_id}", "green")
                            config.reload()

                    elif target == "gemini-api":
                        if update_env_file("GEMINI_API_KEY", value):
                            print_colored("Gemini API Key set.", "green")
                            config.reload()

                    elif target == "notion-api":
                        if update_env_file("NOTION_TOKEN", value):
                            print_colored("Notion Token set.", "green")
                            config.reload()

                    elif target == "model":
                        if update_env_file("GEMINI_MODEL", value):
                            print_colored(f"Model set to: {value}", "green")
                            config.reload()
                    else:
                        print_colored(f"Unknown attribute: {target}", "yellow")

                # Handle UNSET command
                elif command == "unset":
                    if len(args) < 1:
                        print_colored("Usage: unset <attribute>", "yellow")
                        continue

                    target = args[0].lower()

                    if target == "notion-link":
                        update_env_file("PAGE_ID", "")
                        print_colored("Notion Page ID unset.", "yellow")
                        config.reload()
                    elif target == "gemini-api":
                        update_env_file("GEMINI_API_KEY", "")
                        print_colored("Gemini API Key unset.", "yellow")
                        config.reload()
                    elif target == "notion-api":
                        update_env_file("NOTION_TOKEN", "")
                        print_colored("Notion Token unset.", "yellow")
                        config.reload()
                    elif target == "model":
                        update_env_file("GEMINI_MODEL", "gemini-2.5-flash")  # Reset to default
                        print_colored("Model reset to default.", "yellow")
                        config.reload()
                    else:
                        print_colored(f"Unknown attribute: {target}", "yellow")

                # Legacy interactive commands (kept for backward compatibility / menu usage)
                elif command == "model":
                    selected = select_gemini_model()
                    if selected:
                        if update_env_file("GEMINI_MODEL", selected):
                            print_colored(f"Model updated to: {selected}", "green")
                            config.reload()

                elif command == "notion-link":
                    url = input("Paste Notion Link: ").strip()
                    page_id = extract_page_id(url)
                    if page_id:
                        if update_env_file("PAGE_ID", page_id):
                            print_colored(f"Page ID saved: {page_id}", "green")
                            config.reload()

                elif command == "gemini-api":
                    key = input("Enter Gemini API Key: ").strip()
                    if key:
                        if update_env_file("GEMINI_API_KEY", key):
                            print_colored("Gemini API Key saved.", "green")
                            config.reload()

                elif command == "notion-api":
                    token = input("Enter Notion Integration Token: ").strip()
                    if token:
                        if update_env_file("NOTION_TOKEN", token):
                            print_colored("Notion Token saved.", "green")
                            config.reload()

                else:
                    print_colored(f"Unknown command: '{command}'. Type 'help'.", "yellow")

            except KeyboardInterrupt:
                print_colored("\nExiting...", "yellow")
                return False, ""

        return False, ""
