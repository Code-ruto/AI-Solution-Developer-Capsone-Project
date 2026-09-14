response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": "hi"}])
print(type(response))          # confirms it's a ChatResponse object
print(response.message)        # try this
print(response.message.content)  # and this