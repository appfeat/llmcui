from unittest.mock import patch
from core.services.llm_service import LLMService

def test_llm_service_calls_llm_prompt():
    svc = LLMService()

    with patch("core.services.llm_service.LLMService.call_prompt") as mock_call:
        mock_call.return_value = "ok"
        out = svc.call_prompt("hello")
        assert out == "ok"
