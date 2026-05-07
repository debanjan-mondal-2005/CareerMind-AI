import sys
import os

# Add backend folder path so Python can import agents, llm, database
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import (
    create_tables,
    login_student,
    get_onboarding_answers,
    save_student_profile
)

from agents.profile_builder_agent import ProfileBuilderAgent


create_tables()

print("=== CareerMind AI Profile Builder Agent ===")

student_key = input("Enter student key: ")
password = input("Enter password: ")

login_result = login_student(student_key, password)

if not login_result["success"]:
    print(login_result["message"])
    exit()

student = login_result["student"]
student_id = student["id"]

answers = get_onboarding_answers(student_id)

if not answers:
    print("No onboarding answers found. Please complete onboarding first.")
    exit()

agent = ProfileBuilderAgent()
agent_result = agent.build_profile(answers)

if not agent_result["success"]:
    print("Profile Builder Agent failed.")
    print(agent_result)
    exit()

profile = agent_result["profile"]

result = save_student_profile(
    student_id=student_id,
    degree=profile.get("degree", ""),
    semester=profile.get("semester", ""),
    specialization=profile.get("specialization", ""),
    career_goal=profile.get("career_goal", ""),
    skills=", ".join(profile.get("skills", [])),
    weak_areas=", ".join(profile.get("weak_areas", [])),
    daily_study_hours=profile.get("daily_study_hours", "")
)

print("\nProfile Created Successfully!")
print(profile)
print(result)