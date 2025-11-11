# create_admin.py
from db import get_session, init_db
from models import User
from auth import hash_password
init_db()
s = get_session()
admin = User(email="admin@example.com", name="Administrator", password_hash=hash_password("adminpass"), role="admin", is_verified=True)
s.add(admin)
s.commit()
print("Admin user created:", admin.email, "password: adminpass")
s.close()
