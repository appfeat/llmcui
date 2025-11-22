import subprocess
import shlex
import os

class LLMService:
    def __init__(self, llm_cmd="llm"):
        self.llm_cmd = llm_cmd

    def call_prompt(self, prompt_text):
        try:
            p = subprocess.Popen(
                [self.llm_cmd, "prompt"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            out, err = p.communicate(prompt_text, timeout=120)
            if p.returncode != 0:
                print("llm error:", err.strip())
                return None
            return out.strip()
        except Exception as e:
            print("LLM invocation error:", e)
            return None

    # -----------------------------------------------------
    # STEP 3 ADDITION → title generation for new chats
    # -----------------------------------------------------
    def generate_title(self, user_prompt: str) -> str:
        """
        Ask the LLM to generate a short title (max 6 words)
        based ONLY on the user's first message.
        """
        title_prompt = (
            "Generate a very short title (max 6 words) summarizing this message. "
            "Return only the title, no quotes, no punctuation.\n\n"
            f"MESSAGE:\n{user_prompt}"
        )

        try:
            p = subprocess.Popen(
                [self.llm_cmd, "prompt"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            out, err = p.communicate(title_prompt, timeout=30)
            if p.returncode != 0:
                print("llm error:", err.strip())
                return "untitled"
            title = out.strip()
            # cleanliness enforcement
            return title.replace("\n", " ").strip()[:80]
        except Exception:
            return "untitled"
