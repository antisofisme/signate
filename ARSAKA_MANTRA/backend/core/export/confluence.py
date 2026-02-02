"""
Confluence Exporter

Export MANTRA documents to Atlassian Confluence.

Requires:
- Confluence Cloud API token (api_token)
- Confluence base URL in extra['base_url']
- User email in extra['email']
- Space key (space_key)
"""

import httpx
import base64
import re
from typing import Any, Optional

from .base import BaseExporter, ExportConfig, ExportResult, ExportTarget


class ConfluenceExporter(BaseExporter):
    """Export documents to Atlassian Confluence."""

    def __init__(self):
        super().__init__()
        self.target = ExportTarget.CONFLUENCE

    def _get_auth_header(self, config: ExportConfig) -> dict[str, str]:
        """Get authentication header for Confluence API."""
        email = config.extra.get("email", "")
        token = config.api_token or ""
        credentials = f"{email}:{token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    def _get_base_url(self, config: ExportConfig) -> str:
        """Get Confluence base URL."""
        base_url = config.extra.get("base_url", "")
        return base_url.rstrip("/")

    def _markdown_to_confluence_storage(self, markdown: str) -> str:
        """
        Convert Markdown to Confluence Storage Format (XHTML).

        This is a basic conversion - for production, consider using
        a proper markdown-to-confluence library.
        """
        content = markdown

        # Headers
        content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', content, flags=re.MULTILINE)

        # Bold and italic
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)

        # Code blocks
        content = re.sub(
            r'```(\w+)?\n([\s\S]*?)```',
            r'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">\1</ac:parameter><ac:plain-text-body><![CDATA[\2]]></ac:plain-text-body></ac:structured-macro>',
            content
        )

        # Inline code
        content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)

        # Links
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', content)

        # Lists
        content = re.sub(r'^- (.+)$', r'<li>\1</li>', content, flags=re.MULTILINE)
        content = re.sub(r'(<li>.*</li>\n)+', r'<ul>\g<0></ul>', content)

        # Paragraphs (simple - wrap non-tag lines)
        lines = content.split('\n')
        result = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('<'):
                result.append(f'<p>{stripped}</p>')
            else:
                result.append(line)

        return '\n'.join(result)

    async def validate_config(self, config: ExportConfig) -> tuple[bool, Optional[str]]:
        """Validate Confluence configuration."""
        if not config.api_token:
            return False, "API token is required"

        if not config.extra.get("email"):
            return False, "Email is required for authentication"

        if not config.extra.get("base_url"):
            return False, "Confluence base URL is required"

        if not config.space_key:
            return False, "Space key is required"

        # Test connection
        try:
            base_url = self._get_base_url(config)
            headers = self._get_auth_header(config)
            headers["Content-Type"] = "application/json"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/wiki/rest/api/space/{config.space_key}",
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 401:
                    return False, "Authentication failed - check email and API token"
                elif response.status_code == 404:
                    return False, f"Space '{config.space_key}' not found"
                elif response.status_code != 200:
                    return False, f"Failed to connect: {response.status_code}"

                return True, None

        except httpx.ConnectError:
            return False, "Failed to connect to Confluence"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def export_document(
        self,
        content: str,
        title: str,
        config: ExportConfig,
    ) -> ExportResult:
        """Export document to Confluence."""
        is_valid, error = await self.validate_config(config)
        if not is_valid:
            return self._create_error_result(self.target, error or "Invalid configuration")

        try:
            base_url = self._get_base_url(config)
            headers = self._get_auth_header(config)
            headers["Content-Type"] = "application/json"

            # Convert markdown to Confluence storage format
            storage_content = self._markdown_to_confluence_storage(content)

            # Build request body
            body: dict[str, Any] = {
                "type": "page",
                "title": title,
                "space": {"key": config.space_key},
                "body": {
                    "storage": {
                        "value": storage_content,
                        "representation": "storage"
                    }
                }
            }

            # Add parent page if specified
            if config.parent_page_id:
                body["ancestors"] = [{"id": config.parent_page_id}]

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/wiki/rest/api/content",
                    headers=headers,
                    json=body,
                    timeout=30.0,
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    page_id = data.get("id")
                    page_url = f"{base_url}/wiki{data.get('_links', {}).get('webui', '')}"

                    return ExportResult(
                        success=True,
                        target=self.target,
                        url=page_url,
                        page_id=page_id,
                        metadata={"version": data.get("version", {}).get("number", 1)},
                    )
                else:
                    error_msg = response.json().get("message", response.text)
                    return self._create_error_result(self.target, f"Export failed: {error_msg}")

        except Exception as e:
            return self._create_error_result(self.target, f"Export error: {str(e)}")

    async def update_document(
        self,
        page_id: str,
        content: str,
        title: str,
        config: ExportConfig,
    ) -> ExportResult:
        """Update an existing Confluence page."""
        try:
            base_url = self._get_base_url(config)
            headers = self._get_auth_header(config)
            headers["Content-Type"] = "application/json"

            # Get current version
            async with httpx.AsyncClient() as client:
                get_response = await client.get(
                    f"{base_url}/wiki/rest/api/content/{page_id}",
                    headers=headers,
                    timeout=10.0,
                )

                if get_response.status_code != 200:
                    return self._create_error_result(self.target, f"Page not found: {page_id}")

                current = get_response.json()
                current_version = current.get("version", {}).get("number", 1)

                # Convert and update
                storage_content = self._markdown_to_confluence_storage(content)

                body = {
                    "type": "page",
                    "title": title,
                    "body": {
                        "storage": {
                            "value": storage_content,
                            "representation": "storage"
                        }
                    },
                    "version": {"number": current_version + 1}
                }

                response = await client.put(
                    f"{base_url}/wiki/rest/api/content/{page_id}",
                    headers=headers,
                    json=body,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    page_url = f"{base_url}/wiki{data.get('_links', {}).get('webui', '')}"

                    return ExportResult(
                        success=True,
                        target=self.target,
                        url=page_url,
                        page_id=page_id,
                        metadata={"version": current_version + 1},
                    )
                else:
                    error_msg = response.json().get("message", response.text)
                    return self._create_error_result(self.target, f"Update failed: {error_msg}")

        except Exception as e:
            return self._create_error_result(self.target, f"Update error: {str(e)}")

    async def delete_document(
        self,
        page_id: str,
        config: ExportConfig,
    ) -> ExportResult:
        """Delete a Confluence page."""
        try:
            base_url = self._get_base_url(config)
            headers = self._get_auth_header(config)

            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{base_url}/wiki/rest/api/content/{page_id}",
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code in (200, 204):
                    return ExportResult(
                        success=True,
                        target=self.target,
                        page_id=page_id,
                    )
                else:
                    return self._create_error_result(
                        self.target,
                        f"Delete failed: {response.status_code}"
                    )

        except Exception as e:
            return self._create_error_result(self.target, f"Delete error: {str(e)}")

    async def list_pages(
        self,
        config: ExportConfig,
        parent_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List pages in the Confluence space."""
        try:
            base_url = self._get_base_url(config)
            headers = self._get_auth_header(config)

            params = {
                "spaceKey": config.space_key,
                "expand": "version",
                "limit": 50,
            }

            if parent_id:
                params["ancestorId"] = parent_id

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/wiki/rest/api/content",
                    headers=headers,
                    params=params,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "id": page.get("id"),
                            "title": page.get("title"),
                            "version": page.get("version", {}).get("number"),
                            "url": f"{base_url}/wiki{page.get('_links', {}).get('webui', '')}",
                        }
                        for page in data.get("results", [])
                    ]
                else:
                    return []

        except Exception:
            return []
