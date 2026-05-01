from app.db.session import SessionLocal
from app.db.entities import User, Role

def list_all_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"{'Email':<35} | {'StudentID':<15} | {'Role':<10} | {'PasswordHash'}")
        print("-" * 100)
        for u in users:
            email = str(u.Email) if u.Email else "N/A"
            sid = str(u.StudentID) if u.StudentID else "N/A"
            role = u.Role.RoleName if u.Role else "N/A"
            # We only show the hash because passwords are not stored in plain text
            print(f"{email:<35} | {sid:<15} | {role:<10} | {u.PasswordHash}")
    finally:
        db.close()

if __name__ == "__main__":
    list_all_users()
