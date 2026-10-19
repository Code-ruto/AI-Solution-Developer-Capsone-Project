import pytest
from pydantic import ValidationError

import search


@pytest.mark.parametrize("search_type", ["title", "author", "topic"])
def test_extract_intent_accepts_supported_types(monkeypatch, search_type):
    """Accept each supported search type and strip whitespace from its value."""
    monkeypatch.setattr(
        search,
        "ask_llm",
        lambda prompt: f'{{"type": "{search_type}", "value": " Dune "}}',
    )

    assert search.extract_intent("Dune") == {
        "type": search_type,
        "value": "Dune",
    }


@pytest.mark.parametrize(
    "response",
    [
        '{"type": "publisher", "value": "Dune"}',
        '{"type": "topic", "value": "Dune", "extra": "unexpected"}',
        '{"type": "topic"}',
        '{"type": "topic", "value": "   "}',
        "not valid JSON",
    ],
)
def test_extract_intent_rejects_invalid_responses(monkeypatch, response):
    """Reject malformed intent JSON and values outside the model schema."""
    monkeypatch.setattr(search, "ask_llm", lambda prompt: response)

    with pytest.raises(ValidationError):
        search.extract_intent("Dune")


def test_format_response_uses_llm(monkeypatch):
    """Format a search result through the LLM using a facts-only prompt."""
    result = {"status": "not_found"}
    expected_response = "I couldn't find that book."
    captured_prompts = []

    def fake_ask_llm(prompt):
        """Capture the formatter prompt and return a predictable response."""
        captured_prompts.append(prompt)
        return expected_response

    monkeypatch.setattr(search, "ask_llm", fake_ask_llm)

    assert search.format_response(result) == expected_response
    assert "Only use the facts given below" in captured_prompts[0]
    assert f"Result: {result}" in captured_prompts[0]
