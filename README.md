# envoypimonitor
Realtime and historical monitoring of envoy system

You need python and sqlite3 installed.

solar.py will grab usage data from local envoy device and insert into sqlite3 database.
makepage.py will create a html file as per the attached image.  This fits perfectly on a 3.5" touch screen for the Pi.
This does include a section at the bottom for my front gate ESP32.  I will remove that on next update for general use.



crontab config:
# Grab Envoy data
* * * * * python /home/pi/solar/solar.py
* * * * * sleep 20; python /home/pi/solar/solar.py
* * * * * sleep 40; python /home/pi/solar/solar.py

# Generate Webpage
* * * * * sleep 5; python /home/pi/solar/makepage.py


