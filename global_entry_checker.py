import requests
import json
from datetime import datetime
import time

def check_timestamp(url):
    try:
        # Make a GET request to the specified URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code != 200:
            print(f"Error: Failed to fetch data. Status code: {response.status_code}")

        # Parse the JSON response
        data = response.json()

        with open("global_entry_log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()}\n{data}\n\n")

        # Extract the "startTimestamp" field from the JSON data
        available_slots = data['availableSlots']

        if len(available_slots) == 0:
            print(f"{datetime.now()}: No slots available")

        for slot in available_slots:

            start_timestamp_str = slot["startTimestamp"]

            if not start_timestamp_str:
                print(f"{datetime.now()}: ERROR: 'startTimestamp' field not found in JSON response.")

            # Convert the timestamp string to a datetime object
            start_timestamp = datetime.fromisoformat(start_timestamp_str)

            # Check if the timestamp is before March 2024
            if start_timestamp < datetime(2024, 3, 1):
                print(f"{datetime.now()} - Global Entry opening on " + start_timestamp_str)
                # requests.post("https://ntfy.sh/ge-den",
                #         data="Found appointment with date: " + start_timestamp_str,
                #         headers={
                #             "Title": "Global Entry Opening!",
                #             "Priority": "default",
                #             "Tags": "earth_americas,passport_control,airplane"
                #         },
                #         timeout=15)
            else:
                print(f"{datetime.now()}")

    except Exception as e:
        print(f"Exception: {e}")

# DEN Airpot location
website_url = 'https://ttp.cbp.dhs.gov/schedulerapi/slot-availability?locationId=6940'

# Run the script in a loop with a 45-second delay between iterations
while True:
    check_timestamp(website_url)
    time.sleep(15)
