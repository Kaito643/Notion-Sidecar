from unittest.mock import Mock, patch

import pytest

from src.notion_client import NotionClient


@pytest.fixture
def mock_response():
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {}
    return resp


@pytest.fixture
def client():
    with patch.dict("os.environ", {"NOTION_TOKEN": "fake_token"}):
        return NotionClient()


def test_get_page_blocks_success(client, mock_response):
    # Mock data
    mock_data = {
        "results": [
            {
                "id": "block-1",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"plain_text": "Hello World"}]},
            }
        ],
        "has_more": False,
    }
    mock_response.json.return_value = mock_data

    # Mock session request
    with patch.object(client.session, "request", return_value=mock_response) as mock_req:
        blocks = client.get_page_blocks("page-id")

        assert len(blocks) == 1
        assert blocks[0]["content"] == "Hello World"
        assert blocks[0]["type"] == "paragraph"
        mock_req.assert_called_once()


def test_get_page_blocks_empty(client, mock_response):
    mock_response.json.return_value = {"results": [], "has_more": False}

    with patch.object(client.session, "request", return_value=mock_response):
        blocks = client.get_page_blocks("page-id")
        assert len(blocks) == 0


def test_update_block_success(client, mock_response):
    with patch.object(client.session, "request", return_value=mock_response):
        success = client.update_block("block-1", "New text")
        assert success is True


def test_append_block_success(client, mock_response):
    with patch.object(client.session, "request", return_value=mock_response):
        success = client.append_block("page-id", "New paragraph")
        assert success is True


def test_delete_block_success(client, mock_response):
    with patch.object(client.session, "request", return_value=mock_response) as mock_req:
        success = client.delete_block("block-1")
        assert success is True
        mock_req.assert_called_with(
            "DELETE", f"{client.BASE_URL}/blocks/block-1", params=None, json=None
        )


def test_insert_block_after_success(client, mock_response):
    with patch.dict("os.environ", {"PAGE_ID": "test-page-id"}):
        with patch.object(client.session, "request", return_value=mock_response) as mock_req:
            success = client.insert_block_after("block-1", "Inserted Text")
            assert success is True
            # Check if 'after' param was in payload
            call_args = mock_req.call_args
            assert call_args.kwargs["json"]["after"] == "block-1"


def test_api_rate_limit_retry(client):
    # Mock 429 then 200
    resp_429 = Mock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "0"}

    resp_200 = Mock()
    resp_200.status_code = 200

    with patch.object(client.session, "request", side_effect=[resp_429, resp_200]) as mock_req:
        with patch("time.sleep") as mock_sleep:  # Don't actually wait
            client._make_request("GET", "url")

            assert mock_req.call_count == 2
