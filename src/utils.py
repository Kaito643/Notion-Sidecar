import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

import google.generativeai as genai

from src.config import config


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def setup_logger(name: str = "GeminiAgent", level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with colorful console output
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        # Custom formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def print_colored(text: str, color: str = "cyan") -> None:
    """Print colored text to terminal"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")


def update_env_file(key: str, value: str) -> bool:
    """
    Update or add a key-value pair in the .env file.
    Non-destructive updates (keeps comments and structure).
    """
    env_path = Path(".env")
    try:
        if not env_path.exists():
            env_path.write_text(f'{key}="{value}"\n')
            return True

        content = env_path.read_text()

        # Regex to find the key line:
        # ^ - start of line
        # \s* - optional whitespace
        # KEY - the key name
        # \s*=\s* - equals sign with optional whitespace
        # (?:['"]?) - optional quote
        # (.*?) - capture current value (non-greedy)
        # (?:['"]?) - optional closing quote
        # $ - end of line
        pattern = re.compile(rf'^{key}\s*=\s*["\']?(.*?)["\']?$', re.MULTILINE)

        if pattern.search(content):
            new_content = pattern.sub(f'{key}="{value}"', content)
        else:
            # Append if not found
            if content and not content.endswith("\n"):
                new_content = content + f'\n{key}="{value}"\n'
            else:
                new_content = content + f'{key}="{value}"\n'

        env_path.write_text(new_content)
        return True
    except Exception as e:
        print_colored(f"[ERROR] Failed to update .env: {e}", "red")
        return False


def extract_page_id(url_or_id: str) -> Optional[str]:
    """
    Extract Notion Page ID from a URL or validate a raw ID.
    Notion IDs are 32 chars hex. URLs usually end with <description>-<32charID>.
    """
    # 1. Clean the input
    text = url_or_id.strip()

    # 2. Try raw 32-char hex check
    # Sometimes it comes with dashes (version 4 UUID), remove them
    clean_id = text.replace("-", "")
    if len(clean_id) == 32 and re.match(r"^[a-fA-F0-9]{32}$", clean_id):
        return clean_id

    # 3. Try parsing URL
    # Example: https://www.notion.so/username/Page-Title-1234567890abcdef1234567890abcdef
    match = re.search(r"([a-fA-F0-9]{32})", text)
    if match:
        return match.group(1)

    print_colored("[ERROR] Could not extract a valid Page ID.", "red")
    return None


def select_gemini_model() -> Optional[str]:
    """
    Interactively select a Gemini model from the available list.
    Returns the selected model name or None if selection failed/cancelled.
    """
    try:
        genai.configure(api_key=config.gemini_api_key)
        print_colored("\n[INFO] Fetching available Gemini models...", "cyan")

        models: list[str] = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                models.append(m.name)

        if not models:
            print_colored("[ERROR] No suitable models found.", "red")
            return None

        print_colored("\nAvailable Models:", "white")
        print("0. Exit / Cancel")
        for i, model in enumerate(models):
            name = model.replace("models/", "")
            print(f"{i + 1}. {name}")

        while True:
            try:
                choice = input("\nSelect a model (number) [Default: 1]: ").strip()
                if not choice:
                    return models[0].replace("models/", "")

                if choice == "0":
                    print_colored("Selection cancelled.", "yellow")
                    return None

                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    return models[idx].replace("models/", "")
                else:
                    print_colored("Invalid selection. Please try again.", "yellow")
            except ValueError:
                print_colored("Please enter a number.", "yellow")

    except Exception as e:
        print_colored(f"[ERROR] Failed to list models: {e}", "red")
        return None
