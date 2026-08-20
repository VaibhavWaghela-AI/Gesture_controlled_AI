import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split

# 1. Load Data
print("Loading 'gesture_data_final.csv'...")
try:
    data = pd.read_csv("gesture_data_final.csv")
except FileNotFoundError:
    print("ERROR: CSV file not found! Run the Collector first.")
    exit()

X = data.iloc[:, 1:].values
y = data.iloc[:, 0].values

# 2. Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 3. Model Architecture (Updated for 7 Classes)
model = tf.keras.models.Sequential([
    tf.keras.layers.Input(shape=(42,)),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(64, activation='relu'),
    # OUTPUT LAYER: 7 neurons for 7 classes
    tf.keras.layers.Dense(7, activation='softmax') 
])

# 4. Compile
model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# 5. Train
print("Training Neural Network...")
model.fit(X_train, y_train, epochs=25, batch_size=32, validation_data=(X_test, y_test))

# 6. Save
model.save("gesture_model_7class.h5")
print(">>> SUCCESS! Model saved as 'gesture_model_7class.h5'")