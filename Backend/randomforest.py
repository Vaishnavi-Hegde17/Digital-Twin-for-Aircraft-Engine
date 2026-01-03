# ===================== IMPORTS =====================
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

sns.set_style("whitegrid")

# ===================== LOAD DATA =====================
df = pd.read_csv("adour_engine_stable_ml_dataset.csv")

# ===================== AIRCRAFT-WISE SPLIT =====================
train_aircraft = ["HAL-HJT-01", "HAL-HJT-02", "HAL-HJT-03", "HAL-HJT-04"]
test_aircraft  = ["HAL-HJT-05", "HAL-HJT-06"]

train_df = df[df["Aircraft_ID"].isin(train_aircraft)].copy()
test_df  = df[df["Aircraft_ID"].isin(test_aircraft)].copy()

# ===================== FEATURE SELECTION =====================
drop_cols = [
    "Timestamp",
    "Aircraft_ID",
    "Engine_Model",
    "Health",
    "Severity"   # latent ground truth (DO NOT use)
]

X_train = train_df.drop(columns=drop_cols)
X_test  = test_df.drop(columns=drop_cols)

y_train = train_df["Health"]
y_test  = test_df["Health"]

# ===================== ONE-HOT ENCODING (SAFE) =====================
X_train = pd.get_dummies(X_train, columns=["Phase"])
X_test  = pd.get_dummies(X_test, columns=["Phase"])

# Align columns (THIS FIXES YOUR ERROR)
X_train, X_test = X_train.align(X_test, join="left", axis=1, fill_value=0)

# ===================== LABEL ENCODING =====================
le = LabelEncoder()
y_train_enc = le.fit_transform(y_train)
y_test_enc  = le.transform(y_test)

# ===================== FEATURE SCALING =====================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# ===================== MODEL =====================
rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=14,
    class_weight="balanced",
    random_state=42
)

rf.fit(X_train_scaled, y_train_enc)

# ===================== PREDICTION =====================
y_pred = rf.predict(X_test_scaled)

# ===================== EVALUATION =====================
print("=== Classification Report ===")
print(classification_report(
    y_test_enc,
    y_pred,
    target_names=le.classes_
))

# ===================== CONFUSION MATRIX =====================
cm = confusion_matrix(y_test_enc, y_pred)

plt.figure(figsize=(5,4))
sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=le.classes_,
    yticklabels=le.classes_
)
plt.title("Aircraft-wise Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

# ===================== FEATURE IMPORTANCE =====================
feature_importance = pd.DataFrame({
    "Feature": X_train.columns,
    "Importance": rf.feature_importances_
}).sort_values(by="Importance", ascending=False)

print("\n=== Top 10 Important Features ===")
print(feature_importance.head(10))

# ===================== SAVE MODEL & PREPROCESSORS =====================
import joblib

joblib.dump(rf, "rf_engine_health_model.pkl")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(le, "label_encoder.pkl")
joblib.dump(X_train.columns.tolist(), "model_features.pkl")

print(" Random Forest model and preprocessors saved successfully")
