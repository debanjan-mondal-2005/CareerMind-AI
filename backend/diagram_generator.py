import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.diagram_agent import DiagramAgent


print("=== CareerMind AI Diagram Generator Agent ===")

agent = DiagramAgent()

while True:
    user_request = input("\nEnter diagram request or type exit: ")

    if user_request.lower() == "exit":
        print("Goodbye!")
        break

    result = agent.generate_diagram(user_request)

    print("\nGenerated Mermaid Diagram Code:\n")
    print(result["diagram_code"])

    print("\nSources Used:")
    for source in result["sources"]:
        print(f"- {source['source']} | Score: {source['score']:.4f}")

    print("\n" + "-" * 80)