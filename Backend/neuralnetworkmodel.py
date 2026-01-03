# ===================== IMPORTS =====================
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

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

# ===================== NEURAL NETWORK =====================
model = Sequential([
    Dense(64, activation="relu", input_shape=(X_train_scaled.shape[1],)),
    Dropout(0.3),
    Dense(32, activation="relu"),
    Dropout(0.2),
    Dense(3, activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

early_stop = EarlyStopping(
    monitor="val_loss",
    patience=5,
    restore_best_weights=True
)

history = model.fit(
    X_train_scaled,
    y_train_enc,
    validation_split=0.2,
    epochs=50,
    batch_size=64,
    callbacks=[early_stop],
    verbose=1
)

# ===================== PREDICTION =====================
y_pred_prob = model.predict(X_test_scaled)
y_pred = np.argmax(y_pred_prob, axis=1)

# ===================== EVALUATION =====================
print("=== Neural Network Classification Report ===")
print(classification_report(
    y_test_enc,
    y_pred,
    target_names=le.classes_
))

# ===================== CONFUSION MATRIX =====================
cm = confusion_matrix(y_test_enc, y_pred)

plt.figure(figsize=(5,4))
sns.heatmap(
    cm, annot=True, fmt="d", cmap="Oranges",
    xticklabels=le.classes_, yticklabels=le.classes_
)
plt.title("Neural Network Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

# Save neural network
model.save("nn_engine_health_model.h5")


print("Neural Network model saved successfully")
