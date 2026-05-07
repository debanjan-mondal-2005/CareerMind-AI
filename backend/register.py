import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import create_tables, register_student
from mail.email_service import send_registration_email


create_tables()

print("=== CareerMind AI Student Registration ===")

first_name = input("Enter first name: ")
middle_name = input("Enter middle name optional: ")
last_name = input("Enter last name: ")
email = input("Enter email: ")
password = input("Set password: ")

result = register_student(
    first_name,
    middle_name,
    last_name,
    email,
    password
)

print("\nRegistration Result:")
print(result)

if result["success"]:
    student_key = result["student_key"]

    email_result = send_registration_email(
        to_email=email,
        first_name=first_name,
        student_key=student_key
    )

    print("\nEmail Result:")
    print(email_result)