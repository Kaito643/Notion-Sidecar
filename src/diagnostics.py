from typing import List

import google.generativeai as genai

from src.config import config
from src.utils import print_colored, setup_logger

logger = setup_logger("Diagnostics", "INFO")


class Diagnostics:
    def __init__(self) -> None:
        self.api_key = config.gemini_api_key

    def run_all(self) -> None:
        print_colored("\n🔍 Starting System Diagnostics...", "cyan")
        print_colored("--------------------------------", "white")

        # 1. Check API Key configuration
        if not self._check_api_key():
            return

        # 2. List Available Models
        available_models = self._list_available_models()

        # 3. Test Connectivity & Quota with Default Model
        self._test_default_model(available_models)

        print_colored("--------------------------------", "white")
        print_colored("✅ Diagnostics Complete.", "cyan")

    def _check_api_key(self) -> bool:
        print("[1/3] Checking API Key Config...", end=" ")
        if not self.api_key:
            print_colored("FAILED", "red")
            print_colored("❌ GEMINI_API_KEY is missing in .env", "yellow")
            return False

        try:
            genai.configure(api_key=self.api_key)
            print_colored("OK", "green")
            return True
        except Exception as e:
            print_colored("ERROR", "red")
            logger.error(f"API Configuration failed: {e}")
            return False

    def _list_available_models(self) -> List[str]:
        print("\n[2/3] Fetching Available Gemini Models...")
        models_found = []
        try:
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    print(f"  - {m.name}")
                    models_found.append(m.name)

            if not models_found:
                print_colored("  ⚠️  No 'generateContent' models found for this API key.", "yellow")
            else:
                print_colored(f"  ✅ Found {len(models_found)} capable models.", "green")

            return models_found
        except Exception as e:
            print_colored("  ❌ Failed to list models.", "red")
            print_colored(f"  Error: {e}", "white")
            return []

    def _test_default_model(self, available_models: List[str]) -> None:
        print("\n[3/3] Finding a working model...")

        # Priority list of models to try
        models_to_try = [
            config.gemini_model,  # Try configured one first
            "gemini-2.0-flash-exp",
            "gemini-2.0-flash",
            "gemini-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]

        # Add any "flash" models found dynamically
        for m in available_models:
            clean_name = m.replace("models/", "")
            if clean_name not in models_to_try and "flash" in clean_name:
                models_to_try.append(clean_name)

        tested = set()
        working_model = None

        for model_name in models_to_try:
            # Handle 'models/' prefix loose matching
            target = model_name
            if (
                not model_name.startswith("models/")
                and f"models/{model_name}" not in available_models
            ):
                # Skip if not in the user's available list at all unless it's an alias
                # But allow it if we are just trying blind
                pass

            if target in tested:
                continue
            tested.add(target)

            print(f"  Testing '{target}'...", end="")
            try:
                model = genai.GenerativeModel(target)
                model.generate_content("Hello")
                print_colored(" OK", "green")
                working_model = target
                break
            except Exception:
                print_colored(" Failed", "red")

        if working_model:
            clean_model = working_model.replace("models/", "")
            print_colored(
                f"\n✅ RECOMMENDED FIX: Set GEMINI_MODEL={clean_model} in your .env file.",
                "green",
            )
            # verification logic
        else:
            print_colored(
                "\n❌ Could not find any working model with current quota/permissions.", "red"
            )
            print("  Please check your billing and API limits at https://aistudio.google.com/")


if __name__ == "__main__":
    diag = Diagnostics()
    diag.run_all()
