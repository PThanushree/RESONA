"""
Demonstration 06: Student Grade Evaluator
RESONA Accessible Assistive Programming System
Showcases: Multi-branch if/elif/else structure and corresponding sonification earcons.
"""

def evaluate_grade(score):
    if score >= 90:
        return "A (Distinction)"
    elif score >= 75:
        return "B (First Class)"
    elif score >= 60:
        return "C (Second Class)"
    elif score >= 50:
        return "D (Pass Class)"
    else:
        return "F (Needs Improvement)"

scores = [94, 82, 67, 53, 41]
for s in scores:
    grade = evaluate_grade(s)
    print(f"Score {s} yields grade: {grade}")
