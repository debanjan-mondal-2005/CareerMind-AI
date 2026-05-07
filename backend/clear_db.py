import sqlite3

conn = sqlite3.connect('careermind.db')
cursor = conn.cursor()
cursor.execute('DELETE FROM chat_history')
cursor.execute('DELETE FROM student_profiles')
cursor.execute('DELETE FROM onboarding_answers')
cursor.execute('DELETE FROM students')
conn.commit()
conn.close()
print('✓ All students and related data deleted successfully!')