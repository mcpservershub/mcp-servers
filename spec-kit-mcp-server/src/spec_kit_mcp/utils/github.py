"""GitHub API client for template downloads."""

import httpx
import zipfile
import tempfile
import shutil
import platform
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import json

from ..exceptions import NetworkError, FileSystemError
from ..config import Settings

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for GitHub API interactions."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if settings.github_token:
            self.headers["Authorization"] = f"token {settings.github_token}"

    async def download_template(
        self,
        ai_assistant: str,
        target_dir: Path
    ) -> Path:
        """Download spec-kit template from GitHub releases."""
        try:
            # Get latest release
            release_info = await self._get_latest_release()

            # Determine shell type based on platform
            system = platform.system()
            if system == "Windows":
                shell_type = "ps"  # PowerShell
            else:
                shell_type = "sh"  # Bash (Linux/macOS)

            logger.info(f"Detected platform: {system}, using shell type: {shell_type}")

            # Find template asset with platform-specific naming
            # Try pattern: spec-kit-template-{ai_assistant}-{shell_type}-{version}.zip
            version = release_info['tag_name']
            asset_name = f"spec-kit-template-{ai_assistant}-{shell_type}-{version}.zip"
            asset = self._find_asset(release_info, asset_name)

            if not asset:
                # Try without version but with shell type
                asset_name = f"spec-kit-template-{ai_assistant}-{shell_type}.zip"
                asset = self._find_asset(release_info, asset_name)

            if not asset:
                # Fallback: Try old naming pattern without shell type
                asset_name = f"spec-kit-template-{ai_assistant}-{version}.zip"
                asset = self._find_asset(release_info, asset_name)

            if not asset:
                # Last attempt: without version or shell type
                asset_name = f"spec-kit-template-{ai_assistant}.zip"
                asset = self._find_asset(release_info, asset_name)

            if not asset:
                raise NetworkError(
                    f"Template not found for AI assistant: {ai_assistant} on {system}",
                    details={
                        "available_assets": [a["name"] for a in release_info.get("assets", [])],
                        "attempted_names": [
                            f"spec-kit-template-{ai_assistant}-{shell_type}-{version}.zip",
                            f"spec-kit-template-{ai_assistant}-{shell_type}.zip",
                            f"spec-kit-template-{ai_assistant}-{version}.zip",
                            f"spec-kit-template-{ai_assistant}.zip"
                        ]
                    },
                    suggestions=[
                        "Check available AI assistants",
                        "Try a different assistant",
                        f"Verify template exists for {system} platform"
                    ]
                )

            # Download template
            zip_path = await self._download_asset(asset)

            # Extract template
            await self._extract_template(zip_path, target_dir)

            logger.info(f"Successfully downloaded and extracted template to {target_dir}")
            return target_dir

        except Exception as e:
            if isinstance(e, (NetworkError, FileSystemError)):
                raise
            raise NetworkError(
                f"Failed to download template",
                details={"error": str(e)},
                suggestions=["Check internet connection", "Verify GitHub credentials"]
            )

    async def _get_latest_release(self) -> Dict[str, Any]:
        """Get latest release information from GitHub."""
        url = f"{self.base_url}/repos/{self.settings.github_repo_owner}/{self.settings.github_repo_name}/releases/latest"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NetworkError(
                        "No releases found for spec-kit repository",
                        details={"url": url},
                        suggestions=["Check repository name", "Ensure releases exist"]
                    )
                raise NetworkError(
                    f"GitHub API error: {e.response.status_code}",
                    details={"url": url, "status": e.response.status_code}
                )
            except httpx.RequestError as e:
                raise NetworkError(
                    f"Failed to connect to GitHub API",
                    details={"url": url, "error": str(e)},
                    suggestions=["Check internet connection", "Try again later"]
                )

    def _find_asset(self, release_info: Dict[str, Any], asset_name: str) -> Optional[Dict[str, Any]]:
        """Find asset in release by name."""
        for asset in release_info.get("assets", []):
            if asset["name"] == asset_name or asset["name"].startswith(asset_name.replace(".zip", "")):
                return asset
        return None

    async def _download_asset(self, asset: Dict[str, Any]) -> Path:
        """Download asset from GitHub."""
        download_url = asset["browser_download_url"]
        file_size = asset["size"]
        filename = asset["name"]

        logger.info(f"Downloading {filename} ({file_size:,} bytes)")

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        download_url,
                        headers=self.headers,
                        timeout=60,
                        follow_redirects=True
                    )
                    response.raise_for_status()
                    tmp_file.write(response.content)
                    logger.info(f"Downloaded {filename} to {tmp_path}")
                    return tmp_path
                except Exception as e:
                    tmp_path.unlink(missing_ok=True)
                    raise NetworkError(
                        f"Failed to download asset",
                        details={"url": download_url, "error": str(e)}
                    )

    async def _extract_template(self, zip_path: Path, target_dir: Path) -> None:
        """Extract template ZIP file."""
        try:
            target_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract to temporary directory first
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    zip_ref.extractall(temp_path)

                    # Check for nested directory structure
                    extracted_items = list(temp_path.iterdir())
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        # Move contents up one level
                        source_dir = extracted_items[0]
                    else:
                        source_dir = temp_path

                    # Copy to target directory
                    for item in source_dir.iterdir():
                        dest = target_dir / item.name
                        if item.is_dir():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dest)

            logger.info(f"Extracted template to {target_dir}")

        except Exception as e:
            raise FileSystemError(
                f"Failed to extract template",
                details={"zip_path": str(zip_path), "target": str(target_dir), "error": str(e)}
            )
        finally:
            # Clean up ZIP file
            zip_path.unlink(missing_ok=True)

    async def check_rate_limit(self) -> Dict[str, int]:
        """Check GitHub API rate limit."""
        url = f"{self.base_url}/rate_limit"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return {
                    "limit": data["rate"]["limit"],
                    "remaining": data["rate"]["remaining"],
                    "reset": data["rate"]["reset"]
                }
            except Exception as e:
                logger.warning(f"Failed to check rate limit: {e}")
                return {"limit": 0, "remaining": 0, "reset": 0}