import pandas as pd
import os

class CarDataTransformer:
    """
    A class to handle loading and transforming car data from CSV.
    Follows SOLID principles: Single Responsibility for each method,
    Open for extension (can subclass to add new transformations).
    """

    def __init__(self, csv_path: str):
        """
        Initialize the transformer with the path to the CSV file.

        Args:
            csv_path (str): Path to the CSV file containing car data.
        """
        self.csv_path = csv_path
        self.df = None

    def load_data(self) -> None:
        """
        Load the data from the CSV file into a pandas DataFrame.
        """
        self.df = pd.read_csv(self.csv_path)

    def get_origin_mapping(self) -> dict:
        """
        Return the mapping dictionary from car make to origin country.

        Returns:
            dict: Mapping of car makes to their origin countries.
        """
        return {
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

    def add_origin_country(self) -> None:
        """
        Add a new column 'Origin_Country' based on the 'Make' column using the mapping.
        """
        mapping = self.get_origin_mapping()
        self.df['Origin_Country'] = self.df['Make'].map(mapping).fillna('')

    def rename_origin_to_region(self) -> None:
        """
        Rename the 'Origin' column to 'Origin_Region'.
        """
        self.df = self.df.rename(columns={"Origin": "Origin_Region"})

    def select_columns(self, columns: list) -> None:
        """
        Select only the specified columns from the DataFrame.

        Args:
            columns (list): List of column names to keep.
        """
        self.df = self.df[columns]

    def get_shape(self) -> tuple:
        """
        Get the shape of the DataFrame.

        Returns:
            tuple: (number of rows, number of columns)
        """
        return self.df.shape

    def get_head(self, n: int = 5) -> pd.DataFrame:
        """
        Get the first n rows of the DataFrame.

        Args:
            n (int): Number of rows to return. Default is 5.

        Returns:
            pd.DataFrame: First n rows of the DataFrame.
        """
        return self.df.head(n)


if __name__ == "__main__":
    # Determine the path to the CSV file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "csv", "cars.csv")

    # Create an instance of the transformer
    transformer = CarDataTransformer(csv_path)

    # Load the data
    transformer.load_data()

    # Apply transformations
    transformer.add_origin_country()
    transformer.rename_origin_to_region()
    transformer.select_columns(['Make', 'Model', 'Origin_Region', 'Origin_Country'])

    # Output results
    print(transformer.get_shape())  # should print (428, 4)
    print(transformer.get_head())