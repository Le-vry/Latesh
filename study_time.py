import matplotlib.pyplot as plt
import numpy as np

# Mock data
study_time = np.array([0, 1, 2, 3, 4])
grades = ['E', 'D', 'C', 'B', 'A']
grade_numeric = np.array([1, 2.5, 3.5, 4.5, 5])  # Adjusted for steeper improvement

# Create line graph
plt.figure(figsize=(6, 4.5))
plt.plot(study_time, grade_numeric, marker='o', linestyle='-', linewidth=3, markersize=14, color='#1f77b4')

# Customize the chart
plt.title('Studietid vs Betyg', fontsize=18, fontweight='bold', pad=16)
plt.xlabel('Studietid (timmar/dag)', fontsize=18, labelpad=16)
plt.ylabel('Betyg', fontsize=18, labelpad=18)
plt.xlim(-0.5, 4.5)
plt.ylim(0.5, 6)

# Customize x-axis ticks
plt.xticks(study_time, fontsize=16)

# Customize y-axis ticks
plt.yticks(grade_numeric, grades, fontsize=16)

# Add labels to each point
for x, y, grade in zip(study_time, grade_numeric, grades):
    plt.text(x, y+0.2, grade, ha='center', va='bottom', fontsize=16, fontweight='bold')

# Add a grid for better readability
plt.grid(True, linestyle='--', alpha=0.7)

# Improve layout
plt.tight_layout()

# Save the figure
plt.savefig('study_time.png', dpi=300, bbox_inches='tight')
plt.close()