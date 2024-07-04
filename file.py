import pyfirmata
import time
import serial
from flask import Flask, render_template, request
import os
import numpy as np
import joblib
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import requests
import serial
import requests
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore, db

api_key = '6d91b22bd2dc4d98a29b5d51c38dff0e'
#api_key = 'f53389f6ba21442b9044062ccf083115'

start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)

total_precipitation_mm = 400.0

current_date = start_date

formatted_date1 = current_date.strftime('%Y-%m-%d')
formatted_date2 = end_date.strftime('%Y-%m-%d')

ser=serial.Serial()
nan=0
cred = credentials.Certificate(r"E:\git\BuildSafe\credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://vaultrix-c5e8c-default-rtdb.firebaseio.com'
})

fdb = firestore.client()
doc_ref = db.reference("/")

app = Flask(__name__)

depth_model = joblib.load(r'E:\git\BuildSafe/models/earthquake_depth.pkl')
ph_porosity_model = joblib.load(r'E:\git\BuildSafe/models/soil_ph_porosity_model.pkl')
magnitude_model = joblib.load(r'E:\git\BuildSafe/models/earthquake_magnitude.pkl')
occurrence_model = joblib.load(r'E:\git\BuildSafe/models/earthquake_occurance.pkl')
flood_model = joblib.load(r'E:\git\BuildSafe/models/flood_occurance.pkl')
soil_model = load_model(r'E:\git\BuildSafe/models/soil_type.h5')
moisture_floor_model = joblib.load(r'E:\git\BuildSafe/models/moisture_floor.pkl')
moisture_ground_model = joblib.load(r'E:\git\BuildSafe/models/moisture_ground.pkl')
groundwater_model = joblib.load(r"E:\git\BuildSafe\models\groundwater_level_model.joblib")
getVal={'Humidity': 0, 'Temperature': 'nan nan', 'Soil Moisture': 1023.0, 'Cap Moisture': 564.0, 'Air Quality': 20.0, 'Sound': 54.0}

