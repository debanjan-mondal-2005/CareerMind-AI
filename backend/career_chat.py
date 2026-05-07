import sys
import os
import json

# Add backend folder path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import (
    create_tables,
    login_student,
    get_connection,
    save_chat_history
)

from agents.career_mentor_agent import CareerMentorAgent


def get_student_profile(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM student_profiles
    WHERE student_id = ?
    """, (student_id,))

    profile = cursor.fetchone()
    conn.close()

    if not profile:
        return None

    return {
        "degree": profile["degree"],
        "semester": profile["semester"],
        "specialization": profile["specialization"],
        "career_goal": profile["career_goal"],
        "skills": profile["skills"],
        "weak_areas": profile["weak_areas"],
        "daily_study_hours": profile["daily_study_hours"]
    }


create_tables()

print("=== CareerMind AI Career Mentor Chat ===")

student_key = input("Enter student key: ")
password = input("Enter password: ")

login_result = login_student(student_key, password)

if not login_result["success"]:
    print(login_result["message"])
    exit()

student = login_result["student"]
student_id = student["id"]

profile = get_student_profile(student_id)

if not profile:
    print("Student profile not found. Please complete onboarding and profile builder first.")
    exit()

print(f"\nWelcome {student['first_name']}! Ask your career question.")
print("Type 'exit' to stop.\n")

agent = CareerMentorAgent()

while True:
    user_question = input("You: ")

    if user_question.lower() == "exit":
        print("Goodbye!")
        break

    result = agent.answer_question(profile, user_question)
    
    if '"error"' not in result["answer"]:
        save_chat_history(
        student_id=student_id,
        user_message=user_question,
        ai_response=result["answer"],
        sources_used=json.dumps(result["sources"])
    )
    else:
        print("\nChat not saved because LLM returned an error.")