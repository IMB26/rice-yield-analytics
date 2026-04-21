import pandas as pd

df = pd.read_csv("Merged_PSA_AreaHavested_Production.csv")
df.columns = [
    "Eco_Type", "Province", "Yr", "Sem",
    "Lvl", "Area", "Prod", "Yld"
]
df.to_csv("test_mismatched.csv", index=False)
print("Created test_mismatched.csv")
