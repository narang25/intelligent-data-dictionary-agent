import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.domain.models import Annotation, ColumnPermission, User

def seed_test_data():
    db = SessionLocal()
    
    # 1. Get the test user
    user = db.query(User).filter_by(email="nikhilnarang2505@gmail.com").first()
    if not user:
        print("No user found")
        return
        
    print(f"Testing with User: {user.email}, Role: {user.role}")
    
    # 2. Add an Annotation
    existing_anno = db.query(Annotation).filter_by(table_name="customers", column_name="customer_city").first()
    if not existing_anno:
        anno = Annotation(
            table_name="customers",
            column_name="customer_city",
            content="CRITICAL NOTE: Our business logic requires checking customer_state when querying city because city names are not unique across states.",
            author_id=user.id
        )
        db.add(anno)
        print("Added annotation to customers.customer_city")
    
    # 3. Add a Guardrail (Block access to payment_value)
    existing_perm = db.query(ColumnPermission).filter_by(role="analyst", table_name="payments", column_name="payment_value").first()
    if not existing_perm:
        perm = ColumnPermission(
            role="analyst",
            table_name="payments",
            column_name="payment_value",
            allow=False
        )
        db.add(perm)
        print("Added restrictive guardrail for role 'analyst' on payments.payment_value")
        
    db.commit()
    db.close()
    print("Seed complete")

if __name__ == "__main__":
    seed_test_data()
