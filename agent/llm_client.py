from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

def generate_response(prompt: str, temperature: float = 0.2) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=temperature,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

if __name__=="__main__":
    result = generate_response("Hello,!")
    print(result)