"""Unit tests for the HttpClientTool."""

import json
import pytest
from unittest.mock import patch, MagicMock

from qa_council.tools.http_client import HttpClientTool


@pytest.fixture
def http_tool():
    """Create an HttpClientTool instance."""
    return HttpClientTool()


class TestHttpClientTool:
    """Tests for HttpClientTool._run()."""

    def test_basic_get_request(self, http_tool):
        """Should make a GET request and return formatted response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.text = '{"status": "available"}'
        mock_response.headers = {"content-type": "application/json"}

        with patch("qa_council.tools.http_client.httpx.request", return_value=mock_response):
            result = http_tool._run('{"method": "GET", "url": "https://api.example.com/health"}')

        assert "HTTP 200 OK" in result
        assert "available" in result

    def test_post_request_with_body(self, http_tool):
        """Should send JSON body with POST requests."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.reason_phrase = "Created"
        mock_response.text = '{"id": 1}'
        mock_response.headers = {"content-type": "application/json"}

        with patch(
            "qa_council.tools.http_client.httpx.request", return_value=mock_response
        ) as mock_req:
            result = http_tool._run(
                json.dumps(
                    {
                        "method": "POST",
                        "url": "https://api.example.com/pets",
                        "body": {"name": "Rex", "status": "available"},
                    }
                )
            )

        mock_req.assert_called_once()
        call_kwargs = mock_req.call_args
        assert call_kwargs.kwargs["method"] == "POST"
        assert call_kwargs.kwargs["json"] == {"name": "Rex", "status": "available"}
        assert "HTTP 201 Created" in result

    def test_handles_timeout(self, http_tool):
        """Should return a clear error on timeout."""
        import httpx

        with patch(
            "qa_council.tools.http_client.httpx.request",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            result = http_tool._run('{"method": "GET", "url": "https://api.example.com/slow"}')

        assert "Error" in result
        assert "timed out" in result

    def test_handles_connection_error(self, http_tool):
        """Should return a clear error on connection failure."""
        import httpx

        with patch(
            "qa_council.tools.http_client.httpx.request", side_effect=httpx.ConnectError("refused")
        ):
            result = http_tool._run('{"method": "GET", "url": "https://invalid.example.com"}')

        assert "Error" in result
        assert "Connection failed" in result

    def test_handles_invalid_json_input(self, http_tool):
        """Should return error for malformed JSON input."""
        result = http_tool._run("not valid json {{{")
        assert "Error" in result
        assert "Invalid JSON" in result

    def test_handles_missing_url(self, http_tool):
        """Should return error when URL is missing."""
        result = http_tool._run('{"method": "GET"}')
        assert "Error" in result
        assert "url" in result.lower()

    def test_truncates_long_responses(self, http_tool):
        """Should truncate responses longer than 3000 chars."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.text = "x" * 5000
        mock_response.headers = {"content-type": "text/plain"}

        with patch("qa_council.tools.http_client.httpx.request", return_value=mock_response):
            result = http_tool._run('{"method": "GET", "url": "https://api.example.com/big"}')

        assert "TRUNCATED" in result
        assert "5000" in result

    def test_filters_interesting_headers(self, http_tool):
        """Should only include relevant headers in the output."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.text = "{}"
        mock_response.headers = {
            "content-type": "application/json",
            "x-ratelimit-limit": "100",
            "x-request-id": "abc-123",  # should be filtered out
            "server": "nginx",  # should be filtered out
        }

        with patch("qa_council.tools.http_client.httpx.request", return_value=mock_response):
            result = http_tool._run('{"method": "GET", "url": "https://api.example.com"}')

        assert "content-type" in result
        assert "x-ratelimit-limit" in result
        assert "x-request-id" not in result
        assert "nginx" not in result

    def test_defaults_to_get_method(self, http_tool):
        """Should default to GET when method is not provided."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.text = "{}"
        mock_response.headers = {}

        with patch(
            "qa_council.tools.http_client.httpx.request", return_value=mock_response
        ) as mock_req:
            http_tool._run('{"url": "https://api.example.com"}')

        assert mock_req.call_args.kwargs["method"] == "GET"

    def test_sends_query_params(self, http_tool):
        """Should pass query parameters when provided."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.text = "[]"
        mock_response.headers = {}

        with patch(
            "qa_council.tools.http_client.httpx.request", return_value=mock_response
        ) as mock_req:
            http_tool._run(
                json.dumps(
                    {
                        "method": "GET",
                        "url": "https://api.example.com/search",
                        "params": {"q": "test", "limit": 10},
                    }
                )
            )

        assert mock_req.call_args.kwargs["params"] == {"q": "test", "limit": 10}
