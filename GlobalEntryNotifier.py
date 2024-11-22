import requests
from datetime import datetime, timedelta
from collections import defaultdict, deque

class GlobalEntryNotifier:
    def __init__(self, base_url="https://ntfy.sh", timeout=15):
        """
        Initializes the notifier with a base URL and optional timeout.

        :param base_url: The base URL for the ntfy service.
        :param timeout: Timeout for the request in seconds.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.notifications = []  # List to store timestamps of sent notifications

        # How many times do we want to repeatedly notify the user
        self.NUM_REPEAT_SENDS = 3
         # Tracks last n messages per location
        self.sent_messages = defaultdict(lambda: deque(maxlen=self.NUM_REPEAT_SENDS))


    def send_notification(self, url, data, headers, timeout):
        """
        Sends a notification with the given parameters.

        :param url: The URL to send the notification to.
        :param data: The payload data for the POST request.
        :param headers: Headers for the POST request.
        :param timeout: Timeout for the request in seconds.
        :return: Response object from the POST request.
        """

        try:
            response = requests.post(url, data=data, headers=headers, timeout=timeout)
            response.raise_for_status()

            # Add the current timestamp to the notifications list
            self._record_notification()

            print(f"Notification sent successfully: {response.status_code}")
            return response
        except requests.RequestException as e:
            print(f"Error sending notification: {e}")
            return None

    def send_global_entry_notification(self, location, message: str):
        """
        Sends a Global Entry notification about an appointment opening.

        :param location: The location of the appointment.
        :param start_timestamp_str: The start timestamp of the appointment.
        :return: Response object from the POST request.
        """
        # Check if this message has been sent 3 times already
        messages = self.sent_messages[location]
        if messages.count(message) >= self.NUM_REPEAT_SENDS:
            print("Skipping notification, we have already sent it at least " +
                  f"{self.NUM_REPEAT_SENDS} times: {message}")
            return None

        # Build the notification
        url = f"{self.base_url}/GE-{location}"
        data = f"{message}"
        headers = {
            "Title": "Global Entry Alert!",
            "Priority": "default",
            "Tags": "earth_americas,passport_control,airplane"
        }

        # Send the notification
        response = self.send_notification(url, data, headers, self.timeout)

        if response:
            # Record the ssent message for the location
            messages.append(message)

        return response

    def _record_notification(self):
        """
        Records a notification timestamp and logs the number of notifications
            sent in the last 24 hours.
        """
        now = datetime.now()

        # Add the current timestamp
        self.notifications.append(now)

        # Remove notifications older than 24 hours
        cutoff = now - timedelta(hours=24)
        self.notifications = [ts for ts in self.notifications if ts > cutoff]

        # Log the count
        print(f"Notifications sent in the last 24 hours: {len(self.notifications)}")


# Example usage
if __name__ == "__main__":
    notifier = GlobalEntryNotifier()
    location = "DEN"
    start_timestamp_str = "2024-11-21 15:00:00"
    response = notifier.send_global_entry_notification(location, start_timestamp_str)
