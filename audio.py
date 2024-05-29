import json
import time
import requests
from pymongo import MongoClient



def getAudio(text, file_name, apikey):
    payload = text
    url = 'https://api.fpt.ai/hmi/tts/v5'
    headers = {
        'api-key': apikey,
        'speed': '',
        'voice': 'banmai'
    }
    response = requests.request('POST', url, data=payload.encode('utf-8'), headers=headers)
    print(response)

    if len(text.split(" ")) <= 50:
        time.sleep(25)
    elif len(text.split(" ")) <= 100:
        time.sleep(30)
    elif len(text.split(" ")) <= 300:
        time.sleep(45)
    else:
        time.sleep(120)
    output = response.text
    file_url = json.loads(output)

    rp = requests.get(file_url["async"])
    time.sleep(5)
    print(rp)

    if rp.status_code == 200:
        # Specify the local file path where you want to save the downloaded file

        # Open the local file in binary write mode and write the content of the response
        with open(file_name, 'wb') as file:
            file.write(rp.content)

        print(f"File downloaded and saved to {file_name}")
    else:
        print(f"Failed to download the file. Status code: {rp.status_code}")
        # raise ValueError("File not save")
    time.sleep(5)
    with open(file_name, 'rb') as mp3_file:
        mp3_content = mp3_file.read()
    mp3_file.close()
    # metadata = {
    #     'file_name': local_file_path,
    #     'content': mp3_content,
    # }
    return mp3_content
    # db.vn_newflow["audio"].insert_one(metadata)

    # print("Successfull insert audio")


def generate_audio(text, file_audio_save, config):
    # Assuming your API endpoint is hosted locally
    url =  config.API_ENDPOINT_TEXT_TO_SPEECH  # Replace this with your actual API endpoint
    # Sample text to convert to speech
    # Make a GET request with the text as a query parameter
    response = requests.get(url, params={"text": text})
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Assuming you want to save the audio file locally
        with open(file_audio_save, "wb") as f:
            f.write(response.content)
        print("Audio file saved successfully!")
    else:
        print("Failed to retrieve audio:", response.text)




    