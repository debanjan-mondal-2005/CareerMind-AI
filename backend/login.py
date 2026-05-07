from database.db import create_tables, login_student

create_tables()

print("=== CareerMind AI Student Login ===")

student_key = input("Enter student key: ")
password = input("Enter password: ")

result = login_student(student_key, password)

print("\nResult:")
print(result)