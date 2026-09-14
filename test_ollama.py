import ollama

def ask_llm(prompt: str, model: str = "llama3.2") -> str:
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.message.content
    if content is None:
        raise ValueError("Model returned no content")
    return content  # now guaranteed to be str