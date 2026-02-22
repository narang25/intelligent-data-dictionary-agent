import os
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"

    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False):
        try:
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,  # Lower = more deterministic
            }

            # Enable JSON mode if requested (helps ensure valid JSON output)
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)

            content = response.choices[0].message.content
            logger.debug(f"AI Response: {content[:200]}...")
            return content

        except Exception as e:
            logger.error(f"AI Service Error: {str(e)}")
            return f"AI Error: {str(e)}"
