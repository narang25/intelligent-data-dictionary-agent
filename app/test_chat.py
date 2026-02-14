from dotenv import load_dotenv
from app.core.database import engine, SessionLocal
from app.services.ai_service import AIService
from app.services.chat_service import ChatService

load_dotenv()

session = SessionLocal()
ai_service = AIService()

chat = ChatService(engine, session, ai_service)

question = "Are there any data quality issues in documentation table?"

answer = chat.ask(question)

res1 = chat.ask("Show documentation records.")
print(res1)

sid = res1["session_id"]

res2 = chat.ask("Now only show table ones.", session_id=sid)
print(res2)


print("\nAI Answer:\n")
print(answer)
