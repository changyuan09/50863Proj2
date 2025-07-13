import matplotlib.pyplot as plt

# Data
implementations = ["Latest Version", "Second Version", "Stop_and_Go"]
goodputs = [47893, 31756, 4899]

# Distinct colors for the three bars (choose any you like)
colors = ["red", "green", "blue"]

# Create the bar chart
plt.bar(implementations, goodputs, color=colors)

# Add labels and title
plt.xlabel("Implementation")
plt.ylabel("Goodput")
plt.title("Goodput Comparison")

# Display the plot
plt.show()


