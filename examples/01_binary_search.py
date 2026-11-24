"""
Demonstration 01: Binary Search Algorithm
RESONA Accessible Assistive Programming System
Showcases: While loops, multi-way branch earcons, and variable changes (low, high, mid).
"""

def binary_search(arr, target):
    low = 0
    high = len(arr) - 1
    
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
            
    return -1

# Sample execution
numbers = [2, 5, 8, 12, 16, 23, 38, 56, 72]
search_key = 23
result_index = binary_search(numbers, search_key)

print(f"Target {search_key} located at array index: {result_index}")
