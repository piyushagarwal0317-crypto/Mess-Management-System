from datetime import date, timedelta
from database import SessionLocal, engine
import models

def seed_data():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(models.User).first():
        print("Database already seeded! Delete mess_management.db first if you want a fresh reset.")
        db.close()
        return

    # 1. Create Users & Role Profiles
    users = [
        models.User(username="piyush", password="password123", email="piyush@nits.ac.in", phone_no="9876543210", role="student"),
        models.User(username="rahul", password="password123", email="rahul@nits.ac.in", phone_no="9876543211", role="student"),
        models.User(username="manager1", password="password123", email="manager@nits.ac.in", phone_no="9123456780", role="manager"),
        models.User(username="staff1", password="password123", email="ramesh.cook@nits.ac.in", phone_no="9123456789", role="staff"),
        models.User(username="admin1", password="adminpass", email="warden@nits.ac.in", phone_no="9000011111", role="admin"),
    ]
    db.add_all(users)

    db.add(models.Student(username="piyush", room_no="BH-201", mess_id="M1", is_registered="Approved"))
    db.add(models.Student(username="rahul", room_no="BH-205", mess_id="M1", is_registered="Pending"))
    db.add(models.MessManager(username="manager1", manage_mess_id="M1"))
    db.add(models.MessStaff(username="staff1", job_title="Head Cook"))
    db.add(models.Admin(username="admin1", admin_level=1))

    # 2. Seed 7-Day Weekly Menu
    weekly_menu = [
        ("Monday", "Aloo Paratha, Curd, Tea", "Rajma Chawal, Salad, Papad", "Roti, Paneer Butter Masala, Dal Fry"),
        ("Tuesday", "Poha, Jalebi, Milk", "Rice, Sambar, Aloo Fry, Curd", "Roti, Egg Curry / Veg Kofta, Dal"),
        ("Wednesday", "Puri Sabzi, Tea", "Veg Biryani, Raita", "Roti, Chicken Curry / Kadhai Paneer"),
        ("Thursday", "Idli, Vada, Sambar, Coffee", "Rice, Dal Makhani, Jeera Aloo", "Roti, Mix Veg, Gulab Jamun"),
        ("Friday", "Bread Omelette / Cutlet, Tea", "Chole Bhature, Lassi", "Roti, Fish Curry / Matar Paneer, Rice"),
        ("Saturday", "Masala Dosa, Chutney", "Khichdi, Beguni, Papad, Pickle", "Roti, Soyabean Curry, Tadka Dal"),
        ("Sunday", "Chole Kulche, Tea", "Pulao, Kosha Mangsho / Shahi Paneer", "Light Dinner: Fried Rice & Manchurian")
    ]
    for day, b, l, d in weekly_menu:
        db.add(models.Menu(day=day, breakfast=b, lunch=l, dinner=d))

    # 3. Seed Sample Complaints
    db.add(models.Complaint(student_id="piyush", text="Dinner rotis were cold on Tuesday.", date=date.today() - timedelta(days=2), status="Resolved"))
    db.add(models.Complaint(student_id="piyush", text="Water cooler filter in Mess Hall needs cleaning.", date=date.today(), status="Pending"))

    # 4. Seed Sample Payments & Monthly Bills
    db.add(models.Payment(student_id="piyush", month="October 2026", amount=3500.0, date=date.today() - timedelta(days=25), status="Paid (Verified)", warden_approved="Signed & Approved"))
    db.add(models.Payment(student_id="piyush", month="November 2026", amount=3650.0, date=date.today(), status="Unpaid", warden_approved="Signed & Approved"))
    db.add(models.Payment(student_id="rahul", month="November 2026", amount=3650.0, date=date.today(), status="Unpaid", warden_approved="Pending"))

    # 5. Seed Sample Staff Leave
    db.add(models.Leave(staff_id="staff1", start_date=date.today() + timedelta(days=3), end_date=date.today() + timedelta(days=5), reason="Family medical emergency in hometown", status="Pending"))

    # 6. Seed DFD Level 1 Stock & Attendance
    db.add(models.Stock(item_name="Basmati Rice", quantity=180.0, unit="kg", alert_threshold=50.0))
    db.add(models.Stock(item_name="Mustard Oil", quantity=12.0, unit="Liters", alert_threshold=20.0)) # Will trigger low stock alert!
    db.add(models.Stock(item_name="Wheat Flour (Atta)", quantity=95.0, unit="kg", alert_threshold=30.0))
    db.add(models.Attendance(person_id="staff1", role="MessStaff", date=date.today(), status="Present"))
    db.add(models.Attendance(person_id="piyush", role="Student", date=date.today(), status="Present"))

    db.commit()
    db.close()
    print("Full database seeded successfully!")

if __name__ == "__main__":
    seed_data()