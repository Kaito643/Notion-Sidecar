import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration and validation"""
    
    @property
    def NOTION_TOKEN(self) -> str:
        token = os.getenv("NOTION_TOKEN")
        if not token:
            self._error("NOTION_TOKEN environment variable is not set.")
        return token

    @property
    def PAGE_ID(self) -> str:
        page_id = os.getenv("PAGE_ID")
        if not page_id:
            self._error("PAGE_ID environment variable is not set.")
        return page_id

    @property
    def GEMINI_API_KEY(self) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self._error("GEMINI_API_KEY environment variable is not set.")
        return api_key

    @property
    def GEMINI_MODEL(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")

    def validate(self) -> bool:
        """Validate all required configuration is present"""
        try:
            _ = self.NOTION_TOKEN
            _ = self.PAGE_ID
            _ = self.GEMINI_API_KEY
            return True
        except ValueError as e:
            print(f"Configuration Error: {e}")
            return False

    def _error(self, message: str) -> None:
        """Raise error with helpful message"""
        raise ValueError(f"{message}\nPlease check your .env file or environment variables.")

# Singleton instance
config = Config()
