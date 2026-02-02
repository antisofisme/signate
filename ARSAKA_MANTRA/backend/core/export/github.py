"""
GitHub Wiki Exporter

Export MANTRA documents to GitHub Wiki.

GitHub Wiki uses a git repository behind the scenes. This exporter uses the
GitHub API to manage wiki pages.

Requires:
- GitHub personal access token (api_token) with repo scope
- Repository owner (repo_owner)
- Repository name (repo_name)
"""

import httpx
import re
from typing import Any, Optional

from .base import BaseExporter, ExportConfig, ExportResult, ExportTarget


class GitHubWikiExporter(BaseExporter):
    """Export documents to GitHub Wiki."""

    GITHUB_API_BASE = "https://api.github.com"

    def __init__(self):
        super().__init__()
        self.target = ExportTarget.GITHUB_WIKI

    def _get_headers(self, config: ExportConfig) -> dict[str, str]:
        """Get headers for GitHub API requests."""
        return {
            "Authorization": f"token {config.api_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

    def _title_to_filename(self, title: str) -> str:
        """Convert a page title to a valid wiki filename."""
        # GitHub wiki uses the title as filename
        # Replace spaces with hyphens, remove special characters
        filename = re.sub(r'[^\w\s-]', '', title)
        filename = re.sub(r'[-\s]+', '-', filename)
        return filename.strip('-')

    def _get_wiki_url(self, config: ExportConfig, title: str) -> str:
        """Get the URL for a wiki page."""
        filename = self._title_to_filename(title)
        return f"https://github.com/{config.repo_owner}/{config.repo_name}/wiki/{filename}"

    async def validate_config(self, config: ExportConfig) -> tuple[bool, Optional[str]]:
        """Validate GitHub configuration."""
        if not config.api_token:
            return False, "GitHub personal access token is required"

        if not config.repo_owner:
            return False, "Repository owner is required"

        if not config.repo_name:
            return False, "Repository name is required"

        # Test connection and check repo access
        try:
            headers = self._get_headers(config)

            async with httpx.AsyncClient() as client:
                # Check repository access
                response = await client.get(
                    f"{self.GITHUB_API_BASE}/repos/{config.repo_owner}/{config.repo_name}",
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 401:
                    return False, "Invalid GitHub token"
                elif response.status_code == 404:
                    return False, f"Repository not found: {config.repo_owner}/{config.repo_name}"
                elif response.status_code != 200:
                    return False, f"Failed to access repository: {response.status_code}"

                repo_data = response.json()
                if not repo_data.get("has_wiki"):
                    return False, "Wiki is not enabled for this repository"

                return True, None

        except httpx.ConnectError:
            return False, "Failed to connect to GitHub API"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def export_document(
        self,
        content: str,
        title: str,
        config: ExportConfig,
    ) -> ExportResult:
        """
        Export document to GitHub Wiki.

        Note: GitHub's wiki API is limited. This uses the gollum-based wiki
        which requires git operations. For simplicity, we use the REST API
        where available, falling back to creating issues with wiki content.
        """
        is_valid, error = await self.validate_config(config)
        if not is_valid:
            return self._create_error_result(self.target, error or "Invalid configuration")

        try:
            # GitHub doesn't have a direct Wiki API for creating pages
            # We need to use the wiki git repository
            # For now, we'll use the GitHub API to interact with the wiki repo

            wiki_repo_url = f"https://github.com/{config.repo_owner}/{config.repo_name}.wiki.git"

            # Try to create/update via the wiki git repo API
            headers = self._get_headers(config)
            filename = self._title_to_filename(title)

            async with httpx.AsyncClient() as client:
                # Check if wiki exists by trying to get it
                wiki_check = await client.get(
                    f"{self.GITHUB_API_BASE}/repos/{config.repo_owner}/{config.repo_name}.wiki/contents/{filename}.md",
                    headers=headers,
                    timeout=10.0,
                )

                if wiki_check.status_code == 404:
                    # Wiki repo might not exist yet or page doesn't exist
                    # Create via contents API
                    import base64
                    encoded_content = base64.b64encode(content.encode()).decode()

                    create_response = await client.put(
                        f"{self.GITHUB_API_BASE}/repos/{config.repo_owner}/{config.repo_name}.wiki/contents/{filename}.md",
                        headers=headers,
                        json={
                            "message": f"Create wiki page: {title}",
                            "content": encoded_content,
                        },
                        timeout=30.0,
                    )

                    if create_response.status_code in (200, 201):
                        return ExportResult(
                            success=True,
                            target=self.target,
                            url=self._get_wiki_url(config, title),
                            page_id=filename,
                        )
                    elif create_response.status_code == 404:
                        # Wiki repo doesn't exist - user needs to create first page manually
                        return self._create_error_result(
                            self.target,
                            "Wiki not initialized. Please create the first wiki page manually on GitHub."
                        )
                    else:
                        error_msg = create_response.json().get("message", create_response.text)
                        return self._create_error_result(self.target, f"Create failed: {error_msg}")

                elif wiki_check.status_code == 200:
                    # Page exists - update it
                    existing = wiki_check.json()
                    sha = existing.get("sha")

                    import base64
                    encoded_content = base64.b64encode(content.encode()).decode()

                    update_response = await client.put(
                        f"{self.GITHUB_API_BASE}/repos/{config.repo_owner}/{config.repo_name}.wiki/contents/{filename}.md",
                        headers=headers,
                        json={
                            "message": f"Update wiki page: {title}",
                            "content": encoded_content,
                            "sha": sha,
                        },
                        timeout=30.0,
                    )

                    if update_response.status_code == 200:
                        return ExportResult(
                            success=True,
                            target=self.target,
                            url=self._get_wiki_url(config, title),
                            page_id=filename,
                        )
                    else:
                        error_msg = update_response.json().get("message", update_response.text)
                        return self._create_error_result(self.target, f"Update failed: {error_msg}")

                else:
                    return self._create_error_result(
                        self.target,
                        f"Wiki check failed: {wiki_check.status_code}"
                    )

        except Exception as e:
            return self._create_error_result(self.target, f"Export error: {str(e)}")

    async def update_document(
        self,
        page_id: str,
        content: str,
        title: str,
        config: ExportConfig,
    ) -> ExportResult:
        """Update an existing GitHub Wiki page."""
        try:
            headers = self._get_headers(config)
            filename = page_id  # page_id is the filename

            async with httpx.AsyncClient() as client:
                # Get current file to get SHA
                get_response = await client.get(
                    f"{self.GITHUB_API_BASE}/repos/{config.repo_owner}/{config.repo_name}.wiki/contents/{filename}.md",
                    headers=headers,
                    timeout=10.0,
                )

                if get_response.status_code != 200:
                    return self._create_error_result(self.target, f"Page not found: {filename}")

                existing = get_response.json()
                sha = existing.get("sha")

                import base64
                encoded_content = base64.b64encode(content.encode()).decode()

                update_response = await client.put(
                    f"{self.GITHUB_API_BASE}/repos/{config.repo_owner}/{config.repo_name}.wiki/contents/{filename}.md",
                    headers=headers,
                    json={
                        "message": f"Update wiki page: {title}",
                        "content": encoded_content,
                        "sha": sha,
                    },
                    timeout=30.0,
                )

                if update_response.status_code == 200:
                    return ExportResult(
                        success=True,
                        target=self.target,
                        url=self._get_wiki_url(config, title),
                        page_id=filename,
                    )
                else:
                    error_msg = update_response.json().get("message", update_response.text)
                    return self._create_error_result(self.target, f"Update failed: {error_msg}")

        except Exception as e:
            return self._create_error_result(self.target, f"Update error: {str(e)}")

    async def delete_document(
        self,
        page_id: str,
        config: ExportConfig,
    ) -> ExportResult:
        """Delete a GitHub Wiki page."""
        try:
            headers = self._get_headers(config)
            filename = page_id

            async with httpx.AsyncClient() as client:
                # Get current file to get SHA
                get_response = await client.get(
                    f"{self.GITHUB_API_BASE}/repos/{config.repo_owner}/{config.repo_name}.wiki/contents/{filename}.md",
                    headers=headers,
                    timeout=10.0,
                )

                if get_response.status_code != 200:
                    return self._create_error_result(self.target, f"Page not found: {filename}")

                existing = get_response.json()
                sha = existing.get("sha")

                delete_response = await client.delete(
                    f"{self.GITHUB_API_BASE}/repos/{config.repo_owner}/{config.repo_name}.wiki/contents/{filename}.md",
                    headers=headers,
                    json={
                        "message": f"Delete wiki page: {filename}",
                        "sha": sha,
                    },
                    timeout=10.0,
                )

                if delete_response.status_code in (200, 204):
                    return ExportResult(
                        success=True,
                        target=self.target,
                        page_id=filename,
                    )
                else:
                    error_msg = delete_response.json().get("message", delete_response.text)
                    return self._create_error_result(self.target, f"Delete failed: {error_msg}")

        except Exception as e:
            return self._create_error_result(self.target, f"Delete error: {str(e)}")

    async def list_pages(
        self,
        config: ExportConfig,
        parent_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List all pages in the GitHub Wiki."""
        try:
            headers = self._get_headers(config)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.GITHUB_API_BASE}/repos/{config.repo_owner}/{config.repo_name}.wiki/contents",
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    files = response.json()
                    pages = []

                    for file in files:
                        if file.get("name", "").endswith(".md"):
                            filename = file["name"][:-3]  # Remove .md
                            title = filename.replace("-", " ")
                            pages.append({
                                "id": filename,
                                "title": title,
                                "url": self._get_wiki_url(config, title),
                            })

                    return pages

                return []

        except Exception:
            return []
