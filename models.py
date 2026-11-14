from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True, index=True)
    password = Column(String, nullable=False)
    email = Column(String)
    phone_no = Column(String)
    role = Column(String, nullable=False)  # 'student', 'manager', 'staff', 'admin'

class Student(Base):
    __tablename__ = 'students'
    username = Column(String, ForeignKey('users.username', ondelete="CASCADE"), primary_key=True)
    room_no = Column(String)
    mess_id = Column(String)
    is_registered = Column(String, default="Approved")  # Pending, Approved, Rejected

    user = relationship("User")
    complaints = relationship("Complaint", back_populates="student", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="student", cascade="all, delete-orphan")

class MessManager(Base):
    __tablename__ = 'mess_managers'
    username = Column(String, ForeignKey('users.username', ondelete="CASCADE"), primary_key=True)
    manage_mess_id = Column(String)

    user = relationship("User")

class MessStaff(Base):
    __tablename__ = 'mess_staff'
    username = Column(String, ForeignKey('users.username', ondelete="CASCADE"), primary_key=True)
    job_title = Column(String)

    user = relationship("User")
    leaves = relationship("Leave", back_populates="staff", cascade="all, delete-orphan")

class Admin(Base):
    __tablename__ = 'admins'
    username = Column(String, ForeignKey('users.username', ondelete="CASCADE"), primary_key=True)
    admin_level = Column(Integer)

    user = relationship("User")

class Menu(Base):
    __tablename__ = 'menus'
    menu_id = Column(Integer, primary_key=True, index=True)
    day = Column(String, unique=True)
    breakfast = Column(Text)
    lunch = Column(Text)
    dinner = Column(Text)

class Complaint(Base):
    __tablename__ = 'complaints'
    complaint_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, ForeignKey('students.username'))
    text = Column(Text)
    date = Column(Date)
    status = Column(String, default="Pending")  # Pending, Resolved, Rejected

    student = relationship("Student", back_populates="complaints")

class Leave(Base):
    __tablename__ = 'leaves'
    leave_id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(String, ForeignKey('mess_staff.username'))
    start_date = Column(Date)
    end_date = Column(Date)
    reason = Column(Text)
    status = Column(String, default="Pending")  # Pending, Approved, Rejected

    staff = relationship("MessStaff", back_populates="leaves")

class Payment(Base):
    __tablename__ = 'payments'
    payment_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, ForeignKey('students.username'))
    month = Column(String)
    amount = Column(Float)
    date = Column(Date)
    status = Column(String, default="Unpaid")  # Unpaid, Paid, Verified
    warden_approved = Column(String, default="Pending")  # Maps to DFD Level 1 Warden/MMC approval

    student = relationship("Student", back_populates="payments")

# DFD Level 1 Data Stores: Attendance and Stock
class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(String)
    role = Column(String)
    date = Column(Date)
    status = Column(String)  # Present, Absent

class Stock(Base):
    __tablename__ = 'stocks'
    stock_id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, unique=True)
    quantity = Column(Float)
    unit = Column(String)
    alert_threshold = Column(Float)