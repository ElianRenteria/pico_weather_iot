import time
time.sleep(2)
import network
import urequests
import ntptime
import utime
from machine import I2C, Pin
from I2C_LCD import I2CLcd
from config import *


# Set up I2C and LCD
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
devices = i2c.scan()
lcd = I2CLcd(i2c, devices[0], 2, 16) if devices else None
if lcd:
    lcd.putstr("Initializing...")

# Initialize Variables
setup_success = False
weather_update_interval = 60 * 60
time_update_interval = 60
last_weather_update = -weather_update_interval
last_time_update = -time_update_interval
time_offset = 4 * 3600  # 4 hours for timezone adjustment

# Connect to Wi-Fi with Robust Retry Mechanism
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def connect_wifi():
    attempt_count = 0
    max_attempts = 10
    connected = False
    while attempt_count < max_attempts:
        if not wlan.isconnected():
            print("Attempting Wi-Fi connection...")
            if lcd:
                lcd.clear()
                lcd.putstr("Attempting Wi-Fi connection...")
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            time.sleep(1)  # Short wait between connection attempts
            attempt_count += 1
        else:
            connected = True
            break
    if connected:
        print("Wi-Fi connected!")
        if lcd:
            lcd.clear()
            lcd.putstr("Wi-Fi Connected")
    else:
        print("Wi-Fi connection failed after multiple attempts.")
        if lcd:
            lcd.clear()
            lcd.putstr("Wi-Fi Failed")
    return connected

def sync_time():
    try:
        ntptime.settime()
        print("Time synchronized!")
        if lcd:
            lcd.clear()
            lcd.putstr("Time Synced")
            time.sleep(1)
        return True
    except:
        print("Failed to sync time.")
        if lcd:
            lcd.clear()
            lcd.putstr("Time Sync Failed")
            time.sleep(1)
        return False

def get_weather():
    headers = {"Content-Type": "application/json"}
    try:
        response = urequests.get(WEATHER_API_URL, headers=headers)
        temp = response.json()["weather"]["temp"]
        response.close()
        print("Weather updated successfully!")
        return temp
    except:
        print("Failed to get weather.")
        return None

def display_on_lcd(time_str, temp):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(CITY+"  " + time_str)
    lcd.move_to(0, 1)
    lcd.putstr("   Temp: " + convert_temp(temp) if temp else "No data")

def convert_temp(t):
    return str(round((t-273.15)*(9/5)+32)) + " F"


while True:
    if setup_success and wlan.isconnected() and lcd:
        current_time = utime.time()

        if current_time - last_time_update >= time_update_interval:
            last_time_update = current_time
            local_time = utime.localtime(current_time + time_offset)
            hour, minute = local_time[3], local_time[4]
            am_pm = "AM" if hour < 12 else "PM"
            hour = hour % 12 or 12
            formatted_time = "{:02}:{:02} {}".format(hour, minute, am_pm)
            print("Time updated:", formatted_time)

        if current_time - last_weather_update >= weather_update_interval:
            last_weather_update = current_time
            temp = get_weather()

        display_on_lcd(formatted_time, temp)
        time.sleep(60)
    else:
        count = 0
        # Setup Wi-Fi and initial time sync with retry logic
        while not connect_wifi():
            time.sleep(5)
        while not setup_success and count < 3:
            setup_success = sync_time()
            count += 1
            time.sleep(1)

