from openai import OpenAI

client = OpenAI()

def answer(prompt):
    return client.responses.create(model="gpt-4.1-mini", input=prompt)
