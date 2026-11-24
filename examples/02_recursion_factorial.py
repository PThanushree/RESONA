"""
Demonstration 02: Recursive Factorial Computation
RESONA Accessible Assistive Programming System
Showcases: Call stack depth escalation, recursive function entry earcon, and descending return cadence.
"""

def factorial(n):
    # Base case: depth reached
    if n <= 1:
        return 1
    # Recursive step
    sub_problem = factorial(n - 1)
    return n * sub_problem

num = 4
answer = factorial(num)
print(f"The factorial of {num} is {answer}")
