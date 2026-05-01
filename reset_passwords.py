from app.db.session import SessionLocal
from app.db.entities import User
from app.core.security import hash_password

def reset_passwords():
    db = SessionLocal()
    try:
        # Reset Teacher
        teacher = db.query(User).filter(User.Email == 'teacher@school.com').first()
        if teacher:
            teacher.PasswordHash = hash_password('Teacher@123')
            print("Teacher password reset to 'Teacher@123'")
            
        # Reset Admin
        admin = db.query(User).filter(User.Email == 'admin@school.com').first()
        if admin:
            admin.PasswordHash = hash_password('Admin@123')
            print("Admin password reset to 'Admin@123'")
            
        # Reset Parent
        parent = db.query(User).filter(User.Email == 'parent@home.com').first()
        if parent:
            parent.PasswordHash = hash_password('Parent@123')
            print("Parent password reset to 'Parent@123'")
            
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    reset_passwords()
