import pandas as pd

# Step 1: Create sample dataset
data = {
    "id": [1, 2, 3, 4, 5],
    "name": ["John", "Mary", "David", "Lisa", "James"],
    "age": [28, 35, 42, 30, 50],
    "salary": [40000, 55000, 65000, 48000, 70000],
    "department": ["IT", "HR", "Finance", "IT", "Finance"]
}

df = pd.DataFrame(data)

# Step 2: Create new variable (like DATA step)
df["age_group"] = df["age"].apply(
    lambda x: "Senior" if x >= 40 else "Junior"
)

# Step 3: Print dataset
print("Employees Updated:")
print(df)

# Step 4: Summary statistics (like PROC MEANS)
summary = df.groupby("age_group")["salary"].mean()
print("\nAverage Salary by Age Group:")
print(summary)

# Step 5: Sort data (like PROC SORT)
sorted_df = df.sort_values(by="salary", ascending=False)

# Step 6: Print sorted data
print("\nSorted Data (by salary descending):")
print(sorted_df)

# Step 7: Frequency count (like PROC FREQ)
freq = df["department"].value_counts()
print("\nDepartment Frequency:")
print(freq)