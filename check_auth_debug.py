from app.db.session import SessionLocal
from app.db.entities import User, Role
from app.core.security import verify_password

def check_users():
    db = SessionLocal()
    try:
        emails = ['parent@home.com', 'teacher@school.com']
        users = db.query(User).filter(User.Email.in_(emails)).all()
        for u in users:
            role_name = u.Role.RoleName if u.Role else "N/A"
            pwd_match_parent = verify_password("Parent@123", u.PasswordHash)
            pwd_match_teacher = verify_password("Teacher@123", u.PasswordHash)
            print(f"Email: {u.Email}")
            print(f"  IsActive: {u.IsActive}")
            print(f"  Role: {role_name}")
            print(f"  StudentID: {u.StudentID}")
            print(f"  Match Parent@123: {pwd_match_parent}")
            print(f"  Match Teacher@123: {pwd_match_teacher}")
            print("-" * 20)
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
