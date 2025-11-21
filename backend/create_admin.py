# create_admin.py
import sys
from db import SessionLocal, engine, Base
from models import User
from auth import hash_password

# Create tables
Base.metadata.create_all(bind=engine)

def create_admin(username="admin", password="admin123"):
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"User '{username}' already exists. Updating password and setting to active.")
            existing.hashed_password = hash_password(password)
            existing.is_active = True
            db.add(existing)
            db.commit()
            db.refresh(existing)
            print(f"✅ Admin user '{username}' updated successfully!")
            return
        
        # Create admin user
        admin = User(
            username=username,
            hashed_password=hash_password(password),
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Role: admin")
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        username = sys.argv[1] if len(sys.argv) > 1 else "admin"
        password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
        create_admin(username, password)
    else:
        create_admin()
