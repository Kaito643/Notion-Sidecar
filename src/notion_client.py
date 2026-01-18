import time
from typing import Any, Dict, List, Optional

import requests

from src.config import config
from src.utils import setup_logger

logger = setup_logger("NotionClient", config.LOG_LEVEL)


class NotionClient:
    """
    A client wrapper for the Notion API handling block operations
    with retry logic and error handling.
    """

    BASE_URL = "https://api.notion.com/v1"

    def __init__(self) -> None:
        self.headers = {
            "Authorization": f"Bearer {config.NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all supported blocks from a notion page.
        Handles pagination automatically.
        """
        blocks = []
        url = f"{self.BASE_URL}/blocks/{page_id}/children"
        has_more = True
        start_cursor = None

        try:
            while has_more:
                params = {"page_size": 100}
                if start_cursor:
                    params["start_cursor"] = start_cursor

                response = self._make_request("GET", url, params=params)
                if not response:
                    break

                data = response.json()
                results = data.get("results", [])

                for item in results:
                    block_data = self._parse_block(item)
                    if block_data:
                        blocks.append(block_data)

                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")

            return blocks

        except Exception as e:
            logger.error(f"Failed to fetch blocks: {e}")
            return []

    def update_block(self, block_id: str, new_text: str, block_type: str = "paragraph") -> bool:
        """
        Update a specific block's text content.
        Preserves the block type if possible.
        """
        url = f"{self.BASE_URL}/blocks/{block_id}"

        # Construct payload based on block type
        # Notion API structure requires nested object with type name
        payload = {block_type: {"rich_text": [{"type": "text", "text": {"content": new_text}}]}}

        response = self._make_request("PATCH", url, json_data=payload)
        return response is not None and response.status_code == 200

    def append_block(self, parent_id: str, text: str, block_type: str = "paragraph") -> bool:
        """
        Append a new block to the end of a page (or block).
        """
        url = f"{self.BASE_URL}/blocks/{parent_id}/children"

        payload = {
            "children": [
                {
                    "object": "block",
                    "type": block_type,
                    block_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
                }
            ]
        }

        response = self._make_request("PATCH", url, json_data=payload)
        return response is not None and response.status_code == 200

    def delete_block(self, block_id: str) -> bool:
        """
        Delete (archive) a block.
        """
        url = f"{self.BASE_URL}/blocks/{block_id}"
        response = self._make_request("DELETE", url)
        return response is not None and response.status_code == 200

    def insert_block_after(self, block_id: str, text: str, block_type: str = "paragraph") -> bool:
        """
        Insert a block after a specific block_id.
        Notion API 'append' on a block appends to its children (if it can have children).
        To insert *after*, we typically append to the parent.
        However, the Notion API `blocks/{id}/children` endpoint appends to the *bottom* of the children list.
        It has an `after` parameter in the append endpoint now? No, the documentation says "Append block children".

        Wait, Notion API supports `after` in the Append block children payload since version 2022-06-28?
        Actually, looking at the docs, `Append block children` adds to the end.
        To insert in the middle, we have to use `after` parameter in the `children` array?
        No, Notion API is a bit restrictive here.
        Actually, the `Append block children` endpoint appends content to the `block_id`.
        If we want to insert AFTER a block at the same level, we need the parent ID.
        But since we are flattening the list in `get_page_blocks`, we might lose track of the parent structure slightly if nested.
        However, for the main list, the parent is the Page ID.
        The Notion API documentation says: "There is currently no way to insert a block at a specific order among other blocks."
        Wait, `Append block children` now supports `after`?
        Let me double check.
        Ah, the `Append block children` endpoint sends a body with `children`.
        There is NO standard way to insert *between* blocks easily via the API without rewriting the page or using the `after` parameter if it exists.
        Wait, recent API versions added `after`.
        Let's check if the current version `2022-06-28` supports it.
        Actually, it seems `after` is supported in `Append block children`.
        "The `after` parameter... the ID of the existing block that the new block should be appended after".
        Let's assume this exists for `Append block children`.
        Wait, the official docs say: "https://developers.notion.com/reference/patch-block-children"
        Body params: `children`, `after` (optional).
        Yes! "The ID of the existing block that the new block should be appended after."

        So we need the Parent ID. But `get_page_blocks` is getting children of the PAGE.
        So to insert after Block A (which is a child of Page P), we call `append_block(Page P, children=[...], after=Block A)`.

        So `insert_block_after` needs the `parent_id` (the page id) and the `after_block_id`.
        But `analyze_and_act` only knows about the list of blocks.
        We can pass `config.PAGE_ID` as the parent for now, assuming a flat structure for the blog post.
        """
        # For simplicity, we assume we are inserting into the main Page ID list
        # If we support nested blocks later, we'd need to track parent IDs in the block analysis.
        url = f"{self.BASE_URL}/blocks/{config.PAGE_ID}/children"

        payload = {
            "children": [
                {
                    "object": "block",
                    "type": block_type,
                    block_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
                }
            ],
            "after": block_id,
        }

        response = self._make_request("PATCH", url, json_data=payload)
        return response is not None and response.status_code == 200

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        retries: int = 3,
    ) -> Optional[requests.Response]:
        """
        Internal method to handle requests with rate limiting and retries.
        """
        for attempt in range(retries):
            try:
                response = self.session.request(method, url, params=params, json=json_data)

                if response.status_code == 429:
                    # Rate limited
                    wait_time = int(response.headers.get("Retry-After", 1)) + 1
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                if response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}. Retrying...")
                    time.sleep(1 * (attempt + 1))
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                logger.error(f"API Request failed (Attempt {attempt+1}/{retries}): {e}")
                if attempt == retries - 1:
                    return None
                time.sleep(1 * (attempt + 1))  # Exponential backoff

        return None

    def _parse_block(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract relevant data from raw block response.
        """
        b_type = item.get("type")
        supported_types = [
            "paragraph",
            "heading_1",
            "heading_2",
            "heading_3",
            "bulleted_list_item",
            "numbered_list_item",
            "quote",
            "callout",
            "code",
            "to_do",
        ]

        if b_type not in supported_types:
            return {"id": item["id"], "type": "unsupported", "content": f"[{b_type} block]"}

        try:
            rich_text = item.get(b_type, {}).get("rich_text", [])
            content = ""
            if rich_text:
                # Combine all text chunks
                content = "".join([t.get("plain_text", "") for t in rich_text])

            return {"id": item["id"], "type": b_type, "content": content}
        except Exception:
            return {"id": item["id"], "type": "error", "content": "[Error parsing block]"}
