import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_style("whitegrid")

df = pd.read_csv("adour_engine_stable_ml_dataset.csv")
plt.figure(figsize=(6,4))
sns.countplot(data=df, x="Health", order=["NORMAL","WARNING","CRITICAL"])
plt.title("Fleet Health Status Distribution")
plt.xlabel("Health State")
plt.ylabel("Number of Samples")
plt.show()