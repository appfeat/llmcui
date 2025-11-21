import cli.main
from unittest.mock import patch

def test_cli_basic_invocation(monkeypatch):
    # Mock the LLM output
    with patch("core.services.llm_service.LLMService.call_prompt") as mock_call:
        mock_call.return_value = "response"

        # Run CLI with a simple prompt
        rc = cli.main.main(["hello"])

        assert rc == 0
        mock_call.assert_called_once()
