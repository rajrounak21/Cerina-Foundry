from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

from agent.stream_utils import get_stream_callback

def generate_response(prompt: str, temperature: float = 0.2, stream_output: bool = False) -> str:
    callback = get_stream_callback() if stream_output else None
    
    if callback:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        full_response = []
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                full_response.append(content)
                callback(content)
        return "".join(full_response)
    else:
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
