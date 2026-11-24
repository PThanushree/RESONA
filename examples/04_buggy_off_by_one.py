"""
Demonstration 04: Buggy Off-by-One Loop (IndexError)
RESONA Accessible Assistive Programming System
Showcases: Dissonant runtime error chord, automatic crash site jump,
and AI-assisted bug diagnosis explaining that 0-indexed lists cannot be accessed up to len(items).
"""

items = [100, 200, 300, 400]
total = 0

# Intentional off-by-one bug: using <= len(items) instead of < len(items)
for i in range(len(items) + 1):
    val = items[i]
    total += val
    print(f"Added item {i}: {val}, running total: {total}")

print("Final cumulative total:", total)
