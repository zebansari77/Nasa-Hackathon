
import pandas as pd
import os

# Get the project folder location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# NASA CSV file path
file_path = os.path.join(
    BASE_DIR, "nasa_data", "your_file.csv"
)

# Read CSV file
df = pd.read_csv(file_path)

print("NASA CSV Column Names:")
print(df.columns.tolist())

print("\nFirst 10 Rows:")
print(df.head(10).to_string(index=False))

print("\nDataset Information:")
df.info()
