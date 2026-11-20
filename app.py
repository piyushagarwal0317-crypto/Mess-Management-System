from datetime import date

import streamlit as st

import models
from database import SessionLocal, engine


models.Base.metadata.create_all(bind=engine)

st.set_page_config(
    page_title="Hostel Mess Management",
    page_icon="🍽️",
    layout="wide",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def session_db():
    return next(get_db())


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def login():
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown(
            """
            # Hostel Mess Management
            Manage meals, payments, complaints, leave requests, inventory,
            and role-based operations from one portal.

            ### Demo accounts
            - Student: `piyush`
            - Manager: `manager1`
            - Staff: `staff1`
            - Admin: `admin1`

            Password: `password123` (admin: `adminpass`)
            """
        )

    with col2:
        st.subheader("Welcome back")
        role = st.selectbox("Role", ["student", "manager", "staff", "admin"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Sign in", type="primary", use_container_width=True):
            db = session_db()
            user = (
                db.query(models.User)
                .filter(
                    models.User.username == username,
                    models.User.password == password,
                    models.User.role == role,
                )
                .first()
            )
            db.close()
            if user:
                st.session_state.user = {
                    "username": user.username,
                    "role": user.role,
                }
                st.rerun()
            else:
                st.error("Invalid username, password, or role.")


def student_dashboard(db, username):
    user = db.query(models.User).filter(models.User.username == username).first()
    student = db.query(models.Student).filter(models.Student.username == username).first()

    st.title(f"Student Portal: {username}")
    st.caption(
        f"Room: {student.room_no} | Mess ID: {student.mess_id} | "
        f"Registration: {student.is_registered}"
    )

    if st.button("Log out"):
        logout()

    st.header("Weekly Mess Menu")
    menu = db.query(models.Menu).all()
    st.dataframe(
        [
            {
                "Day": item.day,
                "Breakfast": item.breakfast,
                "Lunch": item.lunch,
                "Dinner": item.dinner,
            }
            for item in menu
        ],
        use_container_width=True,
        hide_index=True,
    )

    left, right = st.columns(2)
    unpaid = db.query(models.Payment).filter(
        models.Payment.student_id == username,
        models.Payment.status == "Unpaid",
    ).all()
    history = db.query(models.Payment).filter(
        models.Payment.student_id == username,
        models.Payment.status != "Unpaid",
    ).all()

    with left:
        st.subheader("Pending Bills")
        if unpaid:
            for bill in unpaid:
                with st.container(border=True):
                    st.write(f"**{bill.month}**")
                    st.write(f"Amount: ₹{bill.amount:,.2f}")
                    st.write(f"Warden approval: {bill.warden_approved}")
                    if st.button("Verify & Pay", key=f"pay-{bill.payment_id}"):
                        bill.status = "Paid (Verified)"
                        bill.date = date.today()
                        db.commit()
                        st.success("Payment marked as paid.")
                        st.rerun()
        else:
            st.success("No pending monthly bills.")

    with right:
        st.subheader("Payment History")
        if history:
            st.dataframe(
                [
                    {
                        "ID": item.payment_id,
                        "Month": item.month,
                        "Amount": f"₹{item.amount:,.2f}",
                        "Date": item.date,
                        "Status": item.status,
                    }
                    for item in history
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No payment history.")

    left, right = st.columns(2)
    with left:
        st.subheader("Submit Complaint")
        complaint_text = st.text_area("Complaint or feedback")
        if st.button("Submit complaint"):
            if complaint_text.strip():
                db.add(
                    models.Complaint(
                        student_id=username,
                        text=complaint_text.strip(),
                        date=date.today(),
                        status="Pending",
                    )
                )
                db.commit()
                st.success("Complaint submitted.")
                st.rerun()
            else:
                st.warning("Please enter complaint details.")

    with right:
        st.subheader("My Complaints")
        complaints = db.query(models.Complaint).filter(
            models.Complaint.student_id == username
        ).all()
        if complaints:
            st.dataframe(
                [
                    {
                        "ID": item.complaint_id,
                        "Date": item.date,
                        "Complaint": item.text,
                        "Status": item.status,
                    }
                    for item in complaints
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No complaints submitted.")


def manager_dashboard(db, username):
    manager = db.query(models.MessManager).filter(
        models.MessManager.username == username
    ).first()

    st.title(f"Mess Manager: {username}")
    st.caption(f"Managing Mess ID: {manager.manage_mess_id}")
    if st.button("Log out"):
        logout()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Menu", "Students & Billing", "Complaints & Leave", "Inventory & Attendance"]
    )

    with tab1:
        menu = db.query(models.Menu).all()
        st.subheader("Update Weekly Menu")
        day = st.selectbox("Day", [item.day for item in menu])
        meal_type = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner"])
        meal_items = st.text_input("New meal items")
        if st.button("Update meal"):
            menu_day = db.query(models.Menu).filter(models.Menu.day == day).first()
            setattr(menu_day, meal_type.lower(), meal_items)
            db.commit()
            st.success("Menu updated.")
            st.rerun()
        st.dataframe(
            [
                {
                    "Day": item.day,
                    "Breakfast": item.breakfast,
                    "Lunch": item.lunch,
                    "Dinner": item.dinner,
                }
                for item in menu
            ],
            use_container_width=True,
            hide_index=True,
        )

    with tab2:
        students = db.query(models.Student).all()
        st.subheader("Student Registrations")
        student_username = st.selectbox(
            "Student", [item.username for item in students]
        )
        room_no = st.text_input("Room number")
        mess_id = st.text_input("Mess ID", value="M1")
        status = st.selectbox("Registration status", ["Approved", "Pending", "Rejected"])
        if st.button("Update registration"):
            student = db.query(models.Student).filter(
                models.Student.username == student_username
            ).first()
            student.room_no = room_no or student.room_no
            student.mess_id = mess_id
            student.is_registered = status
            db.commit()
            st.success("Registration updated.")
            st.rerun()

        st.subheader("Generate Monthly Bill")
        choices = ["ALL"] + [item.username for item in students]
        bill_student = st.selectbox("Student", choices)
        month = st.text_input("Month", placeholder="December 2026")
        amount = st.number_input("Amount", min_value=0.0, step=100.0)
        if st.button("Generate bill"):
            if month and amount > 0:
                targets = (
                    db.query(models.Student)
                    .filter(models.Student.is_registered == "Approved")
                    .all()
                    if bill_student == "ALL"
                    else [db.query(models.Student).filter(models.Student.username == bill_student).first()]
                )
                for target in targets:
                    db.add(
                        models.Payment(
                            student_id=target.username,
                            month=month,
                            amount=amount,
                            date=date.today(),
                            status="Unpaid",
                        )
                    )
                db.commit()
                st.success("Bill generated.")
                st.rerun()

    with tab3:
        complaints = db.query(models.Complaint).all()
        st.subheader("Student Complaints")
        for complaint in complaints:
            with st.container(border=True):
                st.write(
                    f"**#{complaint.complaint_id} - {complaint.student_id}:** "
                    f"{complaint.text}"
                )
                new_status = st.selectbox(
                    "Status",
                    ["Pending", "In Progress", "Resolved", "Rejected"],
                    index=["Pending", "In Progress", "Resolved", "Rejected"].index(
                        complaint.status
                    )
                    if complaint.status in ["Pending", "In Progress", "Resolved", "Rejected"]
                    else 0,
                    key=f"complaint-status-{complaint.complaint_id}",
                )
                if st.button("Save", key=f"complaint-save-{complaint.complaint_id}"):
                    complaint.status = new_status
                    db.commit()
                    st.rerun()

        st.subheader("Staff Leave Requests")
        leaves = db.query(models.Leave).all()
        for leave in leaves:
            with st.container(border=True):
                st.write(
                    f"{leave.staff_id}: {leave.start_date} to {leave.end_date} "
                    f"- {leave.reason}"
                )
                decision = st.selectbox(
                    "Decision",
                    ["Pending", "Approved", "Rejected"],
                    index=["Pending", "Approved", "Rejected"].index(leave.status)
                    if leave.status in ["Pending", "Approved", "Rejected"]
                    else 0,
                    key=f"leave-{leave.leave_id}",
                )
                if st.button("Update leave", key=f"leave-save-{leave.leave_id}"):
                    leave.status = decision
                    db.commit()
                    st.rerun()

    with tab4:
        st.subheader("Stock")
        item_name = st.text_input("Item name")
        quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
        unit = st.text_input("Unit", placeholder="kg or liters")
        threshold = st.number_input("Low-stock threshold", min_value=0.0, step=1.0)
        if st.button("Update stock"):
            if item_name and unit:
                stock = db.query(models.Stock).filter(
                    models.Stock.item_name == item_name
                ).first()
                if stock:
                    stock.quantity = quantity
                    stock.unit = unit
                    stock.alert_threshold = threshold
                else:
                    db.add(
                        models.Stock(
                            item_name=item_name,
                            quantity=quantity,
                            unit=unit,
                            alert_threshold=threshold,
                        )
                    )
                db.commit()
                st.success("Stock updated.")
                st.rerun()

        stocks = db.query(models.Stock).all()
        stock_rows = []
        for stock in stocks:
            alert = "LOW STOCK" if stock.quantity <= stock.alert_threshold else "Sufficient"
            stock_rows.append(
                {
                    "Item": stock.item_name,
                    "Quantity": f"{stock.quantity} {stock.unit}",
                    "Threshold": f"{stock.alert_threshold} {stock.unit}",
                    "Status": alert,
                }
            )
        st.dataframe(stock_rows, use_container_width=True, hide_index=True)

        st.subheader("Daily Attendance")
        person_id = st.text_input("Person username")
        role = st.selectbox("Person role", ["MessStaff", "Student"])
        attendance_status = st.selectbox("Attendance", ["Present", "Absent"])
        if st.button("Record attendance"):
            if person_id:
                db.add(
                    models.Attendance(
                        person_id=person_id,
                        role=role,
                        date=date.today(),
                        status=attendance_status,
                    )
                )
                db.commit()
                st.success("Attendance recorded.")
                st.rerun()


def staff_dashboard(db, username):
    staff = db.query(models.MessStaff).filter(
        models.MessStaff.username == username
    ).first()

    st.title(f"Staff Portal: {username}")
    st.caption(staff.job_title)
    if st.button("Log out"):
        logout()

    st.header("Weekly Meal Schedule")
    menu = db.query(models.Menu).all()
    st.dataframe(
        [
            {
                "Day": item.day,
                "Breakfast": item.breakfast,
                "Lunch": item.lunch,
                "Dinner": item.dinner,
            }
            for item in menu
        ],
        use_container_width=True,
        hide_index=True,
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Request Leave")
        start_date = st.date_input("Start date")
        end_date = st.date_input("End date")
        reason = st.text_area("Reason")
        if st.button("Submit leave request"):
            if end_date >= start_date and reason.strip():
                db.add(
                    models.Leave(
                        staff_id=username,
                        start_date=start_date,
                        end_date=end_date,
                        reason=reason.strip(),
                        status="Pending",
                    )
                )
                db.commit()
                st.success("Leave request submitted.")
                st.rerun()
            else:
                st.warning("Enter a valid date range and reason.")

    with right:
        st.subheader("Leave History")
        leaves = db.query(models.Leave).filter(
            models.Leave.staff_id == username
        ).all()
        st.dataframe(
            [
                {
                    "Start": item.start_date,
                    "End": item.end_date,
                    "Reason": item.reason,
                    "Status": item.status,
                }
                for item in leaves
            ],
            use_container_width=True,
            hide_index=True,
        )


def admin_dashboard(db, username):
    admin = db.query(models.Admin).filter(models.Admin.username == username).first()

    st.title(f"Admin / Warden Portal: {username}")
    st.caption(f"Admin clearance level: {admin.admin_level}")
    if st.button("Log out"):
        logout()

    users = db.query(models.User).all()
    payments = db.query(models.Payment).all()
    total_revenue = sum(
        payment.amount for payment in payments if "Paid" in payment.status
    )
    pending_dues = sum(
        payment.amount for payment in payments if payment.status == "Unpaid"
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
    col2.metric("Pending Dues", f"₹{pending_dues:,.2f}")
    col3.metric("Registered Accounts", len(users))

    tab1, tab2, tab3 = st.tabs(["Accounts", "Students & Staff", "Payments & Leave"])

    with tab1:
        st.subheader("Create User")
        new_username = st.text_input("Username")
        new_password = st.text_input("New password", type="password")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        new_role = st.selectbox("Role", ["student", "staff", "manager", "admin"])
        extra1 = st.text_input("Room / Job Title / Mess ID")
        extra2 = st.text_input("Mess ID (for student)")
        if st.button("Create account"):
            if (
                new_username
                and new_password
                and not db.query(models.User)
                .filter(models.User.username == new_username)
                .first()
            ):
                db.add(
                    models.User(
                        username=new_username,
                        password=new_password,
                        email=email,
                        phone_no=phone,
                        role=new_role,
                    )
                )
                if new_role == "student":
                    db.add(
                        models.Student(
                            username=new_username,
                            room_no=extra1 or "A-101",
                            mess_id=extra2 or "M1",
                        )
                    )
                elif new_role == "staff":
                    db.add(
                        models.MessStaff(
                            username=new_username,
                            job_title=extra1 or "Mess Worker",
                        )
                    )
                elif new_role == "manager":
                    db.add(
                        models.MessManager(
                            username=new_username,
                            manage_mess_id=extra1 or "M1",
                        )
                    )
                else:
                    db.add(
                        models.Admin(
                            username=new_username,
                            admin_level=int(extra1)
                            if extra1.isdigit()
                            else 1,
                        )
                    )
                db.commit()
                st.success("Account created.")
                st.rerun()
            else:
                st.warning("Enter a unique username and password.")

        st.subheader("Edit Contact Details")
        target_username = st.selectbox(
            "Account", [item.username for item in users], key="edit-user"
        )
        target = db.query(models.User).filter(
            models.User.username == target_username
        ).first()
        new_email = st.text_input("Email", value=target.email or "")
        new_phone = st.text_input("Phone", value=target.phone_no or "")
        if st.button("Update details"):
            target.email = new_email
            target.phone_no = new_phone
            db.commit()
            st.success("Details updated.")
            st.rerun()

    with tab2:
        left, right = st.columns(2)
        with left:
            st.subheader("Students")
            students = db.query(models.Student).all()
            for student in students:
                with st.container(border=True):
                    st.write(
                        f"**{student.username}** | Room {student.room_no} | "
                        f"Mess {student.mess_id} | {student.is_registered}"
                    )
                    if st.button(
                        "Remove",
                        key=f"remove-student-{student.username}",
                    ):
                        db.query(models.Student).filter(
                            models.Student.username == student.username
                        ).delete()
                        db.query(models.User).filter(
                            models.User.username == student.username
                        ).delete()
                        db.commit()
                        st.rerun()
        with right:
            st.subheader("Staff")
            staff = db.query(models.MessStaff).all()
            for member in staff:
                with st.container(border=True):
                    st.write(f"**{member.username}** | {member.job_title}")
                    if st.button(
                        "Remove",
                        key=f"remove-staff-{member.username}",
                    ):
                        db.query(models.MessStaff).filter(
                            models.MessStaff.username == member.username
                        ).delete()
                        db.query(models.User).filter(
                            models.User.username == member.username
                        ).delete()
                        db.commit()
                        st.rerun()

    with tab3:
        st.subheader("Payments")
        for payment in payments:
            with st.container(border=True):
                st.write(
                    f"#{payment.payment_id} | {payment.student_id} | "
                    f"{payment.month} | ₹{payment.amount:,.2f} | "
                    f"{payment.status} | {payment.warden_approved}"
                )
                if (
                    payment.warden_approved != "Signed & Approved"
                    and st.button(
                        "Sign & approve",
                        key=f"approve-payment-{payment.payment_id}",
                    )
                ):
                    payment.warden_approved = "Signed & Approved"
                    db.commit()
                    st.rerun()

        st.subheader("Leave Requests")
        leaves = db.query(models.Leave).all()
        for leave in leaves:
            with st.container(border=True):
                st.write(
                    f"{leave.staff_id}: {leave.start_date} to {leave.end_date} "
                    f"- {leave.reason} ({leave.status})"
                )
                decision = st.selectbox(
                    "Decision",
                    ["Approved by Admin", "Rejected by Admin", "Pending"],
                    key=f"admin-leave-{leave.leave_id}",
                )
                if st.button("Update", key=f"admin-leave-save-{leave.leave_id}"):
                    leave.status = decision
                    db.commit()
                    st.rerun()


def main():
    if "user" not in st.session_state:
        login()
        return

    db = session_db()
    try:
        role = st.session_state.user["role"]
        username = st.session_state.user["username"]
        if role == "student":
            student_dashboard(db, username)
        elif role == "manager":
            manager_dashboard(db, username)
        elif role == "staff":
            staff_dashboard(db, username)
        elif role == "admin":
            admin_dashboard(db, username)
    finally:
        db.close()


if __name__ == "__main__":
    main()
