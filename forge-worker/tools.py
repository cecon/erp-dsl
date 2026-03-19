"""Forge Tools — filesystem and shell operations for the agent."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable, Awaitable


class ForgeTools:
    """Sandboxed tool execution within a Git workspace directory."""

    def __init__(self, repo_dir: Path, emit: Callable[[str], Awaitable[None]]) -> None:
        self.repo_dir = repo_dir
        self.emit = emit

    def _safe_path(self, path: str) -> Path:
        """Resolve a path relative to repo_dir, preventing directory traversal."""
        resolved = (self.repo_dir / path).resolve()
        if not str(resolved).startswith(str(self.repo_dir.resolve())):
            raise ValueError(f"Path escape attempt: {path}")
        return resolved

    async def read_file(self, path: str) -> str:
        """Read a file and return its content."""
        p = self._safe_path(path)
        if not p.exists():
            return f"[File not found: {path}]"
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"[Error reading file: {e}]"

    async def write_file(self, path: str, content: str) -> str:
        """Write content to a file, creating parent directories as needed."""
        p = self._safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"File written: {path} ({len(content)} chars)"

    async def bash(self, cmd: str) -> str:
        """Execute a shell command in the repo directory and return output."""
        process = await asyncio.create_subprocess_shell(
            cmd,
            cwd=str(self.repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=60.0)
        except asyncio.TimeoutError:
            process.kill()
            return "[Command timed out after 60s]"

        output = stdout.decode(errors="replace")
        return_code = process.returncode
        result = output[:4000]  # Limit output size
        if return_code != 0:
            result += f"\n[Exit code: {return_code}]"
        return result

    async def list_dir(self, path: str = ".") -> str:
        """List files in a directory (non-recursive, ignores .git)."""
        p = self._safe_path(path)
        if not p.exists():
            return f"[Directory not found: {path}]"
        if not p.is_dir():
            return f"[Not a directory: {path}]"

        entries = []
        for entry in sorted(p.iterdir()):
            if entry.name == ".git":
                continue
            if entry.is_dir():
                entries.append(f"📁 {entry.name}/")
            else:
                size = entry.stat().st_size
                entries.append(f"📄 {entry.name} ({size} bytes)")

        return "\n".join(entries) if entries else "[Empty directory]"

    async def git_diff(self) -> str:
        """Return the current git diff (unstaged + staged)."""
        process = await asyncio.create_subprocess_exec(
            "git", "diff", "HEAD",
            cwd=str(self.repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        return stdout.decode(errors="replace")[:8000]

    async def git_commit(self, message: str) -> str:
        """Stage all changes and commit."""
        # Stage all
        add = await asyncio.create_subprocess_exec(
            "git", "add", "-A",
            cwd=str(self.repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await add.communicate()

        # Check if there's anything to commit
        status = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain",
            cwd=str(self.repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await status.communicate()
        if not stdout.strip():
            return "Nothing to commit."

        # Commit
        commit = await asyncio.create_subprocess_exec(
            "git", "commit", "-m", message,
            cwd=str(self.repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await commit.communicate()
        if commit.returncode != 0:
            return f"Commit failed: {stderr.decode()}"
        return stdout.decode()
