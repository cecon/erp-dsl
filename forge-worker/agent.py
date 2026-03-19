"""Cappy Agent — autonomous coding loop.

Flow:
1. Clone the repository (or pull if already cloned)
2. Create a new branch: cappy/{slug}
3. Loop: ask Gemini what to do → execute tool calls → repeat until done
4. Commit all changes
5. Push branch
6. Open GitHub PR"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Awaitable

import httpx

from github_api import GitHubAPI
from tools import ForgeTools


# ── System prompt ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Cappy, an autonomous software engineering agent.
You operate inside a cloned Git repository and your job is to complete a coding task end-to-end.

You have access to the following tools:
- read_file(path): read the content of a file
- write_file(path, content): write content to a file (creates dirs as needed)
- bash(cmd): execute a shell command in the workspace directory
- list_dir(path): list files in a directory
- git_diff(): show current uncommitted changes
- git_commit(message): commit all staged changes with the given message

== CRITICAL: RESPONSE FORMAT ==
You MUST respond with ONLY a raw JSON object. No explanations, no markdown code fences, no text before or after.
Any text outside the JSON will cause a parse failure and you will be asked to retry.

To call a tool:
{"tool": "read_file", "args": {"path": "README.md"}}

When you are completely done (all files written, tests pass if applicable):
{"tool": "done", "args": {"summary": "Brief summary of what was done"}}

== RULES ==
- Always start by exploring the repository structure with list_dir, then read relevant files.
- Make small, focused changes. Commit frequently.
- If a bash command fails, analyze the output and try to fix the issue.
- Never commit secrets, tokens, or credentials.
- Write clear, conventional commit messages (feat:, fix:, chore:, etc).
- Maximum 20 tool calls per task to avoid infinite loops.
- NEVER write prose. Your every response must be valid JSON, nothing else."""


