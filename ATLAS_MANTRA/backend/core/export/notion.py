"""
Notion Exporter

Export MANTRA documents to Notion.

Requires:
- Notion API key (api_key) - Internal Integration Token
- Parent page ID (parent_page_id) or Database ID (database_id)
"""

import httpx
import re
from typing import Any, Optional

from .base import BaseExporter, ExportConfig, ExportResult, ExportTarget


class NotionExporter(BaseExporter):
    """Export documents to Notion."""

    NOTION_API_VERSION = "2022-06-28"
    NOTION_API_BASE = "https://api.notion.com/v1"

    def __init__(self):
        super().__init__()
        self.target = ExportTarget.NOTION

    def _get_headers(self, config: ExportConfig) -> dict[str, str]:
        """Get headers for Notion API requests."""
        return {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_API_VERSION,
        }

    def _markdown_to_notion_blocks(self, markdown: str) -> list[dict[str, Any]]:
        """
        Convert Markdown to Notion blocks.

        This handles common markdown elements and converts them to Notion's block format.
        """
        blocks: list[dict[str, Any]] = []
        lines = markdown.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Headers
            if line.startswith('# '):
                blocks.append({
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]
                    }
                })
            elif line.startswith('## '):
                blocks.append({
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:].strip()}}]
                    }
                })
            elif line.startswith('### '):
                blocks.append({
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:].strip()}}]
                    }
                })

            # Code blocks
            elif line.startswith('```'):
                language = line[3:].strip() or "plain text"
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                code_content = '\n'.join(code_lines)

                blocks.append({
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": code_content}}],
                        "language": language.lower() if language else "plain text"
                    }
                })

            # Bullet lists
            elif line.startswith('- ') or line.startswith('* '):
                text = line[2:].strip()
                blocks.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": self._parse_inline_formatting(text)
                    }
                })

            # Numbered lists
            elif re.match(r'^\d+\. ', line):
                text = re.sub(r'^\d+\. ', '', line).strip()
                blocks.append({
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": self._parse_inline_formatting(text)
                    }
                })

            # Blockquotes
            elif line.startswith('> '):
                text = line[2:].strip()
                blocks.append({
                    "type": "quote",
                    "quote": {
                        "rich_text": self._parse_inline_formatting(text)
                    }
                })

            # Horizontal rule
            elif line.strip() in ('---', '***', '___'):
                blocks.append({"type": "divider", "divider": {}})

            # Regular paragraphs
            else:
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": self._parse_inline_formatting(line.strip())
                    }
                })

            i += 1

        return blocks

    def _parse_inline_formatting(self, text: str) -> list[dict[str, Any]]:
        """Parse inline formatting (bold, italic, code, links)."""
        rich_text: list[dict[str, Any]] = []

        # Simple approach: handle common patterns
        # For production, use a proper parser

        # Handle links [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'

        parts = re.split(link_pattern, text)

        i = 0
        while i < len(parts):
            if i + 2 < len(parts) and i % 3 == 0:
                # Before link
                if parts[i]:
                    rich_text.extend(self._parse_text_styles(parts[i]))
                # Link text
                if parts[i + 1]:
                    rich_text.append({
                        "type": "text",
                        "text": {
                            "content": parts[i + 1],
                            "link": {"url": parts[i + 2]}
                        }
                    })
                i += 3
            else:
                if parts[i]:
                    rich_text.extend(self._parse_text_styles(parts[i]))
                i += 1

        if not rich_text:
            rich_text.append({"type": "text", "text": {"content": text}})

        return rich_text

    def _parse_text_styles(self, text: str) -> list[dict[str, Any]]:
        """Parse bold, italic, and code styling."""
        result: list[dict[str, Any]] = []

        # Handle bold **text**
        bold_pattern = r'\*\*([^*]+)\*\*'
        # Handle italic *text*
        italic_pattern = r'\*([^*]+)\*'
        # Handle inline code `text`
        code_pattern = r'`([^`]+)`'

        # Simple sequential parsing
        remaining = text
        while remaining:
            # Check for bold
            bold_match = re.search(bold_pattern, remaining)
            # Check for code
            code_match = re.search(code_pattern, remaining)
            # Check for italic
            italic_match = re.search(italic_pattern, remaining)

            # Find earliest match
            matches = [
                (bold_match, "bold"),
                (code_match, "code"),
                (italic_match, "italic"),
            ]
            matches = [(m, t) for m, t in matches if m is not None]

            if not matches:
                # No more formatting
                if remaining:
                    result.append({"type": "text", "text": {"content": remaining}})
                break

            # Get earliest match
            earliest = min(matches, key=lambda x: x[0].start())  # type: ignore
            match, match_type = earliest

            # Add text before match
            if match.start() > 0:  # type: ignore
                result.append({
                    "type": "text",
                    "text": {"content": remaining[:match.start()]}  # type: ignore
                })

            # Add formatted text
            content = match.group(1)  # type: ignore
            annotations = {"bold": False, "italic": False, "code": False}
            if match_type == "bold":
                annotations["bold"] = True
            elif match_type == "italic":
                annotations["italic"] = True
            elif match_type == "code":
                annotations["code"] = True

            result.append({
                "type": "text",
                "text": {"content": content},
                "annotations": annotations,
            })

            remaining = remaining[match.end():]  # type: ignore

        return result if result else [{"type": "text", "text": {"content": text}}]

    async def validate_config(self, config: ExportConfig) -> tuple[bool, Optional[str]]:
        """Validate Notion configuration."""
        if not config.api_key:
            return False, "Notion API key is required"

        if not config.parent_page_id and not config.database_id:
            return False, "Either parent_page_id or database_id is required"

        # Test connection
        try:
            headers = self._get_headers(config)

            async with httpx.AsyncClient() as client:
                # Test by getting user info
                response = await client.get(
                    f"{self.NOTION_API_BASE}/users/me",
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 401:
                    return False, "Invalid API key"
                elif response.status_code != 200:
                    return False, f"Connection failed: {response.status_code}"

                return True, None

        except httpx.ConnectError:
            return False, "Failed to connect to Notion API"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def export_document(
        self,
        content: str,
        title: str,
        config: ExportConfig,
    ) -> ExportResult:
        """Export document to Notion as a new page."""
        is_valid, error = await self.validate_config(config)
        if not is_valid:
            return self._create_error_result(self.target, error or "Invalid configuration")

        try:
            headers = self._get_headers(config)

            # Convert markdown to Notion blocks
            blocks = self._markdown_to_notion_blocks(content)

            # Build request body
            body: dict[str, Any] = {
                "properties": {
                    "title": {
                        "title": [{"type": "text", "text": {"content": title}}]
                    }
                },
                "children": blocks[:100],  # Notion limits to 100 blocks per request
            }

            # Set parent
            if config.database_id:
                body["parent"] = {"database_id": config.database_id}
            else:
                body["parent"] = {"page_id": config.parent_page_id}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.NOTION_API_BASE}/pages",
                    headers=headers,
                    json=body,
                    timeout=30.0,
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    page_id = data.get("id")
                    page_url = data.get("url")

                    # If we have more than 100 blocks, append them
                    if len(blocks) > 100:
                        await self._append_blocks(page_id, blocks[100:], headers)

                    return ExportResult(
                        success=True,
                        target=self.target,
                        url=page_url,
                        page_id=page_id,
                    )
                else:
                    error_data = response.json()
                    error_msg = error_data.get("message", response.text)
                    return self._create_error_result(self.target, f"Export failed: {error_msg}")

        except Exception as e:
            return self._create_error_result(self.target, f"Export error: {str(e)}")

    async def _append_blocks(
        self,
        page_id: str,
        blocks: list[dict[str, Any]],
        headers: dict[str, str],
    ) -> None:
        """Append additional blocks to a page."""
        async with httpx.AsyncClient() as client:
            # Append in chunks of 100
            for i in range(0, len(blocks), 100):
                chunk = blocks[i:i + 100]
                await client.patch(
                    f"{self.NOTION_API_BASE}/blocks/{page_id}/children",
                    headers=headers,
                    json={"children": chunk},
                    timeout=30.0,
                )

    async def update_document(
        self,
        page_id: str,
        content: str,
        title: str,
        config: ExportConfig,
    ) -> ExportResult:
        """Update an existing Notion page."""
        try:
            headers = self._get_headers(config)

            async with httpx.AsyncClient() as client:
                # Update title
                title_response = await client.patch(
                    f"{self.NOTION_API_BASE}/pages/{page_id}",
                    headers=headers,
                    json={
                        "properties": {
                            "title": {
                                "title": [{"type": "text", "text": {"content": title}}]
                            }
                        }
                    },
                    timeout=10.0,
                )

                if title_response.status_code != 200:
                    return self._create_error_result(
                        self.target,
                        f"Failed to update title: {title_response.status_code}"
                    )

                # Get existing blocks to delete
                blocks_response = await client.get(
                    f"{self.NOTION_API_BASE}/blocks/{page_id}/children",
                    headers=headers,
                    timeout=10.0,
                )

                if blocks_response.status_code == 200:
                    existing_blocks = blocks_response.json().get("results", [])
                    # Delete existing blocks
                    for block in existing_blocks:
                        await client.delete(
                            f"{self.NOTION_API_BASE}/blocks/{block['id']}",
                            headers=headers,
                            timeout=10.0,
                        )

                # Add new blocks
                new_blocks = self._markdown_to_notion_blocks(content)
                await self._append_blocks(page_id, new_blocks, headers)

                # Get updated page info
                page_response = await client.get(
                    f"{self.NOTION_API_BASE}/pages/{page_id}",
                    headers=headers,
                    timeout=10.0,
                )

                if page_response.status_code == 200:
                    data = page_response.json()
                    return ExportResult(
                        success=True,
                        target=self.target,
                        url=data.get("url"),
                        page_id=page_id,
                    )

                return ExportResult(
                    success=True,
                    target=self.target,
                    page_id=page_id,
                )

        except Exception as e:
            return self._create_error_result(self.target, f"Update error: {str(e)}")

    async def delete_document(
        self,
        page_id: str,
        config: ExportConfig,
    ) -> ExportResult:
        """Archive a Notion page (Notion doesn't truly delete)."""
        try:
            headers = self._get_headers(config)

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.NOTION_API_BASE}/pages/{page_id}",
                    headers=headers,
                    json={"archived": True},
                    timeout=10.0,
                )

                if response.status_code == 200:
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
        """List child pages of a Notion page or database."""
        try:
            headers = self._get_headers(config)
            target_id = parent_id or config.parent_page_id or config.database_id

            if not target_id:
                return []

            async with httpx.AsyncClient() as client:
                # If it's a database, query it
                if config.database_id and not parent_id:
                    response = await client.post(
                        f"{self.NOTION_API_BASE}/databases/{target_id}/query",
                        headers=headers,
                        json={},
                        timeout=10.0,
                    )
                else:
                    # Get children of a page
                    response = await client.get(
                        f"{self.NOTION_API_BASE}/blocks/{target_id}/children",
                        headers=headers,
                        timeout=10.0,
                    )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])

                    pages = []
                    for item in results:
                        if item.get("type") == "child_page" or item.get("object") == "page":
                            title = ""
                            if "child_page" in item:
                                title = item["child_page"].get("title", "")
                            elif "properties" in item:
                                title_prop = item["properties"].get("title", {})
                                if "title" in title_prop and title_prop["title"]:
                                    title = title_prop["title"][0].get("plain_text", "")

                            pages.append({
                                "id": item.get("id"),
                                "title": title,
                                "url": item.get("url"),
                            })

                    return pages

                return []

        except Exception:
            return []
