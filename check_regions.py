import pandas as pd
from data_processor import load_and_validate, clean_data

df, is_valid, message = load_and_validate("Merged_PSA_AreaHavested_Production.csv")
df = clean_data(df)

regions = df[df["level"] == "Region"]["location"].unique()
for r in sorted(regions):
    print(r)
