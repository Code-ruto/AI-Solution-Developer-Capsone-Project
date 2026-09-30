import ollama

def ask_llm(prompt: str, model: str = "llama3.2") -> str:
    """Converts all parameters into string type data. Instantiates llama 3.2 llm instance
    and sets the response to get the prompt from users. Will return the content of the response.
    Handles empty content returns with message displaying that no model content was returned."""
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.message.content
    if content is None:
        raise ValueError("Model returned no content")
    return content  # now guaranteed to be str