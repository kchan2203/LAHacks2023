from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from dateutil.relativedelta import relativedelta
import cohere
from objectdetection import load_yolo_model, detect_objects
from flask import Flask, render_template, request

 
import base64
from PIL import Image
from io import BytesIO

import os

def base64_to_image(base64_str):
    img_data = base64.b64decode(base64_str)
    img = Image.open(BytesIO(img_data))
    return img

app = Flask(__name__)
CORS(app)  # This will allow all origins by default

model = load_yolo_model()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    file = request.files['image']
    image = file.read()
    objects = detect_objects(image, model)
    return render_template('result.html', objects=objects)



# initialize the Cohere Client with an API Key
co = cohere.Client('Zc1Bpd8ZYdYPLwMGT0uwmGQRIjaxD48A6SQsY48t')

# API endpoint for getting data from Firebase
@app.route('/process_image', methods=['GET', 'POST'])
def get_data():
    # Fetch data from Firestore collection
    data = request.get_json()
    image = data['content']

    if image.startswith('data:image/png;base64,'):
      image = image.replace('data:image/png;base64,', '')

    # Set your desired folder and filename
    folder_name = 'saved_images'
    file_name = 'decodedImage.png'

    # Create the folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Join the folder and filename to create the save_path
    save_path = os.path.join(folder_name, file_name)

    # Save decoded image to local filesystem
    with open(save_path, 'wb') as f:
        f.write(base64.b64decode(image))

    return jsonify({"test": "Image saved successfully"})


@app.route('/')
def index():
    return "Hello World"



# API endpoint for getting data from Firebase
@app.route('/generate_recipe', methods=['GET', 'POST'])
def recipe_maker():
    # Fetch data from Firestore collection
    almost_expired = request.get_json()
    almost_expired = almost_expired['content']
    #all_ingredients is a list of all the ingredients in the image
    recipe_prompt = f"Make a recipe using but not only {' '.join(almost_expired)}."
    prediction = co.chat(recipe_prompt,
                        chatlog_override=[
            {'Bot': 'Hey!'},
            {'User': 'Make the output a list of these objects.  Each object is a food item.  The format for the object is: {name:food_name}'},
            {'Bot': 'Okay!'},
        ], max_tokens=300, temperature = 0,return_chatlog = True)
    return jsonify({'recipe': prediction.text})

# Run Flask app
if __name__ == "__main__":
    app.run(debug = True, port = 21394)

def image_process(image):
    return ['apple','tomato','potato','lettuce']

def get_expiry(all_ing):
    ing_w_expiry = []
    for ing in all_ing.keys():
        ingredient_obj = {}
        prediction = co.chat(f"In a one number answer, how long does {ing} last in the fridge? Do not say approximate",
                    chatlog_override=[
            {'Bot': 'Hey!'},
            {'User': 'Make the output in this format: {object_name: response} '},
            {'Bot': 'Okay!'},
        ], max_tokens=8, temperature = 0)
        shift_time = shift_date(prediction.text.split(':')[1].strip())
        ingredient_obj['name'] = ing
        ingredient_obj['expiration_date'] = shift_time[0]
        ing_w_expiry.append(ingredient_obj)
    ing_w_expiry_sorted = dict(sorted(ing_w_expiry.items(), key=lambda x:x[1])) 

    return jsonify(ing_w_expiry_sorted)


def shift_date(input_string):
    # Current date
    current_date = datetime.now()

    # Extract the number and unit from the input string
    input_list = input_string.split()
    num = int(input_list[0])
    unit = input_list[1]

    # Define the mapping of units to relativedelta arguments
    unit_map = {
        'days': {'days': num},
        'weeks': {'weeks': num},
        'months': {'months': num},
    }

    # Create a relativedelta object based on the input unit
    rel_delta = relativedelta(**unit_map[unit])

    # Add the relativedelta to the current date
    new_date = current_date + rel_delta

    # Convert the new date to a string in the desired format
    new_date_string = new_date.strftime("%Y-%m-%d")  # Example format: YYYY-MM-DD
    return new_date, new_date_string

