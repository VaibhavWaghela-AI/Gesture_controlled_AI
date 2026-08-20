import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.utils import to_categorical
import joblib # To save the scaler

# --- CONFIGURATION ---
CSV_FILE = 'imu_data.csv'
MODEL_FILE = 'imu_model.h5'
SCALER_FILE = 'scaler.save' # We need to save the math scaler too

print("--- SMART TRAINING STARTED ---")

# 1. Load Data
try:
    data = pd.read_csv(CSV_FILE)
    print(f"Original Data Size: {len(data)} rows")
except FileNotFoundError:
    print("ERROR: CSV not found!")
    exit()

# 2. THE MAGIC FIX: FILTER OUT "SILENCE" FROM GESTURES
# We calculate 'Gyro Magnitude' to measure how fast the hand is moving
# If the hand is moving slowly, but labeled as a Flick/Twist, we DELETE it.

# Calculate Gyro Magnitude (Energy)
# Assuming columns are: label, ax, ay, az, gx, gy, gz
# We use columns 4, 5, 6 (gx, gy, gz)
data['gyro_energy'] = np.sqrt(data.iloc[:, 4]**2 + data.iloc[:, 5]**2 + data.iloc[:, 6]**2)

# Define a "Movement Threshold" (Adjust based on your sensor)
# For raw MPU6050 data, 20 is usually a good cut-off for "noise"
MOVEMENT_THRESHOLD = 100.0

print("\n--- CLEANING DATA ---")
cleaned_data = []

for label in data['label'].unique():
    subset = data[data['label'] == label]
    
    if label == 0:
        # For IDLE (0), we KEEP low energy data (sitting still)
        # We assume you recorded idle correctly.
        clean_subset = subset
        print(f"Label 0 (IDLE): Kept {len(clean_subset)} rows (No Filtering)")
    else:
        # For GESTURES (1-5), we ONLY keep High Energy rows
        # This removes the "waiting time" between flicks
        clean_subset = subset[subset['gyro_energy'] > MOVEMENT_THRESHOLD]
        print(f"Label {label}: Kept {len(clean_subset)} rows (Removed {len(subset) - len(clean_subset)} 'silent' rows)")
    
    cleaned_data.append(clean_subset)

# Recombine
data = pd.concat(cleaned_data)
print(f"Cleaned Data Size: {len(data)} rows")

# 3. Prepare Inputs
X = data.iloc[:, 1:7].values.astype(float) # ax, ay, az, gx, gy, gz
y = data.iloc[:, 0].values.astype(int)     # label

# 4. SCALE THE DATA (Crucial for Neural Networks)
# This squeezes big numbers (like 15000) into small numbers (0-1)
scaler = StandardScaler()
X = scaler.fit_transform(X)
joblib.dump(scaler, SCALER_FILE) # Save this to use in the App
print(f"Scaler saved to {SCALER_FILE}")

# 5. Split Data
y_cat = to_categorical(y, num_classes=6)
X_train, X_test, y_train, y_test = train_test_split(X, y_cat, test_size=0.2, random_state=42)

# 6. Stronger Model
model = Sequential([
    Dense(128, activation='relu', input_shape=(6,)), # More neurons
    Dropout(0.3),
    Dense(64, activation='relu'),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dense(6, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# 7. Train
print("\n--- TRAINING NEURAL NETWORK ---")
history = model.fit(X_train, y_train, 
                    epochs=40, 
                    batch_size=32, 
                    validation_data=(X_test, y_test),
                    verbose=1)

model.save(MODEL_FILE)
print(f"\nModel saved to {MODEL_FILE}")

# Check Accuracy
loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\nFINAL ACCURACY: {acc*100:.2f}%")