import time
import network
import urequests
import ntptime
import utime
from machine import I2C, Pin
from I2C_LCD import I2CLcd
from config import *


# Initialize variables
setup_success = False
weather_update_interval = 60 * 60  # 1 hour in seconds
time_update_interval = 60  # 1 minute in seconds
last_weather_update = -weather_update_interval  # Ensure weather updates on first run
last_time_update = -time_update_interval  # Ensure time updates on first run
time_offset = 5 * 3600  # 5 hours for timezone adjustment in seconds

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def connect_wifi():
    attempt_count = 0
    max_attempts = 15
    if not wlan.isconnected():
        while not wlan.isconnected() and attempt_count < max_attempts:
            print("Connecting to Wi-Fi...")
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            attempt_count += 1
            time.sleep(1)
    return wlan.isconnected()

def sync_time():
    try:
        ntptime.settime()
        print("Time synchronized!")
        return True
    except:
        print("Failed to sync time.")
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

def display_on_lcd(lcd, time_str, temp):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("Escondido  " + time_str)
    lcd.move_to(0, 1)
    lcd.putstr("   Temp: " + convert_temp(temp) if temp else "No data")

def convert_temp(t):
    return str(round((t-273.15)*(9/5)+32)) + " F"

# Setup Wi-Fi and initial time sync
if connect_wifi():
    setup_success = sync_time()

# Initialize LCD (only once)
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
devices = i2c.scan()
lcd = I2CLcd(i2c, devices[0], 2, 16) if devices else None

while True:
    # Attempt reconnection if Wi-Fi is disconnected
    if not wlan.isconnected():
        print("Wi-Fi disconnected, attempting to reconnect...")
        setup_success = connect_wifi()
        if setup_success:
            setup_success = sync_time()  # Resync time after reconnecting
            print("Reconnected to Wi-Fi and time synced.")
        else:
            print("Failed to reconnect.")

    if setup_success and lcd:
        current_time = utime.time()

        # Update time display every minute
        if current_time - last_time_update >= time_update_interval:
            last_time_update = current_time
            local_time = utime.localtime(current_time + time_offset)
            hour, minute = local_time[3], local_time[4]
            am_pm = "AM" if hour < 12 else "PM"
            hour = hour % 12 or 12  # Convert to 12-hour format
            formatted_time = "{:02}:{:02} {}".format(hour, minute, am_pm)
            print("Time updated:", formatted_time)

        # Update weather every hour
        if current_time - last_weather_update >= weather_update_interval:
            last_weather_update = current_time
            temp = get_weather()

        # Update LCD content
        display_on_lcd(lcd, formatted_time, temp)

    # Sleep briefly to avoid high CPU usage
    time.sleep(60)
