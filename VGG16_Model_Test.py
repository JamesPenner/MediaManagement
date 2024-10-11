import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.callbacks import TensorBoard, EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
from PIL import Image
import logging
import shutil
import csv
import glob

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

Image.MAX_IMAGE_PIXELS = None

# Paths
train_dir = 'D:/Data Analysis/Images/train'
validation_dir = 'D:/Data Analysis/Images/validation'
test_dir = 'D:/Data Analysis/Images/test'
base_model_path = 'D:/Data Analysis/Images/Python/vgg16_model.keras'
model_save_path = 'D:/Data Analysis/Images/Python/pretrained_vgg16.keras'
finetuned_model_save_path = 'D:/Data Analysis/Images/Python/retrained_vgg16_finetuned.keras'
tensorboard_log_dir = 'D:/Data Analysis/Images/tensorboard_logs'
source_dir = 'D:/Data Analysis/Images/source images'
bridge_dir = 'D:/Data Analysis/Images/sorted images/bridge'
no_bridge_dir = 'D:/Data Analysis/Images/sorted images/no_bridge'
csv_file_path = r'D:\Data Analysis\Images\predictions.csv'

# Define data augmentation parameters
data_gen_args = dict(rescale=1./255,
                     rotation_range=20,
                     width_shift_range=0.2,
                     height_shift_range=0.2,
                     shear_range=0.2,
                     zoom_range=0.2,
                     horizontal_flip=True,
                     fill_mode='nearest')

datagen = ImageDataGenerator(**data_gen_args)

# Create generators
train_generator = datagen.flow_from_directory(train_dir,
                                              target_size=(224, 224),
                                              batch_size=32,
                                              class_mode='binary')

validation_generator = datagen.flow_from_directory(validation_dir,
                                                   target_size=(224, 224),
                                                   batch_size=32,
                                                   class_mode='binary')

test_generator = datagen.flow_from_directory(test_dir,
                                             target_size=(224, 224),
                                             batch_size=32,
                                             class_mode='binary')

