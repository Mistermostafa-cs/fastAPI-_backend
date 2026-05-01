from app.db.session import SessionLocal
from app.db.entities import User
from app.core.security import hash_password

def check_or_create_admin():
    db = SessionLocal()
    admin = db.query(User).filter(User.Email == "admin@school.com").first()
    if admin:
        print(f"Admin found: {admin.Email}")
    else:
        print("Admin not found. Creating...")
        # Note: You might need to ensure Role 'Admin' exists first
        from app.db.entities import Role
        admin_role = db.query(Role).filter(Role.RoleName == "Admin").first()
        if not admin_role:
            admin_role = Role(RoleName="Admin", Description="System Administrator")
            db.add(admin_role)
            db.flush()
        
        new_admin = User(
            Email="admin@school.com",
            PasswordHash=hash_password("Admin@123"),
            FirstName="System",
            LastName="Admin",
            RoleID=admin_role.RoleID,
            IsActive=True
        )
        db.add(new_admin)
        db.commit()
        print("Admin created successfully.")
    db.close()

if __name__ == "__main__":
    check_or_create_admin()
