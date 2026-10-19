from types import SimpleNamespace

import pytest

import search


def test_ask_llm_sends_prompt_and_returns_model_response(monkeypatch):
    """Return the model text and send the expected prompt and model to Ollama."""
    expected_text = "Found the book."
    expected_call = {
        "model": "llama3.2",
        "messages": [{"role": "user", "content": "Find a book"}],
    }
    actual_call = {}

    def fake_chat(**kwargs):
        """Capture the Ollama request and return a mock response object."""
        actual_call.update(kwargs)
        return SimpleNamespace(
            message=SimpleNamespace(content=expected_text),
        )

    monkeypatch.setattr(search.ollama, "chat", fake_chat)

    result = search.ask_llm("Find a book")

    assert result == expected_text
    assert actual_call == expected_call


def test_ask_llm_raises_when_model_returns_no_content(monkeypatch):
    """Raise ValueError when the Ollama response has no message content."""
    monkeypatch.setattr(
        search.ollama,
        "chat",
        lambda **kwargs: SimpleNamespace(
            message=SimpleNamespace(content=None),
        ),
    )

    with pytest.raises(ValueError, match="Model returned no content"):
        search.ask_llm("Find a book")
