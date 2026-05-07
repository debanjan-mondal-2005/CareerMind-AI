from database.db import create_tables, login_student, save_onboarding_answer

create_tables()

print("=== CareerMind AI Onboarding ===")

student_key = input("Enter student key: ")
password = input("Enter password: ")

login_result = login_student(student_key, password)

if not login_result["success"]:
    print(login_result["message"])
    exit()

student = login_result["student"]
student_id = student["id"]

print(f"\nWelcome {student['first_name']}! Let's create your career profile.\n")

questions = [
    "Which degree/class are you studying?",
    "Which semester/year are you in?",
    "What is your specialization?",
    "What do you want to become?",
    "Which programming languages or skills do you know?",
    "Which topics are weak for you?",
    "How many hours can you study daily?"
]

for question in questions:
    print(question)
    answer = input("Your answer: ")

    save_onboarding_answer(student_id, question, answer)

print("\nOnboarding completed successfully.")
print("Your answers are saved in the database.")