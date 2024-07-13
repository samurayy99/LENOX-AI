import pandas as pd

# Load the config.csv file
config_path = 'data/config.csv'
df = pd.read_csv(config_path)

# Add new columns if they do not exist
new_columns = ['trend_strength', 'gain_1d', 'gain_1w', 'gain_1m']
for column in new_columns:
    if column not in df.columns:
        df[column] = 0  # Default value or you can calculate the value
        print(f"Column '{column}' added.")
    else:
        print(f"Column '{column}' already exists.")

# Save the updated config.csv
df.to_csv(config_path, index=False)
