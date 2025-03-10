import os
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array

# Paths
TEST_DIR = 'datasets/test/'
MODEL_PATH = 'models/tumor_detection_model.h5'
IMG_SIZE = (128, 128)

# Load test data
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
                img_array = img_to_array(img) / 255.0
                images.append(img_array)
                labels.append(class_num)
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
    return np.array(images), np.array(labels)

# Load test data
X_test, y_test = load_data(TEST_DIR)
print(f"Loaded {len(X_test)} test images")

# Load model
model = tf.keras.models.load_model(MODEL_PATH)

# Evaluate
loss, accuracy = model.evaluate(X_test, y_test)
print(f"Test Accuracy: {accuracy * 100:.2f}%")

# Predict on a single image (example)
sample_img = X_test[0:1]  # First image
prediction = model.predict(sample_img)
print("Prediction (1 = Tumor, 0 = No Tumor):", "Tumor" if prediction[0][0] > 0.5 else "No Tumor")