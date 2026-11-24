"""
Demonstration 03: Bubble Sort Algorithm
RESONA Accessible Assistive Programming System
Showcases: Nested loop indentation sonification (outer loop depth 1, inner loop depth 2),
array comparison conditions, and variable swap mutations.
"""

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                # Swap elements
                temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
                swapped = True
        if not swapped:
            break
    return arr

sample_list = [64, 34, 25, 12, 22]
sorted_list = bubble_sort(sample_list)
print("Sorted array result:", sorted_list)
