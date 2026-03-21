import pandas as pd
import os

# Step 1: Load full dataset (exported from SAS)
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "csv", "cars.csv")
df = pd.read_csv(csv_path) 

# Step 2: Define the Make → Origin_Country mapping
origin_mapping = {
    # Japan
    'Acura': 'Japan', 'Honda': 'Japan', 'Infiniti': 'Japan', 'Isuzu': 'Japan', 'Lexus': 'Japan',
    'Mazda': 'Japan', 'Mitsubishi': 'Japan', 'Nissan': 'Japan', 'Scion': 'Japan', 'Subaru': 'Japan',
    'Suzuki': 'Japan', 'Toyota': 'Japan',
    # South Korea
    'Hyundai': 'South Korea', 'Kia': 'South Korea',
    # Germany
    'Audi': 'Germany', 'BMW': 'Germany', 'Mercedes-Benz': 'Germany', 'Volkswagen': 'Germany', 'Porsche': 'Germany',
    # England
    'Jaguar': 'England', 'Land Rover': 'England', 'MINI': 'England',
    # Sweden
    'Saab': 'Sweden', 'Volvo': 'Sweden',
    # USA
    'Buick': 'United States of America', 'Cadillac': 'United States of America', 'Chevrolet': 'United States of America',
    'Chrysler': 'United States of America', 'Dodge': 'United States of America', 'Ford': 'United States of America',
    'GMC': 'United States of America', 'Hummer': 'United States of America', 'Jeep': 'United States of America',
    'Lincoln': 'United States of America', 'Mercury': 'United States of America', 'Oldsmobile': 'United States of America',
    'Pontiac': 'United States of America', 'Saturn': 'United States of America'
}

# Step 3: Map Make to Origin_Country
df['Origin_Country'] = df['Make'].map(origin_mapping).fillna('')  # fillna = OTHERWISE

# Step 4: Rename Origin column to Origin_Region
df = df.rename(columns={"Origin": "Origin_Region"})

# Step 5: Keep only the columns used in SAS program
df = df[['Make', 'Model', 'Origin_Region', 'Origin_Country']]

# Step 6: Check shape
print(df.shape)  # should print (428, 4)

# Step 7: Preview first few rows
print(df.head())