from kivy.lang import Builder
from math import sin, cos, sqrt, atan2, radians
from plyer import gps, vibrator, tts
from kivy.app import App
from kivy.properties import StringProperty
from kivy.clock import mainthread
from kivy.utils import platform
from geopy.distance import great_circle
import threading
import json
import requests
import string
import random
import time

url = 'https://project1123-2b81f.firebaseio.com/.json' 
auth_key = 'LL7r2d8iKIFP2j6mwYzr7nFDHEPEPtoAIr7kSu3i' 

kv = '''
BoxLayout:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
    Label:
        text: app.gps_location

    Label:
        text: app.gps_status

    BoxLayout:
        size_hint_y: None
        height: '60dp'
        padding: '0dp'
        ToggleButton:
            text: 'Start' if self.state == 'normal' else 'Stop'
            on_state:
                app.start(1000, 0) if self.state == 'down' else \
                app.stop()
'''
def beep(data):
    tts.speak(data)
    # sound = SoundLoader.load('beep-04.wav')
    # sound.play()

def haversine(latitude2, longitude2, latitude1, longitude1):
	R = 6373.0

	lat1 = radians(latitude1)
	lon1 = radians(longitude1)
	lat2 = radians(latitude2)
	lon2 = radians(longitude2)

	dlon = lon2 - lon1
	dlat = lat2 - lat1

	a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))

	distance = R * c
	return distance*3280.84


def check(latitude, longitude, latitude2, longitude2):
    distance = great_circle((latitude, longitude), (latitude2, longitude2)).miles*5280
    print(latitude, longitude)
    print(latitude2, longitude2)
    print(distance)
    
    if distance < 32.5:
        beep("Too Close")

def get_random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

class Database():
    def __init__(self, url, auth_key):
        self.auth_key = auth_key
        self.url = url

    def patch(self, JSON):
        requests.patch(url = self.url, json = JSON)

    def post(self, JSON):
        requests.post(url = self.url, json = JSON)

    def put(self, JSON):
        requests.put(url = self.url, json = JSON)

    def delete(self, code):
        requests.delete(url = self.url[:-5] + code + ".json")

    def get(self):
        request = requests.get(self.url + '?auth=' + self.auth_key)
        return request.json()


class GpsTest(App):

    gps_location = StringProperty()
    gps_status = StringProperty('Click Start to get Be Safer!')
    code = get_random_string()

    count = 0
    def request_android_permissions(self):
        """
        Since API 23, Android requires permission to be requested at runtime.
        This function requests permission and handles the response via a
        callback.

        The request will produce a popup if permissions have not already been
        been granted, otherwise it will do nothing.
        """
        from android.permissions import request_permissions, Permission

        def callback(permissions, results):
            """
            Defines the callback to be fired when runtime permission
            has been granted or denied. This is not strictly required,
            but added for the sake of completeness.
            """
            if all([res for res in results]):
                print("callback. All permissions granted.")
            else:
                print("callback. Some permissions refused.")

        request_permissions([Permission.ACCESS_COARSE_LOCATION,
                             Permission.ACCESS_FINE_LOCATION], callback)
        # # To request permissions without a callback, do:
        # request_permissions([Permission.ACCESS_COARSE_LOCATION,
        #                      Permission.ACCESS_FINE_LOCATION])

    def build(self):
        try:
            gps.configure(on_location=self.on_location,
                          on_status=self.on_status)
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            self.gps_status = 'GPS is not implemented for your platform'

        if platform == "android":
            print("gps.py: Android detected. Requesting permissions")
            self.request_android_permissions()

        return Builder.load_string(kv)

    def start(self, minTime, minDistance):
        gps.start(minTime, minDistance)

    def stop(self):
        gps.stop()
        db = Database(url, auth_key)
        db.delete(self.code)

    @mainthread
    def on_location(self, **kwargs):
        self.gps_location = '\n'.join([
                '{}={}'.format(k, v) for k, v in kwargs.items()])
        
        # if self.count >= 120:
        print(self.count)
        location = list(kwargs.items())
        db = Database(url, auth_key)
        data = {f"{self.code}": {"latitude": location[0][1],"longitude": location[1][1]}}
        db.patch(data)
        all_data = db.get()
        for key, value in all_data.items():
            if key != self.code:
                check(value["latitude"], value["longitude"], location[0][1], location[1][1])
        # else:
        #     print(self.count)
        self.count+=1

    @mainthread
    def on_status(self, stype, status):
        self.gps_status = 'type={}\n{}'.format(stype, status)

    def on_pause(self):
        gps.stop()
        return True

    def on_resume(self):
        gps.start(1000, 0)
        pass


if __name__ == '__main__':
    GpsTest().run()
