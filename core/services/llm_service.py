# core/services/llm_service.py
import subprocess
import shlex
import os

class LLMService:
    def __init__(self, llm_cmd="llm"):
        self.llm_cmd = llm_cmd

    def call_prompt(self, prompt_text):
        try:
            # call: llm prompt --no-stream (if supported) or llm prompt
            # For simplicity call: llm prompt (pass prompt via stdin)
            p = subprocess.Popen([self.llm_cmd, "prompt"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out, err = p.communicate(prompt_text, timeout=120)
            if p.returncode != 0:
                print("llm error:", err.strip())
                return None
            return out.strip()
        except Exception as e:
            print("LLM invocation error:", e)
            return None
