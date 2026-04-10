import sys
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, User
from auth.hashing import hash_password

def create_admin(username: str, email: str, password: str):
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    try:
        # Check if admin already exists
        existing = db.query(User).filter(
            User.username == username
        ).first()
        
        if existing:
            print(f"User '{username}' already exists.")
            if not existing.is_admin:   # type:ignore
                setattr(existing, "is_admin", True)
                db.commit()
                print(f"Updated '{username}' to admin.")
            else:
                print(f"'{username}' is already an admin.")
            return
        
        # Create new admin
        admin = User(
            username=username,
            email=email,
            password=hash_password(password),
            is_admin=True
        )
        db.add(admin)
        db.commit()
        print(f"Admin '{username}' created successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()
        
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python seed_admin.py <username> <email> <password>")
        sys.exit(1)
        
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    if len(password) < 8:
        print(f"Password must be at least 8 characters")
        sys.exit(1)
        
    create_admin(username, email, password)