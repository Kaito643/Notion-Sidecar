import json
from typing import Any, Dict, List

import google.generativeai as genai

from src.config import config
from src.utils import setup_logger

logger = setup_logger("GeminiAgent", config.LOG_LEVEL)


class GeminiAgent:
    """
    AI Agent that analyzes user intents and Notion page content
    to decide on editing actions.
    """

    def __init__(self) -> None:
        self._configure_genai()
        self.model_name = config.GEMINI_MODEL
        self.model = genai.GenerativeModel(self.model_name)

    def _configure_genai(self) -> None:
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            raise

    def analyze_and_act(
        self, user_query: str, current_blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Main reasoning loop:
        1. Contextualize blocks
        2. Construct prompt
        3. Get JSON decision from Gemini
        4. Parse and return action plan
        """
        context_str = self._build_context(current_blocks)
        prompt = self._build_system_prompt(user_query, context_str)

        try:
            response = self.model.generate_content(prompt)
            decision = self._parse_json_response(response.text)
            return decision
        except Exception as e:
            logger.error(f"Gemini reasoning failed: {e}")

            # Additional debug info for model not found errors
            if "404" in str(e) and "not found" in str(e):
                logger.info("Attempting to list available models...")
                try:
                    for m in genai.list_models():
                        if "generateContent" in m.supported_generation_methods:
                            logger.info(f"Available model: {m.name}")
                except Exception as list_err:
                    logger.error(f"Could not list models: {list_err}")

            return {
                "action": "CHAT",
                "text": f"I encountered an error with the AI model ({self.model_name}). Please check the logs for available models.",
            }

    def _build_context(self, blocks: List[Dict[str, Any]]) -> str:
        """Create a numbered string representation of the page content"""
        context = []
        for idx, block in enumerate(blocks):
            # Include type to help agent decide if it should preserve or change it
            context.append(
                f"[BLOCK_{idx}] (ID: {block['id']}, Type: {block['type']})\nContent: {block['content']}"
            )
        return "\n\n".join(context)

    def _build_system_prompt(self, query: str, context: str) -> str:
        return f"""
        You are an intelligent Notion Blog Editor Agent. 
        Your goal is to help the user edit, write, or refine their blog post based on their natural language commands.
        
        CURRENT PAGE CONTENT (Indexed Blocks):
        ----------------------------------------
        {context}
        ----------------------------------------
        
        USER COMMAND: "{query}"
        
        INSTRUCTIONS:
        1. Analyze the user's command and the current content.
        2. Decide on ONE of the following actions:
           - 'UPDATE': Modify an existing block's content.
           - 'APPEND': Add a new block to the end of the page.
           - 'DELETE': Remove a specific block.
           - 'INSERT': Insert a new block AFTER a specific block.
           - 'CHAT': Reply to the user if no editing is needed (e.g. they asked a question).
           
        3. IMPORTANT: working with block indexes (0, 1, 2...) from the context above.
        
        4. LANGUAGE:
        - The user may write in any language, but unless explicitly asked otherwise, generate content and CHAT responses in English.
        
        5. OUTPUT FORMAT:
        Return ONLY valid JSON. Do not include markdown formatting like ```json.
        
        {{
            "action": "UPDATE" | "APPEND" | "DELETE" | "INSERT" | "CHAT",
            "target_block_index": <int> (Required for UPDATE, DELETE, INSERT),
            "text": "<new_content_or_chat_reply>",
            "block_type": "<paragraph|heading_1|heading_2|heading_3|bulleted_list_item|code|to_do|quote|callout>" (Optional, matches target or new type)
        }}
        """

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Clean and parse JSON from LLM response"""
        try:
            # Strip potential markdown code blocks
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from Gemini")
            return {
                "action": "CHAT",
                "text": "I understood your request but failed to generate a structured action. Could you try rephrasing?",
            }
