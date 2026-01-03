# ===================== IMPORTS =====================
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier


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
    "Severity"
]

X_train = train_df.drop(columns=drop_cols)
X_test  = test_df.drop(columns=drop_cols)

y_train = train_df["Health"]
y_test  = test_df["Health"]

# ===================== ONE-HOT ENCODING =====================
X_train = pd.get_dummies(X_train, columns=["Phase"])
X_test  = pd.get_dummies(X_test, columns=["Phase"])

X_train, X_test = X_train.align(X_test, join="left", axis=1, fill_value=0)

# ===================== LABEL ENCODING =====================
le = LabelEncoder()
y_train_enc = le.fit_transform(y_train)
y_test_enc  = le.transform(y_test)

# ===================== FEATURE SCALING =====================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# ===================== XGBOOST MODEL =====================
xgb = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softprob",
    num_class=3,
    eval_metric="mlogloss",
    random_state=42
)

xgb.fit(X_train_scaled, y_train_enc)

# ===================== PREDICTION =====================
y_pred = xgb.predict(X_test_scaled)

# ===================== EVALUATION =====================
print("=== XGBoost Classification Report ===")
print(classification_report(
    y_test_enc,
    y_pred,
    target_names=le.classes_
))

# ===================== CONFUSION MATRIX =====================
cm = confusion_matrix(y_test_enc, y_pred)

plt.figure(figsize=(5,4))
sns.heatmap(
    cm, annot=True, fmt="d", cmap="Greens",
    xticklabels=le.classes_, yticklabels=le.classes_
)
plt.title("XGBoost Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()


# ===================== SAVE MODEL & PREPROCESSORS =====================
import joblib

joblib.dump(xgb, "xg_engine_health_model.pkl")
joblib.dump(scaler, "xg_scaler.pkl")
joblib.dump(le, "xg_label_encoder.pkl")
joblib.dump(X_train.columns.tolist(), "xg_model_features.pkl")

print("model and preprocessors saved successfully")
