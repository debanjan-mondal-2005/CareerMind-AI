import sqlite3
import os

# Get the absolute path to the backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(backend_dir, 'careermind.db')

if not os.path.exists(db_path):
    print(f"⚠️ Database not found at: {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history')
    cursor.execute('DELETE FROM student_profiles')
    cursor.execute('DELETE FROM onboarding_answers')
    cursor.execute('DELETE FROM students')
    conn.commit()
    conn.close()
    print('[SUCCESS] All students and related data deleted successfully from the correct database!')