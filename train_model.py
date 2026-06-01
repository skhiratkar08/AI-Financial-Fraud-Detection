import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle

# Load dataset
df = pd.read_csv(r"C:\Users\ASUS\Downloads\archive (3)\creditcard.csv")

# Features & target
X = df.drop("Class", axis=1)
y = df["Class"]

# Train model
model = RandomForestClassifier(n_estimators=50)
model.fit(X, y)

# Save model
pickle.dump(model, open("model.pkl", "wb"))

print("✅ Model trained successfully!")