@app.route('/')
def index():
    ser = serial.Serial(port='COM13')
    print(os.listdir('./models'))
    getVal = eval(ser.readline())
    print(getVal)
    ser.close() 
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    global total_precipitation_mm
    global doc_ref
    nofloors = float(request.form['nofloors'])
    lat = float(request.form['lat'])
    lon = float(request.form['lon'])
    temp = float(request.form['temp'])
    landuse = request.form['landuse'].title()
    soildepth = float(request.form['soildepth'])
    predicted_class=''
    precip_response = ''
    moisture_value = 100-((getVal['Soil Moisture']/1024)*100)
    cmoisture_value = 100-((getVal['Cap Moisture']/1024)*100)

    url = f'https://api.weatherbit.io/v2.0/history/daily?key={api_key}&lat={lat}&lon={lon}&start_date={formatted_date1}&end_date={formatted_date2}'


    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        total_precipitation_mm += data['data'][0]['precip']
        if total_precipitation_mm==0:
            total_precipitation_mm+=400
    else:
        print(f"Failed to retrieve data for {formatted_date1}: {response.status_code}")

    
    if 'soilImage' in request.files:
        soil_image = request.files['soilImage']
        img = Image.open(soil_image)
        img = img.resize((150,150))
        img = image.img_to_array(img)
        img = np.expand_dims(img, axis=0)
        
        soil_type_prediction = soil_model.predict(img)
        predicted_class_index = np.argmax(soil_type_prediction)
        class_labels = ['Silt','Clay', 'Loam', 'Sand', 'Gravel']

        predicted_class = class_labels[predicted_class_index]

    print(str(predicted_class), moisture_value)

    depth_prediction = depth_model.predict([[lat, lon]])[0][0]
    magnitude_prediction = magnitude_model.predict([[lat, lon]])[0][1]
    occurrence_prediction = 'Chances are there to occur' if occurrence_model.predict([[lat, lon]])[0]==1 else 'Very less Chances are there to occur'
    flood_prediction = 'Chances are there to occur' if flood_model.predict([[lat, lon]])[0]==1 else 'Very less Chances are there to occur'
    sound_level_prediction = 'Loud' if getVal['Sound']>700 else 'Medium'
    air_quality_level_prediction = 'Polluted' if getVal['Air Quality']>500 else 'Not - Polluted'
    label_encoder = LabelEncoder()
    label_encoder.fit(class_labels)
    predicted_class_index = label_encoder.transform([predicted_class])[0]
    binary_representation = [int(i == predicted_class_index) for i in range(len(class_labels))]
    binary_representation.append(moisture_value)
    print(binary_representation)
    moisture_floor_prediction = moisture_floor_model.predict([binary_representation])[0]
    moisture_ground_prediction = moisture_ground_model.predict([binary_representation])[0]

    binary_representation = [int(i == predicted_class_index) for i in range(len(class_labels))]
    binary_representation.append(cmoisture_value)
    print(binary_representation)
    cmoisture_floor_prediction = moisture_floor_model.predict([binary_representation])[0]
    cmoisture_ground_prediction = moisture_ground_model.predict([binary_representation])[0]
    
    new_data = {
    'Moisture Level (%)': [moisture_value],
    'Soil Texture': [str(predicted_class)],
    'Bulk Density (g/cm³)': [1.35],
    'Soil Temperature (°C)': [temp]
    }
    new_df = pd.DataFrame(new_data)

    ph_porosity_predictions = ph_porosity_model.predict(new_df)

    print(f"Predicted Soil pH: {ph_porosity_predictions[0][0]}")
    print(f"Predicted Soil Porosity: {ph_porosity_predictions[0][1]}")

    cnew_data = {
    'Moisture Level (%)': [cmoisture_value],
    'Soil Texture': [str(predicted_class)],
    'Bulk Density (g/cm³)': [1.35],
    'Soil Temperature (°C)': [temp]
    }
    cnew_df = pd.DataFrame(cnew_data)

    cph_porosity_predictions = ph_porosity_model.predict(cnew_df)

    print(f"Predicted Soil pH: {cph_porosity_predictions[0][0]}")
    print(f"Predicted Soil Porosity: {cph_porosity_predictions[0][1]}")

    example_data = pd.DataFrame({
    'Porosity (%)': [ph_porosity_predictions[0][1]],
    'Soil Texture': [predicted_class],
    'Soil Depth (m)': [soildepth],
    'Soil Temp (°C)': [temp],
    'Annual Precipitation (mm)': [total_precipitation_mm],
    'Land Use': [landuse]
    })

    example_pred_loaded = groundwater_model.predict(example_data)
    print(f"Predicted Groundwater Level (loaded model): {example_pred_loaded[0]} meters")

    example_data2 = pd.DataFrame({
    'Porosity (%)': [cph_porosity_predictions[0][1]],
    'Soil Texture': [predicted_class],
    'Soil Depth (m)': [soildepth],
    'Soil Temp (°C)': [temp],
    'Annual Precipitation (mm)': [total_precipitation_mm],
    'Land Use': [landuse]
    })

    example_pred_loaded2 = groundwater_model.predict(example_data2)
    print(f"Predicted Groundwater Level (loaded model): {example_pred_loaded2[0]} meters")
    
    nooffloors = f'Building with {nofloors} floors Can be built' if nofloors <= moisture_floor_prediction else f'Building with {nofloors} floors Can\'t be built'
    
    data = {
        "latitude":lat,
        "longitude":lon,
        "temperature":temp,
        "landuse":landuse,
        "soildepth": soildepth,
        "Earthquake Depth": depth_prediction,
        "Earthquake Magnitude": magnitude_prediction,
        "Earthquake Occurrence": occurrence_prediction,
        "Flood Occurrence": flood_prediction,
        "Soil Type": predicted_class,
        "Sound Pollution": sound_level_prediction,
        "Air Pollution": air_quality_level_prediction,
        "Max No of Floors _ Resistive Moisture": moisture_floor_prediction,
        "Ground Water Level _ Resistive Moisture": moisture_ground_prediction,
        "Max No of Floors _ Capacitive Moisture": cmoisture_floor_prediction,
        "Ground Water Level _ Capacitive Moisture": cmoisture_ground_prediction,
        "No of floors to be built": nooffloors,
        "Soil pH Level _ Resistive Moisture, Texture, Tempature": ph_porosity_predictions[0][0],
        "Soil Porosity _ Resistive Moisture, Texture, Tempature": ph_porosity_predictions[0][1],
        "Soil pH Level _ Capacitive Moisture, Texture, Tempature": cph_porosity_predictions[0][0],
        "Soil Porosity _ Capacitive Moisture, Texture, Tempature": cph_porosity_predictions[0][1],
        "Annual Precipitation": total_precipitation_mm,
        "Ground Water level _ Resistive Moisture - Porosity, Soil Texture, Soil Temp, Soil depth, Annual precip, Land Use": example_pred_loaded[0],
        "Ground Water level _ Capacitive Moisture - Porosity, Soil Texture, Soil Temp, Soil depth, Annual precip, Land Use": example_pred_loaded2[0]
    }

    # Save data to Firestore
    #doc_ref = db.collection('predictions').document()
    doc_ref.set(data)

    return render_template('predictions.html', Humidity =  getVal['Humidity'], Temperature = getVal['Temperature'],
                           Soil_Moisture=getVal['Soil Moisture'], Cap_Moisture=getVal['Cap Moisture'],Air_Quality=getVal['Air Quality'],
                           Sound=getVal['Sound'],depth=depth_prediction, magnitude=magnitude_prediction,
                           occurrence=occurrence_prediction, flood=flood_prediction, soil=predicted_class,
                           sound = sound_level_prediction, air=air_quality_level_prediction,
                           moisture_floor= moisture_floor_prediction, moisture_ground=moisture_ground_prediction,
                           cmoisture_floor=cmoisture_floor_prediction, cmoisture_ground=cmoisture_ground_prediction,
                           nooffloors=nooffloors, soil_ph = ph_porosity_predictions[0][0], porosity=ph_porosity_predictions[0][1],
                           csoil_ph = cph_porosity_predictions[0][0], cporosity=cph_porosity_predictions[0][1],
                           annualprecip = total_precipitation_mm, ground1=example_pred_loaded[0], ground2=example_pred_loaded2[0])

if __name__ == '__main__':
    app.run(debug=True)



# ser = serial.Serial(port='COM13')
# nan=0
# while True:
#     time.sleep(1)
#     getVal = eval(ser.readline())
#     print(getVal)
#     break