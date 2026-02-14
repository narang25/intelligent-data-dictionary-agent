import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"

    def generate(self, system_prompt: str, user_prompt: str):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Lower = more deterministic
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"AI Error: {str(e)}"
