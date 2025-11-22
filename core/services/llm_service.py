#!/usr/bin/env python3
"""
core.services.llm_service

Provides:
- call_prompt(prompt_text): low-level llm invocation
- generate_title(user_prompt): produce short chat title
- summarize_chat(messages): LLM chat summary (string)
- summarize_project(messages): LLM project summary (string)
- summarize_both(chat_messages, project_messages): attempt single JSON response
    { "chat_summary": "...", "project_summary": "..." }
  If JSON parsing fails or fields missing, falls back to two separate calls.
"""
import json
import subprocess
from typing import List, Tuple, Optional, Mapping, Any


class LLMService:
    def __init__(self, llm_cmd: str = "llm"):
        self.llm_cmd = llm_cmd

    # -------------------------------------------------
    # Low-level LLM invocation
    # -------------------------------------------------
    def call_prompt(self, prompt_text: str, timeout: int = 120) -> Optional[str]:
        """
        Call the external llm binary with a prompt. Returns stdout string or None on failure.
        """
        try:
            p = subprocess.Popen(
                [self.llm_cmd, "prompt"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            out, err = p.communicate(prompt_text, timeout=timeout)
            if p.returncode != 0:
                # keep stderr limited: print first line for diagnostics
                first_err_line = (err or "").splitlines()[0] if err else ""
                print("llm error:", first_err_line)
                return None
            return (out or "").strip()
        except subprocess.TimeoutExpired:
            print("LLM invocation timed out")
            try:
                p.kill()
            except Exception:
                pass
            return None
        except Exception as e:
            print("LLM invocation error:", e)
            return None

    # -------------------------------------------------
    # Title generation (existing behaviour)
    # -------------------------------------------------
    def generate_title(self, user_prompt: str) -> str:
        title_prompt = (
            "Generate a short, human-readable chat title, max 6 words.\n"
            "Return ONLY the title on a single line. No quotes, no punctuation, no emojis.\n\n"
            f"USER MESSAGE:\n{user_prompt}\n"
        )
        try:
            out = self.call_prompt(title_prompt, timeout=30)
            if not out:
                return "untitled"
            cleaned = out.replace("\n", " ").strip()
            cleaned = cleaned.strip(' "\'')
            words = cleaned.split()
            limited = " ".join(words[:6])
            return limited[:80].strip() or "untitled"
        except Exception:
            return "untitled"

    # -------------------------------------------------
    # Helpers: convert messages to text
    # -------------------------------------------------
    @staticmethod
    def _messages_to_text(messages: List[Mapping[str, Any]]) -> str:
        """
        Convert messages (rows/dicts with 'role' and 'content') to plain text.
        Each line: ROLE: content
        """
        lines = []
        for m in messages:
            # sqlite rows may be mappings or tuples; use get when possible
            role = m.get("role") if isinstance(m, Mapping) else m["role"]
            content = (m.get("content") if isinstance(m, Mapping) else m["content"]) or ""
            lines.append(f"{role}: {content.strip()}")
        return "\n".join(lines)

    # -------------------------------------------------
    # Summarization helpers
    # -------------------------------------------------
    def summarize_chat(self, messages: List[Mapping[str, Any]]) -> str:
        """
        Ask LLM to produce a chat-level distilled summary (<=400 characters).
        Returns empty string on failure.
        """
        chat_blob = self._messages_to_text(messages[-50:])  # recent messages
        prompt = (
            "You are a concise summarizer. Produce a short distilled summary of the conversation below.\n"
            "Return ONLY the plain text summary. Maximum 400 characters.\n\n"
            "CONVERSATION:\n"
            f"{chat_blob}\n"
        )
        out = self.call_prompt(prompt, timeout=45)
        return (out or "").strip()

    def summarize_project(self, messages: List[Mapping[str, Any]]) -> str:
        """
        Ask LLM to produce a project-level summary (<=800 characters).
        Returns empty string on failure.
        """
        project_blob = self._messages_to_text(messages[-200:])  # a larger window
        prompt = (
            "You are a project-level summarizer. Produce a concise summary capturing high-level goals, "
            "ongoing tasks, design decisions, and important context.\n"
            "Return ONLY the plain text summary. Maximum 800 characters.\n\n"
            "PROJECT MESSAGES:\n"
            f"{project_blob}\n"
        )
        out = self.call_prompt(prompt, timeout=60)
        return (out or "").strip()

    def summarize_both(self, chat_messages: List[Mapping[str, Any]], project_messages: List[Mapping[str, Any]]) -> Tuple[str, str]:
        """
        Preferred single-call summarization: ask the LLM to return a JSON object:
        {
          "chat_summary": "<<=400 chars>",
          "project_summary": "<<=800 chars>"
        }

        If the LLM output is not valid JSON or required keys are missing, fall back to two separate calls.
        Returns (chat_summary, project_summary) — each may be empty string on failure.
        """
        chat_blob = self._messages_to_text(chat_messages[-50:])
        project_blob = self._messages_to_text(project_messages[-200:])

        json_request = (
            "Return a JSON object (and nothing else) with two keys:\n"
            '  "chat_summary": "<short summary, <=400 chars>",\n'
            '  "project_summary": "<higher-level summary, <=800 chars>"\n\n'
            "Respond ONLY with valid JSON. Example:\n"
            '{ "chat_summary": "short chat summary...", "project_summary": "project-level summary..." }\n\n'
            "If you cannot produce valid JSON, return an empty JSON object {}.\n\n"
            "CHAT (most recent messages):\n"
            f"{chat_blob}\n\n"
            "PROJECT (recent project messages):\n"
            f"{project_blob}\n"
        )

        out = self.call_prompt(json_request, timeout=90)
        if not out:
            # fall back to separate calls
            chat_s = self.summarize_chat(chat_messages)
            proj_s = self.summarize_project(project_messages)
            return chat_s or "", proj_s or ""

        # Try to parse JSON robustly: find the first "{" and last "}" to isolate JSON payload
        try:
            first = out.find("{")
            last = out.rfind("}")
            if first != -1 and last != -1 and last >= first:
                raw_json = out[first:last + 1]
                parsed = json.loads(raw_json)
            else:
                parsed = {}
        except Exception:
            parsed = {}

        chat_summary = parsed.get("chat_summary") if isinstance(parsed, dict) else None
        project_summary = parsed.get("project_summary") if isinstance(parsed, dict) else None

        if chat_summary and project_summary:
            return (str(chat_summary).strip(), str(project_summary).strip())

        # If JSON didn't contain both fields, fallback to two separate queries
        chat_s = chat_summary or self.summarize_chat(chat_messages)
        proj_s = project_summary or self.summarize_project(project_messages)
        return (chat_s or "", proj_s or "")
