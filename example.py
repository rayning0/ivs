from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[
        {
            "role": "user",
            "content": "Write a one-sentence bedtime story about a unicorn.",
        }
    ],
)

print(response.choices[0].message.content)

# from openai import OpenAI
# client = OpenAI()

# response = client.embeddings.create(
#     input="Your text string goes here",
#     model="text-embedding-3-small"
# )

# print(response.data[0].embedding)