class CappyAgent:
    """Autonomous coding agent that clones a repo, makes changes, and opens a PR."""

    MAX_ITERATIONS = 20

    def __init__(
        self,
        github_token: str,
        github_repo: str,
        base_branch: str,
        workspace_dir: str,
        emit: Callable[[str], Awaitable[None]],
    ) -> None:
        self.github_token = github_token
        self.github_repo = github_repo  # "org/repo"
        self.base_branch = base_branch
        self.workspace_dir = Path(workspace_dir)
        self.emit = emit
        self.github = GitHubAPI(token=github_token, repo=github_repo)

    # ── Public API ────────────────────────────────────────────────────

    async def run(self, task: str, branch_prefix: str = "cappy") -> str:
        """Execute the full agent loop and return the PR URL."""
        # 1. Prepare workspace
        repo_dir = await self._prepare_workspace()

        # 2. Create branch
        branch_name = self._make_branch_name(task, branch_prefix)
        await self._create_branch(repo_dir, branch_name)

        # 3. Agent loop
        tools = ForgeTools(repo_dir=repo_dir, emit=self.emit)
        summary = await self._agent_loop(task=task, tools=tools)

        # 4. Commit any remaining changes
        diff = await tools.git_diff()
        if diff.strip():
            await tools.git_commit(f"cappy: apply task changes\n\n{summary}")

        # 5. Push
        await self._git_push(repo_dir, branch_name)

        # 6. Open PR
        pr_url = await self.github.create_pull_request(
            head=branch_name,
            base=self.base_branch,
            title=f"forge: {task[:72]}",
            body=self._build_pr_body(task, summary),
        )

        await self.emit(f"✅ Pull Request aberto: {pr_url}")
        return pr_url

    # ── Agent loop ────────────────────────────────────────────────────

    async def _agent_loop(self, task: str, tools: ForgeTools) -> str:
        """Main ReAct loop: think → act → observe → repeat."""
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Task: {task}"},
        ]

        summary = "Task completed."
        for i in range(self.MAX_ITERATIONS):
            await self.emit(f"🔄 Iteração {i + 1}/{self.MAX_ITERATIONS}")

            response_text = await self._call_gemini(messages)
            await self.emit(f"🧠 Gemini: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")

            # Parse tool call from response
            tool_call = self._parse_tool_call(response_text)
            if tool_call is None:
                await self.emit("⚠️ Resposta inválida do Gemini, solicitando reenvio...")
                messages.append({"role": "model", "content": response_text})
                messages.append({
                    "role": "user",
                    "content": (
                        "ERROR: Your response was not valid JSON. "
                        "You MUST respond with ONLY a raw JSON object, nothing else. "
                        'Example: {"tool": "list_dir", "args": {"path": "."}}'
                    ),
                })
                continue

            messages.append({"role": "model", "content": response_text})

            if tool_call["tool"] == "done":
                summary = tool_call.get("args", {}).get("summary", "Task completed.")
                await self.emit(f"✅ Agente finalizou: {summary}")
                break

            # Execute tool
            result = await self._execute_tool(tool_call, tools)
            observation = f"Tool result: {result}"
            await self.emit(f"🔧 {tool_call['tool']}: {str(result)[:300]}")
            messages.append({"role": "user", "content": observation})

        return summary

    # ── Tool execution ────────────────────────────────────────────────

    async def _execute_tool(self, tool_call: dict, tools: ForgeTools) -> str:
        """Dispatch tool call to the appropriate handler."""
        tool = tool_call.get("tool", "")
        args = tool_call.get("args", {})

        try:
            if tool == "read_file":
                return await tools.read_file(args["path"])
            elif tool == "write_file":
                return await tools.write_file(args["path"], args["content"])
            elif tool == "bash":
                return await tools.bash(args["cmd"])
            elif tool == "list_dir":
                return await tools.list_dir(args.get("path", "."))
            elif tool == "git_diff":
                return await tools.git_diff()
            elif tool == "git_commit":
                return await tools.git_commit(args["message"])
            else:
                return f"Unknown tool: {tool}"
        except KeyError as e:
            return f"Missing argument: {e}"
        except Exception as e:
            return f"Tool error: {e}"

    # ── Git operations ────────────────────────────────────────────────

    async def _prepare_workspace(self) -> Path:
        """Clone or update the repository in the workspace."""
        repo_name = self.github_repo.split("/")[-1]
        repo_dir = self.workspace_dir / repo_name

        clone_url = f"https://{self.github_token}@github.com/{self.github_repo}.git"

        if repo_dir.exists():
            await self.emit(f"🔄 Atualizando repositório existente em {repo_dir}")
            await self._run_git(repo_dir, ["fetch", "origin"])
            await self._run_git(repo_dir, ["checkout", self.base_branch])
            await self._run_git(repo_dir, ["reset", "--hard", f"origin/{self.base_branch}"])
        else:
            await self.emit(f"📥 Clonando {self.github_repo} em {repo_dir}")
            await self._run_git(self.workspace_dir, ["clone", "--depth=1", clone_url, repo_name])

        return repo_dir

    async def _create_branch(self, repo_dir: Path, branch_name: str) -> None:
        """Create and checkout a new branch."""
        await self.emit(f"🌿 Criando branch {branch_name}")
        # Delete local branch if exists
        try:
            await self._run_git(repo_dir, ["branch", "-D", branch_name])
        except Exception:
            pass
        await self._run_git(repo_dir, ["checkout", "-b", branch_name])

    async def _git_push(self, repo_dir: Path, branch_name: str) -> None:
        """Push the branch to origin."""
        await self.emit(f"📤 Fazendo push da branch {branch_name}")
        # Set remote URL with token for auth
        remote_url = f"https://{self.github_token}@github.com/{self.github_repo}.git"
        await self._run_git(repo_dir, ["remote", "set-url", "origin", remote_url])
        await self._run_git(repo_dir, ["push", "--force-with-lease", "origin", branch_name])

    async def _run_git(self, cwd: Path, args: list[str]) -> str:
        """Run a git command and return stdout."""
        process = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {stderr.decode()}")
        return stdout.decode()

    # ── Gemini via CLI ────────────────────────────────────────────────

    async def _call_gemini(self, messages: list[dict]) -> str:
        """Call Gemini using the CLI (gemini -p ...) with OAuth credentials."""
        # Build a single prompt from the message list
        # The CLI doesn't support multi-turn natively, so we serialize the history
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt_parts.append(f"[SYSTEM]\n{content}")
            elif role == "user":
                prompt_parts.append(f"[USER]\n{content}")
            elif role in ("model", "assistant"):
                prompt_parts.append(f"[ASSISTANT]\n{content}")

        full_prompt = "\n\n".join(prompt_parts)

        process = await asyncio.create_subprocess_exec(
            "gemini",
            "-p", full_prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={
                **__import__("os").environ,
                "HOME": "/root",  # where gemini stores credentials
                "TERM": "dumb",
                "NO_COLOR": "1",
            },
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120.0)
        except asyncio.TimeoutError:
            process.kill()
            raise RuntimeError("Gemini CLI timed out after 120s")

        if process.returncode != 0:
            err = stderr.decode(errors="replace")
            raise RuntimeError(f"Gemini CLI error: {err}")

        return stdout.decode(errors="replace").strip()

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _parse_tool_call(text: str) -> dict | None:
        """Extract JSON tool call from model response."""
        # Try to find JSON block in the response
        text = text.strip()
        # Remove markdown code blocks if present
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```", "", text)
        text = text.strip()

        # Find first { ... } block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _make_branch_name(task: str, prefix: str) -> str:
        """Convert task to a safe git branch name."""
        slug = re.sub(r"[^a-zA-Z0-9\s]", "", task.lower())
        slug = re.sub(r"\s+", "-", slug.strip())[:40]
        return f"{prefix}/{slug}"

    @staticmethod
    def _build_pr_body(task: str, summary: str) -> str:
        return f"""## 🤖 Cappy Agent — Tarefa Automática

### Tarefa
{task}

### O que foi feito
{summary}

---
*Este PR foi criado automaticamente pelo Cappy Agent.*
"""
