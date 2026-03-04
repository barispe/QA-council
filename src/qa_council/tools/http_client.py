"""HTTP Client tool — allows agents to make HTTP requests to explore APIs."""

import json

import httpx
from crewai.tools import BaseTool
from pydantic import Field


class HttpClientTool(BaseTool):
    """Makes HTTP requests to explore and test APIs.

    Agents use this tool to discover endpoints, test different HTTP methods,
    probe error responses, and capture response shapes.
    """

    name: str = "http_client"
    description: str = (
        "Makes HTTP requests to an API endpoint. "
        "Use this to explore APIs, test endpoints, and capture responses. "
        "Input should be a JSON string with: "
        "'method' (GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS), "
        "'url' (full URL), "
        "optional 'headers' (dict), "
        "optional 'body' (dict for JSON body), "
        "optional 'params' (dict for query parameters)."
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")

    def _run(self, request_json: str) -> str:
        """Execute an HTTP request and return the response summary.

        Args:
            request_json: JSON string with method, url, headers, body, params.

        Returns:
            Formatted string with status code, headers, and response body.
        """
        try:
            request = json.loads(request_json) if isinstance(request_json, str) else request_json
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON input — {e}"

        method = request.get("method", "GET").upper()
        url = request.get("url", "")
        headers = request.get("headers", None)
        body = request.get("body", None)
        params = request.get("params", None)

        if not url:
            return "Error: 'url' is required in the request."

        try:
            response = httpx.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                params=params,
                timeout=self.timeout,
                follow_redirects=True,
            )

            # Truncate very long responses to save token context
            body_text = response.text
            if len(body_text) > 3000:
                body_text = (
                    body_text[:3000]
                    + f"\n\n... [TRUNCATED — full response is {len(response.text)} chars]"
                )

            # Format response headers (only interesting ones)
            interesting_headers = {
                k: v
                for k, v in response.headers.items()
                if k.lower()
                in (
                    "content-type",
                    "content-length",
                    "x-ratelimit-limit",
                    "x-ratelimit-remaining",
                    "www-authenticate",
                    "location",
                    "retry-after",
                    "allow",
                )
            }

            return (
                f"HTTP {response.status_code} {response.reason_phrase}\n"
                f"URL: {method} {url}\n"
                f"Headers: {json.dumps(interesting_headers, indent=2)}\n"
                f"Body:\n{body_text}"
            )

        except httpx.TimeoutException:
            return f"Error: Request timed out after {self.timeout}s — {method} {url}"
        except httpx.ConnectError as e:
            return f"Error: Connection failed — {method} {url} — {e}"
        except httpx.RequestError as e:
            return f"Error: Request failed — {method} {url} — {e}"
