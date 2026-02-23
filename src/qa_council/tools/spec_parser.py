"""OpenAPI Spec Parser tool — parses Swagger/OpenAPI JSON specs."""

import json

import httpx
from crewai.tools import BaseTool
from pydantic import Field


class SpecParserTool(BaseTool):
    """Fetches and parses OpenAPI/Swagger specifications.

    Used by the Scout to quickly understand an API's full surface
    from its specification file.
    """

    name: str = "spec_parser"
    description: str = (
        "Fetches and parses an OpenAPI/Swagger specification. "
        "Input should be a JSON string with: "
        "'url' (URL to the spec JSON file, e.g. 'https://petstore.swagger.io/v2/swagger.json'). "
        "Returns a summary of all endpoints, methods, and schemas."
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")

    def _run(self, request_json: str) -> str:
        """Fetch and parse an OpenAPI spec.

        Args:
            request_json: JSON with 'url' to the spec file.

        Returns:
            Parsed summary of endpoints, methods, and schemas.
        """
        try:
            request = json.loads(request_json) if isinstance(request_json, str) else request_json
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON input — {e}"

        url = request.get("url", "")
        if not url:
            return "Error: 'url' is required."

        try:
            response = httpx.get(url, timeout=self.timeout, follow_redirects=True)
            if response.status_code != 200:
                return f"Error: Got HTTP {response.status_code} fetching spec from {url}"

            spec = response.json()
        except httpx.RequestError as e:
            return f"Error fetching spec: {e}"
        except json.JSONDecodeError:
            return f"Error: Response from {url} is not valid JSON"

        return self._format_spec(spec)

    def _format_spec(self, spec: dict) -> str:
        """Format an OpenAPI spec into a readable summary."""
        lines = []

        # Header
        info = spec.get("info", {})
        lines.append(f"# API Specification: {info.get('title', 'Unknown')}")
        lines.append(f"**Version**: {info.get('version', 'unknown')}")
        if info.get("description"):
            lines.append(f"**Description**: {info['description'][:200]}")
        lines.append("")

        # Base URL
        if "host" in spec:
            scheme = (spec.get("schemes") or ["https"])[0]
            base_path = spec.get("basePath", "")
            lines.append(f"**Base URL**: {scheme}://{spec['host']}{base_path}")
        elif "servers" in spec:
            for server in spec["servers"][:3]:
                lines.append(f"**Server**: {server.get('url', 'N/A')}")
        lines.append("")

        # Endpoints
        paths = spec.get("paths", {})
        lines.append(f"## Endpoints ({len(paths)} paths)")
        lines.append("")

        for path, methods in sorted(paths.items()):
            for method, details in methods.items():
                if method.lower() in ("get", "post", "put", "patch", "delete", "head", "options"):
                    summary = details.get("summary", details.get("operationId", ""))
                    tags = ", ".join(details.get("tags", []))
                    params = details.get("parameters", [])
                    param_names = [p.get("name", "?") for p in params[:5]]

                    lines.append(f"### {method.upper()} {path}")
                    if summary:
                        lines.append(f"  Summary: {summary}")
                    if tags:
                        lines.append(f"  Tags: {tags}")
                    if param_names:
                        lines.append(f"  Parameters: {', '.join(param_names)}")

                    # Response codes
                    responses = details.get("responses", {})
                    codes = list(responses.keys())[:5]
                    if codes:
                        lines.append(f"  Responses: {', '.join(str(c) for c in codes)}")
                    lines.append("")

        # Schemas/Definitions
        definitions = spec.get("definitions", spec.get("components", {}).get("schemas", {}))
        if definitions:
            lines.append(f"## Schemas ({len(definitions)} definitions)")
            lines.append("")
            for name, schema in sorted(definitions.items()):
                props = schema.get("properties", {})
                required = schema.get("required", [])
                prop_list = []
                for prop_name, prop_info in list(props.items())[:10]:
                    prop_type = prop_info.get("type", prop_info.get("$ref", "object"))
                    req_mark = " (required)" if prop_name in required else ""
                    prop_list.append(f"{prop_name}: {prop_type}{req_mark}")
                lines.append(f"### {name}")
                for p in prop_list:
                    lines.append(f"  - {p}")
                lines.append("")

        result = "\n".join(lines)
        # Truncate if extremely long
        if len(result) > 6000:
            result = result[:6000] + f"\n\n... [TRUNCATED — full spec has {len(paths)} endpoints]"
        return result
