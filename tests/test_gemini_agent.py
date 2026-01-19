from typing import Generator
from unittest.mock import Mock, patch

import pytest

from src.gemini_agent import GeminiAgent


@pytest.fixture
def mock_genai_model() -> Generator[Mock, None, None]:
    with patch("src.gemini_agent.genai.GenerativeModel") as mock_model_cls:
        mock_instance = Mock()
        mock_model_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def agent(mock_genai_model: Mock) -> GeminiAgent:
    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake_key", "GEMINI_MODEL": "test-model"}):
        with patch("src.gemini_agent.genai.configure"):
            return GeminiAgent()


def test_analyze_and_act_update(agent: GeminiAgent, mock_genai_model: Mock) -> None:
    # Mock LLM response
    mock_response = Mock()
    mock_response.text = '{"action": "UPDATE", "target_block_index": 0, "text": "New content"}'
    mock_genai_model.generate_content.return_value = mock_response

    blocks = [{"id": "b1", "type": "paragraph", "content": "Old content"}]
    decision = agent.analyze_and_act("Update the first block", blocks)

    assert decision["action"] == "UPDATE"
    assert decision["target_block_index"] == 0
    assert decision["text"] == "New content"


def test_analyze_and_act_json_cleanup(agent: GeminiAgent, mock_genai_model: Mock) -> None:
    # Mock LLM response with markdown blocks
    mock_response = Mock()
    mock_response.text = '```json\n{"action": "CHAT", "text": "Hello"}\n```'
    mock_genai_model.generate_content.return_value = mock_response

    decision = agent.analyze_and_act("Hi", [])

    assert decision["action"] == "CHAT"
    assert decision["text"] == "Hello"


def test_analyze_and_act_error_handling(agent: GeminiAgent, mock_genai_model: Mock) -> None:
    # Mock Error
    mock_genai_model.generate_content.side_effect = Exception("API Error")

    with pytest.raises(Exception, match="API Error"):
        agent.analyze_and_act("Hi", [])


def test_build_context(agent: GeminiAgent) -> None:
    blocks = [
        {"id": "b1", "type": "paragraph", "content": "First para"},
        {"id": "b2", "type": "heading_1", "content": "Title"},
    ]
    context = agent._build_context(blocks)

    assert "[BLOCK_0]" in context
    assert "First para" in context
    assert "[BLOCK_1]" in context
    assert "Title" in context
    assert "heading_1" in context
