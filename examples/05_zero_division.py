"""
Demonstration 05: Zero Division Crash & Exception Handling
RESONA Accessible Assistive Programming System
Showcases: Exception detection, tritone audio alarm, variable inspection at crash,
and AI-recommended guard conditions.
"""

def compute_average(total_score, num_students):
    # Potential ZeroDivisionError if num_students is 0
    return total_score / num_students

class_score = 450
student_count = 0

print(f"Calculating class average for score {class_score}...")
avg = compute_average(class_score, student_count)
print(f"Average grade: {avg}")
