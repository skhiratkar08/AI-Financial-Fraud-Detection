import pickle
import pandas as pd

# Load trained model
model = pickle.load(open("model.pkl", "rb"))

def predict_fraud(data):
    # Convert to DataFrame
    df = pd.DataFrame([data])

    # Ensure all features exist (V1–V28)
    for i in range(1, 29):
        col = f"V{i}"
        if col not in df:
            df[col] = 0

    # Add Time column
    df["Time"] = 0

    # Arrange columns properly
    cols = ["Time"] + [f"V{i}" for i in range(1,29)] + ["Amount"]
    df = df.reindex(columns=cols, fill_value=0)

    # Prediction
    pred = model.predict(df)[0]

    return "Fraud" if pred == 1 else "Normal"