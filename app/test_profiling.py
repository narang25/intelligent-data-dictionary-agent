import os
from dotenv import load_dotenv
from app.core.database import engine, SessionLocal
from app.services.profiling_service import ProfilingService

load_dotenv()

session = SessionLocal()

profiler = ProfilingService(engine, session)
profiler.run_profiling()
