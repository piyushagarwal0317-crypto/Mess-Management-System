from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import date, datetime

import models
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hostel Mess Management System")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# AUTHENTICATION & LOGIN (<<include>> Check Details)
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login")
async def process_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    # Use Case: Login <<include>> Check Details
    user = db.query(models.User).filter(
        models.User.username == username,
        models.User.password == password,
        models.User.role == role
    ).first()

    if user:
        if user.role == 'student':
            return RedirectResponse(url=f"/student/{username}", status_code=303)
        elif user.role == 'manager':
            return RedirectResponse(url=f"/manager/{username}", status_code=303)
        elif user.role == 'staff':
            return RedirectResponse(url=f"/staff/{username}", status_code=303)
        elif user.role == 'admin':
            return RedirectResponse(url=f"/admin/{username}", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": "Invalid Username, Password, or Role selected!"}
    )

# ==========================================
# 1. STUDENT ROLE ROUTES
# ==========================================
@app.get("/student/{username}", response_class=HTMLResponse)
async def student_dashboard(username: str, request: Request, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    student = db.query(models.Student).filter(models.Student.username == username).first()
    menu = db.query(models.Menu).all()
    complaints = db.query(models.Complaint).filter(models.Complaint.student_id == username).all()
    
    # Separate unpaid monthly bills and payment history
    unpaid_bills = db.query(models.Payment).filter(
        models.Payment.student_id == username,
        models.Payment.status == "Unpaid"
    ).all()
    payment_history = db.query(models.Payment).filter(
        models.Payment.student_id == username,
        models.Payment.status != "Unpaid"
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="student_dash.html",
        context={
            "user": user,
            "student": student,
            "menu": menu,
            "complaints": complaints,
            "unpaid_bills": unpaid_bills,
            "payment_history": payment_history
        }
    )

@app.post("/student/{username}/complaint")
async def submit_complaint(username: str, text: str = Form(...), db: Session = Depends(get_db)):
    # Use Case: Submit Complaint
    db.add(models.Complaint(student_id=username, text=text, date=date.today(), status="Pending"))
    db.commit()
    return RedirectResponse(url=f"/student/{username}", status_code=303)

@app.post("/student/{username}/pay/{payment_id}")
async def pay_mess_fee(username: str, payment_id: int, db: Session = Depends(get_db)):
    # Use Case: Pay Mess Fee <<extend>> Verify Payment Details
    payment = db.query(models.Payment).filter(models.Payment.payment_id == payment_id).first()
    if payment and payment.amount > 0:  # verifyDetails() check
        payment.status = "Paid (Verified)"
        payment.date = date.today()
        db.commit()
    return RedirectResponse(url=f"/student/{username}", status_code=303)

@app.get("/student/{username}/receipt/{payment_id}", response_class=HTMLResponse)
async def download_receipt(username: str, payment_id: int, request: Request, db: Session = Depends(get_db)):
    # Use Case: Pay Mess Fee <<extend>> Download Receipt (downloadReceipt())
    payment = db.query(models.Payment).filter(models.Payment.payment_id == payment_id).first()
    student = db.query(models.Student).filter(models.Student.username == username).first()
    user = db.query(models.User).filter(models.User.username == username).first()
    return templates.TemplateResponse(
        request=request,
        name="receipt.html",
        context={"payment": payment, "student": student, "user": user}
    )

# ==========================================
# 2. MESS MANAGER ROLE ROUTES
# ==========================================
@app.get("/manager/{username}", response_class=HTMLResponse)
async def manager_dashboard(username: str, request: Request, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    manager = db.query(models.MessManager).filter(models.MessManager.username == username).first()
    students = db.query(models.Student).all()
    menu = db.query(models.Menu).all()
    complaints = db.query(models.Complaint).all()
    leaves = db.query(models.Leave).all()
    stocks = db.query(models.Stock).all()
    attendance = db.query(models.Attendance).all()
    bills = db.query(models.Payment).all()

    return templates.TemplateResponse(
        request=request,
        name="manager_dash.html",
        context={
            "user": user,
            "manager": manager,
            "students": students,
            "menu": menu,
            "complaints": complaints,
            "leaves": leaves,
            "stocks": stocks,
            "attendance": attendance,
            "bills": bills
        }
    )

@app.post("/manager/{username}/student-reg")
async def manage_student_registration(
    username: str,
    student_username: str = Form(...),
    room_no: str = Form(...),
    mess_id: str = Form(...),
    reg_status: str = Form(...),
    db: Session = Depends(get_db)
):
    # Use Case: Manage Student Registrations
    student = db.query(models.Student).filter(models.Student.username == student_username).first()
    if student:
        student.room_no = room_no
        student.mess_id = mess_id
        student.is_registered = reg_status
        db.commit()
    return RedirectResponse(url=f"/manager/{username}", status_code=303)

@app.post("/manager/{username}/update-menu")
async def update_weekly_menu(
    username: str,
    day: str = Form(...),
    meal_type: str = Form(...),
    item: str = Form(...),
    db: Session = Depends(get_db)
):
    # Class Diagram: Menu.updateMeal(mealType: String, item: String)
    menu_day = db.query(models.Menu).filter(models.Menu.day == day).first()
    if menu_day:
        if meal_type == "breakfast":
            menu_day.breakfast = item
        elif meal_type == "lunch":
            menu_day.lunch = item
        elif meal_type == "dinner":
            menu_day.dinner = item
        db.commit()
    return RedirectResponse(url=f"/manager/{username}", status_code=303)

@app.post("/manager/{username}/complaint/{complaint_id}")
async def manager_process_complaint(
    username: str,
    complaint_id: int,
    new_status: str = Form(...),
    db: Session = Depends(get_db)
):
    # Use Case: View Complaints & Activity Diagram: Process Complaint -> Update Status
    comp = db.query(models.Complaint).filter(models.Complaint.complaint_id == complaint_id).first()
    if comp:
        comp.status = new_status
        db.commit()
    return RedirectResponse(url=f"/manager/{username}", status_code=303)

@app.post("/manager/{username}/generate-bill")
async def generate_monthly_bill(
    username: str,
    student_id: str = Form(...),
    month: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    # Use Case: Generate Monthly Bill (generateBill(student, month))
    if student_id == "ALL":
        students = db.query(models.Student).filter(models.Student.is_registered == "Approved").all()
        for s in students:
            db.add(models.Payment(student_id=s.username, month=month, amount=amount, date=date.today(), status="Unpaid"))
    else:
        db.add(models.Payment(student_id=student_id, month=month, amount=amount, date=date.today(), status="Unpaid"))
    db.commit()
    return RedirectResponse(url=f"/manager/{username}", status_code=303)

@app.post("/manager/{username}/leave/{leave_id}")
async def process_staff_leave(
    username: str,
    leave_id: int,
    decision: str = Form(...),
    db: Session = Depends(get_db)
):
    # Use Case: Manage Mess Staff <<extend>> Approve / Reject Staff Leave (processLeave)
    leave = db.query(models.Leave).filter(models.Leave.leave_id == leave_id).first()
    if leave:
        leave.status = decision
        db.commit()
    return RedirectResponse(url=f"/manager/{username}", status_code=303)

@app.post("/manager/{username}/stock")
async def update_stock(
    username: str,
    item_name: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form(...),
    alert_threshold: float = Form(...),
    db: Session = Depends(get_db)
):
    # DFD Level 1: Record Attendance, Stock Update -> Stock Report & Alerts
    stock = db.query(models.Stock).filter(models.Stock.item_name == item_name).first()
    if stock:
        stock.quantity = quantity
        stock.unit = unit
        stock.alert_threshold = alert_threshold
    else:
        db.add(models.Stock(item_name=item_name, quantity=quantity, unit=unit, alert_threshold=alert_threshold))
    db.commit()
    return RedirectResponse(url=f"/manager/{username}", status_code=303)

@app.post("/manager/{username}/attendance")
async def record_attendance(
    username: str,
    person_id: str = Form(...),
    role: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    # DFD Level 1: Record Attendance
    db.add(models.Attendance(person_id=person_id, role=role, date=date.today(), status=status))
    db.commit()
    return RedirectResponse(url=f"/manager/{username}", status_code=303)

# ==========================================
# 3. MESS STAFF ROLE ROUTES
# ==========================================
@app.get("/staff/{username}", response_class=HTMLResponse)
async def staff_dashboard(username: str, request: Request, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    staff = db.query(models.MessStaff).filter(models.MessStaff.username == username).first()
    menu = db.query(models.Menu).all()
    leaves = db.query(models.Leave).filter(models.Leave.staff_id == username).all()

    return templates.TemplateResponse(
        request=request,
        name="staff_dash.html",
        context={
            "user": user,
            "staff": staff,
            "menu": menu,
            "leaves": leaves
        }
    )

@app.post("/staff/{username}/apply-leave")
async def apply_for_leave(
    username: str,
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason: str = Form(...),
    db: Session = Depends(get_db)
):
    # Use Case: Apply For Leave (applyForLeave(startDate, endDate, reason))
    s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    db.add(models.Leave(staff_id=username, start_date=s_date, end_date=e_date, reason=reason, status="Pending"))
    db.commit()
    return RedirectResponse(url=f"/staff/{username}", status_code=303)

# ==========================================
# 4. ADMIN (Warden / DeanSW / MMC) ROLE ROUTES
# ==========================================
@app.get("/admin/{username}", response_class=HTMLResponse)
async def admin_dashboard(username: str, request: Request, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    admin = db.query(models.Admin).filter(models.Admin.username == username).first()
    users = db.query(models.User).all()
    students = db.query(models.Student).all()
    staff_list = db.query(models.MessStaff).all()
    managers = db.query(models.MessManager).all()
    payments = db.query(models.Payment).all()
    leaves = db.query(models.Leave).all()
    complaints = db.query(models.Complaint).all()

    total_revenue = sum(p.amount for p in payments if "Paid" in p.status)
    pending_dues = sum(p.amount for p in payments if p.status == "Unpaid")

    return templates.TemplateResponse(
        request=request,
        name="admin_dash.html",
        context={
            "user": user,
            "admin": admin,
            "users": users,
            "students": students,
            "staff_list": staff_list,
            "managers": managers,
            "payments": payments,
            "leaves": leaves,
            "complaints": complaints,
            "total_revenue": total_revenue,
            "pending_dues": pending_dues
        }
    )

@app.post("/admin/{username}/create-user")
async def admin_create_user(
    username: str,
    new_username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    phone_no: str = Form(...),
    role: str = Form(...),
    extra_field1: str = Form(""),
    extra_field2: str = Form(""),
    db: Session = Depends(get_db)
):
    # Use Case: Manage Students & Manage Staff / Activity Diagram: Manage Users -> Store Data
    existing = db.query(models.User).filter(models.User.username == new_username).first()
    if not existing:
        db.add(models.User(username=new_username, password=password, email=email, phone_no=phone_no, role=role))
        if role == "student":
            db.add(models.Student(username=new_username, room_no=extra_field1 or "A-101", mess_id=extra_field2 or "M1"))
        elif role == "staff":
            db.add(models.MessStaff(username=new_username, job_title=extra_field1 or "Mess Worker"))
        elif role == "manager":
            db.add(models.MessManager(username=new_username, manage_mess_id=extra_field1 or "M1"))
        elif role == "admin":
            db.add(models.Admin(username=new_username, admin_level=int(extra_field1) if extra_field1.isdigit() else 1))
        db.commit()
    return RedirectResponse(url=f"/admin/{username}", status_code=303)

@app.post("/admin/{username}/edit-user")
async def admin_edit_user(
    username: str,
    target_username: str = Form(...),
    email: str = Form(...),
    phone_no: str = Form(...),
    db: Session = Depends(get_db)
):
    # Activity Diagram: Admin -> Edit User Details -> Store Data
    u = db.query(models.User).filter(models.User.username == target_username).first()
    if u:
        u.email = email
        u.phone_no = phone_no
        db.commit()
    return RedirectResponse(url=f"/admin/{username}", status_code=303)

@app.post("/admin/{username}/delete-user/{target_username}")
async def admin_delete_user(username: str, target_username: str, db: Session = Depends(get_db)):
    if target_username != username:
        db.query(models.Student).filter(models.Student.username == target_username).delete()
        db.query(models.MessStaff).filter(models.MessStaff.username == target_username).delete()
        db.query(models.MessManager).filter(models.MessManager.username == target_username).delete()
        db.query(models.User).filter(models.User.username == target_username).delete()
        db.commit()
    return RedirectResponse(url=f"/admin/{username}", status_code=303)

@app.post("/admin/{username}/approve-bill/{payment_id}")
async def warden_approve_bill(username: str, payment_id: int, db: Session = Depends(get_db)):
    # DFD Level 1: Warden / MMC Prefect -> Sign & Approve Bill
    p = db.query(models.Payment).filter(models.Payment.payment_id == payment_id).first()
    if p:
        p.warden_approved = "Signed & Approved"
        db.commit()
    return RedirectResponse(url=f"/admin/{username}", status_code=303)

@app.post("/admin/{username}/leave/{leave_id}")
async def admin_update_leave(username: str, leave_id: int, decision: str = Form(...), db: Session = Depends(get_db)):
    # DFD Level 0: Admin -> Reject/Update Leave Application
    leave = db.query(models.Leave).filter(models.Leave.leave_id == leave_id).first()
    if leave:
        leave.status = decision
        db.commit()
    return RedirectResponse(url=f"/admin/{username}", status_code=303)