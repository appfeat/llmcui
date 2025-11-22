import subprocess


class LLMService:
    def __init__(self, llm_cmd="llm"):
        self.llm_cmd = llm_cmd

    # -------------------------------------------------
    # Main prompt call
    # -------------------------------------------------
    def call_prompt(self, prompt_text: str):
        try:
            p = subprocess.Popen(
                [self.llm_cmd, "prompt"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            out, err = p.communicate(prompt_text, timeout=120)

            if p.returncode != 0:
                print("llm error:", err.strip())
                return None

            return out.strip()

        except Exception as e:
            print("LLM invocation error:", e)
            return None

    # -------------------------------------------------
    # Title generation for new chats
    # -------------------------------------------------
    def generate_title(self, user_prompt: str) -> str:
        """
        Generate a short chat title (max 6 words).
        Uses only the first user message. Returns a safe,
        cleaned, word-limited string.
        """

        title_prompt = (
            "Generate a short, human-readable chat title, max 6 words. "
            "Return ONLY the title. No quotes. No punctuation. No emojis.\n\n"
            f"USER MESSAGE:\n{user_prompt}"
        )

        try:
            p = subprocess.Popen(
                [self.llm_cmd, "prompt"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            out, err = p.communicate(title_prompt, timeout=30)

            if p.returncode != 0:
                print("llm error:", err.strip())
                return "untitled"

            raw = (out or "").strip()

            if not raw:
                return "untitled"

            # clean punctuation and quotes
            cleaned = raw.replace("\n", " ").strip()
            cleaned = cleaned.strip(' "\'')

            # limit to 6 words while preserving whole-word boundaries
            words = cleaned.split()
            limited = " ".join(words[:6])

            # limit to 80 chars
            return limited[:80].strip() or "untitled"

        except Exception:
            return "untitled"
