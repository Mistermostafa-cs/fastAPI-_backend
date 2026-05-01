
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.entities import User, Role, StudentProfile, Enrollment, Class
from app.db.session import SessionLocal

def test_list_students():
    db = SessionLocal()
    try:
        students = db.query(StudentProfile).all()
        print(f"Found {len(students)} students")
        for s in students:
            print(f"Checking student ID: {s.StudentID}")
            user = db.query(User).filter(User.UserID == s.StudentID).first()
            if not user:
                print(f"User not found for student ID: {s.StudentID}")
                continue
            
            enrollment = db.query(Enrollment).filter(
                Enrollment.StudentID == s.StudentID,
                Enrollment.Status == "Active"
            ).first()
            
            class_name = "Not Assigned"
            if enrollment and enrollment.ClassID:
                class_obj = db.query(Class).filter(Class.ClassID == enrollment.ClassID).first()
                if class_obj:
                    class_name = class_obj.ClassName
            
            print(f"Student: {user.FirstName} {user.LastName}, Roll: {s.RollNumber}, Class: {class_name}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_list_students()
