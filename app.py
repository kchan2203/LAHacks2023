from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from dateutil.relativedelta import relativedelta
import cohere
from flask import Flask, render_template, request

 
import base64
from PIL import Image
from io import BytesIO

import os

app = Flask(__name__)
CORS(app)  # This will allow all origins by default

def base64_to_image(base64_str):
    img_data = base64.b64decode(base64_str)
    img = Image.open(BytesIO(img_data))
    return img


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




def get_expiry(all_ing):
    ingredient_obj = {}
    prediction = co.chat(f"In a one number answer, how long does {all_ing} last in the fridge? Do not say approximate",
                chatlog_override=[
        {'Bot': 'Hey!'},
        {'User': 'Make the output in this format: {object_name: response} '},
        {'Bot': 'Okay!'},
    ], max_tokens=8, temperature = 0)
    ingredient_obj['name'] = all_ing
    ingredient_obj['expiration_date'] = prediction.text.split(':')[1].strip()
    return jsonify(ingredient_obj)



@app.route('/')
def index():
    return render_template('index.html')



@app.route('/find_expiry_single', methods=['POST'])
def detect():
    data = request.get_json()
    all_ingredients = data['content']
    ing_w_expiry = get_expiry([all_ingredients])
    return ing_w_expiry

@app.route('/find_expiry', methods=['POST'])
def detect_multiple():
    data = request.get_json()
    all_ingredients = data['content']
    ing_w_expiry = get_expiry(all_ingredients)
    return jsonify(ing_w_expiry)

# initialize the Cohere Client with an API Key
co = cohere.Client('Zc1Bpd8ZYdYPLwMGT0uwmGQRIjaxD48A6SQsY48t')

# @app.route('/')
# def index():
#     return "Hello World"

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



