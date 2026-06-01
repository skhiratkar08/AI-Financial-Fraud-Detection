import pickle

# Load saved model + vectorizer
model = pickle.load(open("sms_model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# Take user input
sms = input("Enter SMS: ")

# Convert text → numbers
sms_vector = vectorizer.transform([sms])

# Prediction
result = model.predict(sms_vector)

# Output
if result[0] == 1:
    print("🚨 Spam / Suspicious SMS")
else:
    print("✅ Normal SMS")