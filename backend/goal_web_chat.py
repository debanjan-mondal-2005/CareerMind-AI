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

from agents.goal_web_agent import GoalAwareWebAgent


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

print("=== CareerMind AI Goal-Aware Web Connected Agent ===")

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

agent = GoalAwareWebAgent()

print(f"\nWelcome {student['first_name']}!")
print("This mode uses latest web data + local RAG according to your dream/career goal.")
print("Type exit to stop.\n")

while True:
    question = input("You: ")

    if question.lower() == "exit":
        print("Goodbye!")
        break

    result = agent.answer_with_web_and_rag(profile, question)

    print("\nCareerMind AI:")
    print(result["answer"])

    print("\nGenerated Web Search Query:")
    print(result["web_query"])

    print("\nWeb Sources Used:")
    for source in result["web_sources"]:
        print(f"- {source['title']}")
        print(f"  {source['url']}")

    print("\nLocal RAG Sources Used:")
    for source in result["rag_sources"]:
        print(f"- {source['source']} | Score: {source['score']:.4f}")

    if "LLM error" not in result["answer"] and '"error"' not in result["answer"]:
        try:
            combined_sources = {
                "web_sources": result["web_sources"],
                "rag_sources": result["rag_sources"],
                "web_query": result["web_query"]
            }

            save_chat_history(
                student_id=student_id,
                user_message=question,
                ai_response=result["answer"],
                sources_used=json.dumps(combined_sources)
            )

            print("\nChat history saved successfully.")

        except Exception as e:
            print(f"\nChat history not saved due to database error: {e}")

    else:
        print("\nChat not saved because LLM returned an error.")

    print("\n" + "-" * 80)