import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from app.domain.models import Base

Base.metadata.create_all(bind=engine)

print("Tables created successfully!")
