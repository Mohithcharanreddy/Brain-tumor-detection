import os
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import load_img, img_to_array

# Paths
TRAIN_DIR = 'datasets/train/'
MODEL_PATH = 'models/tumor_detection_model.h5'
IMG_SIZE = (128, 128)  # Resize images to 128x128

# Load and preprocess data
def load_data(directory):
    images = []
    labels = []
    for label in ['tumor', 'no_tumor']:
        path = os.path.join(directory, label)
        class_num = 1 if label == 'tumor' else 0
        for img_name in os.listdir(path):
            img_path = os.path.join(path, img_name)
            try:
                img = load_img(img_path, target_size=IMG_SIZE)
                img_array = img_to_array(img) / 255.0  # Normalize to [0, 1]
                images.append(img_array)
                labels.append(class_num)
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
    return np.array(images), np.array(labels)

# Load training data
X_train, y_train = load_data(TRAIN_DIR)
print(f"Loaded {len(X_train)} training images")

# Build CNN model
model = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(128, 128, 3)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(1, activation='sigmoid')  # Binary classification
])

model.compile(optimizer='adam',
              loss='binary_crossentropy',
              metrics=['accuracy'])

# Train the model
model.fit(X_train, y_train, epochs=10, batch_size=32, validation_split=0.2)

# Save the model
os.makedirs('models', exist_ok=True)
model.save(MODEL_PATH)
print(f"Model saved to {MODEL_PATH}")