# Define the model
def create_model():
    base_model = VGG16(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    for layer in base_model.layers:
        layer.trainable = False
    x = base_model.output
    x = Flatten()(x)
    x = Dense(256, activation='relu')(x)
    x = Dense(1, activation='sigmoid')(x)
    model = Model(inputs=base_model.input, outputs=x)
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

# Function to preprocess images for prediction
def preprocess_image(img_path):
    try:
        img = load_img(img_path, target_size=(224, 224))
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        return preprocess_input(img_array)
    except Exception as e:
        logging.error(f"Error processing image {img_path}: {e}")
        return None

# Function to predict images and sort them into bridge or no_bridge directories
def predict_and_sort_images(model, source_dir, bridge_dir, no_bridge_dir):
    if not os.path.exists(bridge_dir):
        os.makedirs(bridge_dir)
    if not os.path.exists(no_bridge_dir):
        os.makedirs(no_bridge_dir)
    
    test_images = glob.glob(os.path.join(source_dir, '*'))
    results = []

    for img_path in test_images:
        img_array = preprocess_image(img_path)
        if img_array is None:
            logging.warning(f"Skipping image {img_path} due to preprocessing error.")
            continue
        confidence = model.predict(img_array)[0][0]
        if confidence >= 0.5:
            dest_dir = bridge_dir
        else:
            dest_dir = no_bridge_dir
        dest_path = os.path.join(dest_dir, os.path.basename(img_path))
        shutil.move(img_path, dest_path)
        result_dict = {'File Path': img_path, 'bridge_confidence': confidence, 'Destination': dest_path}
        results.append(result_dict)
        logging.info(f"Processed {img_path}: confidence={confidence}, moved to {dest_path}")

    # Write results to CSV file
    try:
        logging.info(f"Writing results to {csv_file_path}")
        with open(csv_file_path, 'w', newline='') as csvfile:
            fieldnames = ['File Path', 'bridge_confidence', 'Destination']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(result)
                logging.debug(f"Wrote result to CSV: {result}")
        logging.info("Predictions saved to predictions.csv and images sorted.")
    except Exception as e:
        logging.error(f"Error writing to CSV file: {e}")

# Function to load the appropriate model with error handling and advising user
def load_model_safe():
    if os.path.exists(finetuned_model_save_path):
        try:
            model = load_model(finetuned_model_save_path)
            logging.info(f"Loaded fine-tuned model from {finetuned_model_save_path}")
            return model
        except Exception as e:
            logging.error(f"Error loading fine-tuned model: {e}")
    if os.path.exists(model_save_path):
        try:
            model = load_model(model_save_path)
            logging.info(f"Loaded trained model from {model_save_path}")
            return model
        except Exception as e:
            logging.error(f"Error loading trained model: {e}")

    logging.info("No trained or fine-tuned model found, creating a new base model.")
    return create_model()

# Menu options
def train_binary_classification_model():
    model = create_model()

    # Callbacks
    tensorboard = TensorBoard(log_dir=tensorboard_log_dir)
    early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    checkpoint = ModelCheckpoint(model_save_path, monitor='val_loss', save_best_only=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7)
    
    # Fit the model
    history = model.fit(train_generator,
                        steps_per_epoch=train_generator.samples // train_generator.batch_size,
                        validation_data=validation_generator,
                        validation_steps=validation_generator.samples // validation_generator.batch_size,
                        epochs=50,  # Increased epochs for better training
                        callbacks=[tensorboard, early_stopping, checkpoint, reduce_lr])

    # Save the model (it will save the best model as per ModelCheckpoint)
    model.save(model_save_path)

    return history

def fine_tune_model(base_model_path, train_generator, validation_generator, model_save_path):
    """
    Fine-tune a pre-trained model by unfreezing top layers and re-training with a lower learning rate.

    Args:
    - base_model_path (str): Path to the pre-trained model weights file.
    - train_generator (tf.keras.preprocessing.image.DirectoryIterator): Data generator for training data.
    - validation_generator (tf.keras.preprocessing.image.DirectoryIterator): Data generator for validation data.
    - model_save_path (str): Path to save the fine-tuned model.
    """
    model = load_model_safe(base_model_path)
    if model is None:
        logging.error("Cannot fine-tune because the model could not be loaded.")
        return

    # Unfreeze top layers for fine-tuning
    for layer in model.layers[-4:]:
        layer.trainable = True

    # Compile the model with a lower learning rate
    model.compile(optimizer=Adam(lr=1e-5), loss='binary_crossentropy', metrics=['accuracy'])

    # Define callbacks and train the model
    tensorboard = TensorBoard(log_dir='logs/fine_tuning')
    history_fine = model.fit(train_generator,
                             steps_per_epoch=train_generator.samples // train_generator.batch_size,
                             validation_data=validation_generator,
                             validation_steps=validation_generator.samples // validation_generator.batch_size,
                             epochs=10,
                             callbacks=[tensorboard])

    # Save the fine-tuned model
    model.save(model_save_path)

    return model, history_fine

def evaluate_model():
    model = load_model_safe()
    if model is None:
        logging.error("Cannot evaluate because the model could not be loaded.")
        return

    test_loss, test_acc = model.evaluate(test_generator, steps=test_generator.samples // test_generator.batch_size)
    print(f'Test accuracy: {test_acc}')

def predict_sort():
    model = load_model_safe()
    if model is None:
        logging.error("Cannot predict and sort because the model could not be loaded.")
        return

    predict_and_sort_images(model, source_dir, bridge_dir, no_bridge_dir)



def train_multi_dimensional_model(base_model_path, dimension_name, train_generator, validation_generator, model_save_path, epochs=10, generate_new_base_model=False):
    """
    Train a multi-dimensional classifier model by adding one dimension at a time to the base VGG16 model.

    Args:
    - base_model_path (str): Path to the base VGG16 model weights file.
    - dimension_name (str): Name of the dimension being added to the model (e.g., "bridges", "cars").
    - train_generator (tf.keras.preprocessing.image.DirectoryIterator): Data generator for training data.
    - validation_generator (tf.keras.preprocessing.image.DirectoryIterator): Data generator for validation data.
    - model_save_path (str): Path to save the trained model.
    - epochs (int): Number of epochs for training. Default is 10.
    - generate_new_base_model (bool): Whether to generate a new base model without pre-trained weights. Default is False.
    """
    # Generate new base model if specified
    if generate_new_base_model:
        base_model = VGG16(weights=None, include_top=False, input_shape=(224, 224, 3))
    else:
        base_model = load_model(base_model_path)

    # Freeze convolutional layers
    for layer in base_model.layers:
        layer.trainable = False

    # Add custom classifier layers for binary classification
    x = Flatten(name=f'{dimension_name}_flatten')(base_model.output)
    x = Dense(256, activation='relu', name=f'{dimension_name}_dense')(x)
    predictions = Dense(1, activation='sigmoid', name=f'{dimension_name}_predictions')(x)

    # Create the new model by combining base model with custom layers
    model = Model(inputs=base_model.input, outputs=predictions)

    # Compile the model
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    # Train the model
    history = model.fit(train_generator,
                        steps_per_epoch=train_generator.samples // train_generator.batch_size,
                        validation_data=validation_generator,
                        validation_steps=validation_generator.samples // validation_generator.batch_size,
                        epochs=epochs)

    # Save the trained model
    model.save(model_save_path)

    return model, history




def main_menu():
    while True:
        print("\nMenu:")
        print("1. Train Binary Classification Model")
        print("2. Train Multi-Dimentional Model")
        print("3. Fine-tune Model")
        print("4. Evaluate Model")
        print("5. Predict and Sort Images")
        print("6. Exit")
        choice = input("Enter your choice: ")
        
        if choice == '1':
            train_binary_classification_model()
        if choice == '2':
            new_base_model_response = input("Remove current dimensions and Generate a new model (Y/N): ")
            if new_base_model_response.lower() == "y":
                new_base_model_response = True
            else: 
                new_base_model_response = False
            dimension_name = input("Name of the new dimension: ")
            train_multi_dimensional_model(base_model_path, dimension_name, train_generator, validation_generator, model_save_path, epochs=10, generate_new_base_model=new_base_model_response)
        elif choice == '3':
            fine_tune_model()
        elif choice == '4':
            evaluate_model()
        elif choice == '5':
            predict_sort()
        elif choice == '6':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()