import pandas as pd
print("Extracting 5000 real rows from the giant file. Please wait...")
df = pd.read_json("Electronics_5.json", lines=True, nrows=5000)
df.to_csv("fast_amazon.csv", index=False)
print("Done! Fast dataset created successfully.")
