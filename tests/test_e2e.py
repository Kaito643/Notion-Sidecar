import pytest
from unittest.mock import Mock, patch
from src.agent import main
from src.config import config

@pytest.fixture
def mock_clients():
    with patch("src.agent.NotionClient") as mock_notion_cls, \
         patch("src.agent.GeminiAgent") as mock_gemini_cls:
        
        mock_notion = Mock()
        mock_notion_cls.return_value = mock_notion
        
        mock_gemini = Mock()
        mock_gemini_cls.return_value = mock_gemini
        
        yield mock_notion, mock_gemini

def test_e2e_update_flow(mock_clients):
    mock_notion, mock_gemini = mock_clients
    
    # 1. Setup Mock Data
    mock_notion.get_page_blocks.return_value = [
        {"id": "b1", "type": "paragraph", "content": "Original text"}
    ]
    
    mock_gemini.analyze_and_act.return_value = {
        "action": "UPDATE",
        "target_block_index": 0,
        "text": "Updated text",
        "block_type": "paragraph"
    }
    
    mock_notion.update_block.return_value = True

    # 2. Simulate User Input AND patch sys.argv to avoid argparse conflicting with pytest
    with patch("builtins.input", side_effect=["Fix the text", "exit"]), \
         patch("sys.argv", ["notion_sidecar"]), \
         patch.dict("os.environ", {"NOTION_TOKEN": "fake", "PAGE_ID": "fake", "GEMINI_API_KEY": "fake"}):
        
        try:
            main()
        except SystemExit:
            pass
    
    # 3. Verify Interactions
    mock_notion.get_page_blocks.assert_called()
    mock_gemini.analyze_and_act.assert_called()
    mock_notion.update_block.assert_called_with("b1", "Updated text", block_type="paragraph")

def test_e2e_delete_flow(mock_clients):
    mock_notion, mock_gemini = mock_clients
    
    mock_notion.get_page_blocks.return_value = [
        {"id": "b1", "type": "paragraph", "content": "To be deleted"}
    ]
    
    mock_gemini.analyze_and_act.return_value = {
        "action": "DELETE",
        "target_block_index": 0
    }
    
    mock_notion.delete_block.return_value = True

    with patch("builtins.input", side_effect=["Delete it", "exit"]), \
         patch("sys.argv", ["notion_sidecar"]), \
         patch.dict("os.environ", {"NOTION_TOKEN": "fake", "PAGE_ID": "fake", "GEMINI_API_KEY": "fake"}):
        try:
            main()
        except SystemExit:
            pass
    
    mock_notion.delete_block.assert_called_with("b1")

def test_e2e_insert_flow(mock_clients):
    mock_notion, mock_gemini = mock_clients
    
    mock_notion.get_page_blocks.return_value = [
        {"id": "b1", "type": "paragraph", "content": "Anchor block"}
    ]
    
    mock_gemini.analyze_and_act.return_value = {
        "action": "INSERT",
        "target_block_index": 0,
        "text": "New block",
        "block_type": "heading_1"
    }
    
    mock_notion.insert_block_after.return_value = True

    with patch("builtins.input", side_effect=["Insert after this", "exit"]), \
         patch("sys.argv", ["notion_sidecar"]), \
         patch.dict("os.environ", {"NOTION_TOKEN": "fake", "PAGE_ID": "fake", "GEMINI_API_KEY": "fake"}):
        try:
            main()
        except SystemExit:
            pass
    
    mock_notion.insert_block_after.assert_called_with("b1", "New block", block_type="heading_1")
