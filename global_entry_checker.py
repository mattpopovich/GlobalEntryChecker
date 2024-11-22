"""
Date:   November 14, 2023
Author: Matt Popovich (https://mattpopovich.com/)
About:  Checks the locations.yaml file for open Global Entry interview openings
        Will send alerts via ntfy.sh for the desired `locations_to_alert`

Ex. python3 global_entry_checker.py
"""

import requests
import json
from datetime import datetime
import time
import yaml                     # Parse .yaml file
from typing import Final        # Extra typing imports
from GlobalEntryNotifier import GlobalEntryNotifier

def check_timestamp(global_entry_notifier: GlobalEntryNotifier,
                    location: str,
                    locations: dict,
                    locations_to_alert: dict,
                    dhs_availability_url: str):

    # Populate with empty values if they weren't already created
    default_previous_timestamp = datetime(2030, 1, 1)
    locations[location].setdefault("previous_timestamp", default_previous_timestamp)
    locations[location].setdefault("datetime_last_notification", None)

    # Make a GET request to the specified URL
    url = dhs_availability_url + str(locations[location]["locationId"])
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code != 200:
        print(f"Error: Failed to fetch data. Status code: {response.status_code}")

    # Parse the JSON response
    data = response.json()

    with open("global_entry_log.txt", "a") as log_file:
        log_file.write(f"{datetime.utcnow()}\n{data}\n\n")

    # Extract the "startTimestamp" field from the JSON data
    available_slots = data['availableSlots']

    if len(available_slots) == 0:
        print(f"{datetime.utcnow()}: No slots available for {location}")
        if locations[location]["datetime_last_notification"]:
            if location in locations_to_alert:
                message = f"Previous appointment at {location} is no longer available :("
                global_entry_notifier.send_global_entry_notification(location, message)

        locations[location]["previous_timestamp"] = default_previous_timestamp
        locations[location]["datetime_last_notification"] = None


    for slot in available_slots:

        start_timestamp_str = slot["startTimestamp"]

        if not start_timestamp_str:
            print(f"{datetime.utcnow()}: ERROR: 'startTimestamp' field not found in JSON response for {location}")

        # Convert the timestamp string to a datetime object
        start_timestamp = datetime.fromisoformat(start_timestamp_str)

        # If the found appointment isn't within 90 days, ignore it
        if (start_timestamp - datetime.utcnow()).days < 90:

            # If the appointment is newer than the previous appointment we were tracking
            if start_timestamp < locations[location]["previous_timestamp"]:
                print(f"{datetime.utcnow()}: Found slot in {location} for {start_timestamp_str}, it is new best!")

                if location in locations_to_alert:
                    message = f"Found new appointment at {location}: " + start_timestamp_str
                    global_entry_notifier.send_global_entry_notification(location, message)

                locations[location]["previous_timestamp"] = start_timestamp
                locations[location]["datetime_last_notification"] = datetime.utcnow()

            # If the appointment is the same as the last one we were tracking
            elif start_timestamp == locations[location]["previous_timestamp"]:
                print(f"{datetime.utcnow()}: Found slot in {location} for {start_timestamp_str}, it is same as previous appointment")
                if (datetime.utcnow() - locations[location]["datetime_last_notification"]).seconds > 180:
                    # Every 3min, send a reminder that the appointment is still open

                    if location in locations_to_alert:
                        message = f"Appointment at {location} is still open: {start_timestamp_str}"
                        global_entry_notifier.send_global_entry_notification(location, message)

                    locations[location]["datetime_last_notification"] = datetime.utcnow()

            # If the appointment is worse than the last one we were tracking
            elif start_timestamp > locations[location]["previous_timestamp"]:
                print(f"{datetime.utcnow()}: Found slot in {location} for {start_timestamp_str}, it is worse than previous appointment")
                if location in locations_to_alert:
                    message = f"Appointment at {location} closed, but now there is one at {start_timestamp_str}"
                    global_entry_notifier.send_global_entry_notification(location, message)

                locations[location]["previous_timestamp"] = start_timestamp
                locations[location]["datetime_last_notification"] = datetime.utcnow()
        else:
            print(f"{datetime.utcnow()}: Found slot in {location} for {start_timestamp_str}, but it is > 90 days away")

### Constants
locations_to_alert = ["SEA"]
period_s: Final[int] = 15
dhs_availability_url: Final[str] = "https://ttp.cbp.dhs.gov/schedulerapi/slot-availability?locationId="
locations_file: Final[str] = "locations.yaml"

### Variables
global_entry_notifier = GlobalEntryNotifier()
locations: dict = yaml.safe_load(open(locations_file))
sleep_between_calls_s: Final[float] = period_s / len(locations)

# Run the script in a loop with a delay between iterations
while True:
    for location in locations:
        try:
            check_timestamp(global_entry_notifier, location, locations, locations_to_alert, dhs_availability_url)
        except Exception as e:
            print(f"Exception occurred while trying to get {location}: {e}")
            print(f"Aborting this location and trying the next one...")
        # print(locations)
        time.sleep(sleep_between_calls_s)
