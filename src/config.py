import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration and validation"""

    @property
    def notion_token(self) -> str:
        token = os.getenv("NOTION_TOKEN")
        if not token:
            self._error("NOTION_TOKEN environment variable is not set.")
        assert token is not None
        return token

    @property
    def page_id(self) -> str:
        page_id = os.getenv("PAGE_ID")
        if not page_id:
            self._error("PAGE_ID environment variable is not set.")
        assert page_id is not None
        return page_id

    @property
    def gemini_api_key(self) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self._error("GEMINI_API_KEY environment variable is not set.")
        assert api_key is not None
        return api_key

    @property
    def gemini_model(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    @property
    def log_level(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")

    def validate(self) -> bool:
        """Validate all required configuration is present"""
        try:
            _ = self.notion_token
            _ = self.page_id
            _ = self.gemini_api_key
            return True
        except ValueError as e:
            print(f"Configuration Error: {e}")
            return False

    def _error(self, message: str) -> None:
        """Raise error with helpful message"""
        raise ValueError(f"{message}\nPlease check your .env file or environment variables.")


# Singleton instance
config = Config()
