import numpy as np
import matplotlib.pyplot as plt

# Generate test data for 10 surface measurement points
num_points = 10
x_labels = [f"P{i+1}" for i in range(num_points)]  # Label for surface points

# Randomized min/max/avg measurements
avg_value = np.random.uniform(0, 1, num_points)  # Average height
min_value = avg_value - np.random.uniform(0.1, 0.2, num_points)  # Minimum
max_value = avg_value + np.random.uniform(0.1, 0.2, num_points)  # Maximum

# Shim values (material to add)
avg_shim = np.random.uniform(0, 0.3, num_points)
min_shim = avg_shim - np.random.uniform(0, 0.1, num_points)
max_shim = avg_shim + np.random.uniform(0, 0.1, num_points)

# Scrape values (material to remove)
avg_scrape = np.random.uniform(0, 0.3, num_points)
min_scrape = avg_scrape - np.random.uniform(0, 0.1, num_points)
max_scrape = avg_scrape + np.random.uniform(0, 0.1, num_points)

# Plotting the box plot for measurements
plt.figure(figsize=(10, 5))
plt.errorbar(x_labels, avg_value, yerr=[avg_value - min_value, max_value - avg_value], fmt='o', label="Measured (Min/Max)")
plt.errorbar(x_labels, avg_value, yerr=[avg_shim - min_shim, max_shim - avg_shim], fmt='s', label="Shim (Min/Max)", color='green')
plt.errorbar(x_labels, avg_value, yerr=[avg_scrape - min_scrape, max_scrape - avg_scrape], fmt='^', label="Scrape (Min/Max)", color='red')

plt.xlabel("Surface Points")
plt.ylabel("Height Deviation")
plt.title("Surface Measurement Variability with Shim & Scrape")
plt.legend()
plt.grid()
plt.show()
