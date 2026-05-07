import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import (
    create_tables,
    login_student,
    get_connection,
    save_chat_history
)

from agents.specialized_agents import (
    SkillGapAgent,
    CareerRoadmapAgent,
    ProjectRecommendationAgent,
    InterviewPreparationAgent
)


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


def print_sources(sources):
    print("\nSources Used:")
    for source in sources:
        print(f"- {source['source']} | Score: {source['score']:.4f}")


create_tables()

print("=== CareerMind AI Multi-Agent System ===")

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

print(f"\nWelcome {student['first_name']}!")

skill_gap_agent = SkillGapAgent()
roadmap_agent = CareerRoadmapAgent()
project_agent = ProjectRecommendationAgent()
interview_agent = InterviewPreparationAgent()

while True:
    print("\nChoose Agent:")
    print("1. Skill Gap Agent")
    print("2. Career Roadmap Agent")
    print("3. Project Recommendation Agent")
    print("4. Interview Preparation Agent")
    print("5. Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        result = skill_gap_agent.analyze(profile)

    elif choice == "2":
        result = roadmap_agent.generate_roadmap(profile)

    elif choice == "3":
        result = project_agent.recommend_projects(profile)

    elif choice == "4":
        result = interview_agent.prepare_interview(profile)

    elif choice == "5":
        print("Goodbye!")
        break

    else:
        print("Invalid choice.")
        continue

    print(f"\n{result['agent']} Output:")
    print(result["answer"])

    print_sources(result["sources"])
    
    if "LLM error" not in result["answer"] and '"error"' not in result["answer"]:
        try:
            save_chat_history(
                student_id=student_id,
                user_message=f"Used {result['agent']}",
                ai_response=result["answer"],
                sources_used=json.dumps(result["sources"])
            )
            print("\nChat history saved successfully.")

        except Exception as e:
            print(f"\nChat history not saved due to database error: {e}")

    else:
        print("\nChat not saved because LLM returned an error.")

print("\n" + "-" * 80)