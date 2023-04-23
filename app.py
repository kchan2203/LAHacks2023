from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from dateutil.relativedelta import relativedelta
import cohere

app = Flask(__name__)

#Database stuff if required
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("serviceAccountKeyFirebase.json")
firebase_admin.initialize_app(cred)

# initialize the Cohere Client with an API Key
co = cohere.Client('Zc1Bpd8ZYdYPLwMGT0uwmGQRIjaxD48A6SQsY48t')

# API endpoint for getting data from Firebase
@app.route('/process_image', methods=['GET', 'POST'])
def get_data():
    # Fetch data from Firestore collection
    image = request.form['content']
    #all_ingredients is a list of all the ingredients in the image
    all_ingredients = image_process(image)
    #ing_w_expiry is a dictionary of all the ingredients with their expiry dates
    ing_w_expiry = get_expiry(all_ingredients)
    return jsonify(ing_w_expiry)


@app.route('/')
def index():
    return "Hello World"

# Run Flask app
if __name__ == "__main__":
    app.run(debug = True)


# API endpoint for getting data from Firebase
@app.route('/generate_recipe', methods=['GET', 'POST'])
def get_data():
    # Fetch data from Firestore collection
    almost_expired = request.form['content']
    #all_ingredients is a list of all the ingredients in the image
    recipe_prompt = f"Make a recipe using but not only {' '.join(almost_expired)}."
    prediction = co.chat(recipe_prompt,
                        chatlog_override=[
            {'Bot': 'Hey!'},
            {'User': 'Make the output a list of these objects.  Each object is a food item.  The format for the object is: {name:food_name}'},
            {'Bot': 'Okay!'},
        ], max_tokens=300, temperature = 0,return_chatlog = True)
    return jsonify({'recipe': prediction.text})


def image_process(image):
    return ['apple','tomato','potato','lettuce']

def get_expiry(all_ing):
    ing_w_expiry = []
    for ing in all_ing.keys():
        ingredient_obj = {}
        prediction = co.chat("In a one number answer, how long does carrot last in the fridge? Do not say approximate",
                    chatlog_override=[
            {'Bot': 'Hey!'},
            {'User': 'Make the output in this format: {object_name: response} '},
            {'Bot': 'Okay!'},
        ], max_tokens=8, temperature = 0)
        shift_time = shift_date(prediction.text.split(':')[1].strip())
        ingredient_obj['name'] = ing
        ingredient_obj['expiration_date'] = shift_time[0]
        ing_w_expiry.append(ingredient_obj)
    return jsonify(ing_w_expiry)

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

