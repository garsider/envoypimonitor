import urllib2, json, sqlite3, datetime, calendar, requests, time
from bs4 import BeautifulSoup
from datetime import timedelta
from datetime import date

dayrate = 0.83952
import_tarrif = 0.28809
export_tarrif = 0.20
database_path = '/home/pi/solar/merge.db'
webpage_path = '/var/www/html/index.php'
gate_url = 'http://192.168.0.6'

# Function to pull total tarrif, total production and total consumption from a given SELECT statement where colums returned are prodnow and connow
def CalculateTarrif(records):
    read_total = 0
    prod_total = 0
    con_total = 0
    for row in records:
        prod_total = prod_total + row[0]
        con_total = con_total + row[1]
        if row[0] > row[1]:
            read_total = read_total + ((row[0] - row[1])/1000/r_freq) * export_tarrif
        else:
            read_total = read_total + ((row[0] - row[1])/1000/r_freq) * import_tarrif

    return read_total, prod_total, con_total

#----------------------------------------------------------
#Grab the last read from the envoy entered in the database
#----------------------------------------------------------
con = sqlite3.connect(database_path)
cursorObj = con.cursor()

cursorObj.execute("""SELECT * FROM envoydata WHERE id = (SELECT MAX(id) FROM envoydata)""")
records = cursorObj.fetchall()
for row in records:
    p_now = row[2]
    p_today = row[3]
    c_now = row[4]
    c_today = row[5]
    r_freq = row[6]

str_webpage = ""
str_webpage = str_webpage + "<!DOCTYPE html>\n<html>\n<head>\n"
str_webpage = str_webpage + "<style>\nbody {\n   font-size: medium;\n   width: 320px;\n   background-color: black;\n   font-family:'Courier New';\n   color:white;\n}\n"
str_webpage = str_webpage + "</style>\n"

if p_now > c_now:
    solar_cost = (((p_now - c_now) / 1000) / r_freq) * export_tarrif
    str_webpage = str_webpage + "<link rel=\"icon\" href=\"/img/sun.png\"><title>OUT:" + format((p_now-c_now)/1000, '.1f') + "kW</title><meta http-equiv=\"refresh\" content=\"28\"></head>\n"
    str_webpage = str_webpage + "<body>\n<table style=\"border:1px solid green;\">\n"
    str_webpage = str_webpage + "<tr><th colspan=\"2\" style=\"background-color:green;font-size: x-large;\">EXPORTING</th></tr>\n"
else:
    solar_cost = (((p_now - c_now) / 1000) / r_freq) * import_tarrif
    str_webpage = str_webpage + "<link rel=\"icon\" href=\"/img/sun.png\"><title>IN:" + format((p_now-c_now)/1000, '.1f') + "kW</title><meta http-equiv=\"refresh\" content=\"28\"></head>\n"
    str_webpage = str_webpage + "<body>\n<table style=\"border:1px solid red;\">\n"
    str_webpage = str_webpage + "<tr><th colspan=\"2\" style=\"background-color:red;font-size: x-large;\">IMPORTING</th></tr>\n"

#-----------------------------------------------------
# Build Real-Time View
#-----------------------------------------------------
str_webpage = str_webpage + "<tr><td>Current Production:</td><td style=\"text-align:right\">" + format(p_now/1000, '.3f') + "kW</td></tr>\n"
str_webpage = str_webpage + "<tr><td>Current Consumption:</td><td style=\"text-align:right\">" + format(c_now/1000, '.3f') + "kW</td></tr>\n"
str_webpage = str_webpage + "<tr><td>Net Power:</td><td style=\"text-align:right\">" + format((p_now-c_now)/1000, '.3f') + "kW</td></tr>\n"

if solar_cost >= 0:
    str_webpage = str_webpage + "<tr><td>Cost/Income this hour:</td><td style=\"text-align:right;color:green\">$" + format(solar_cost * r_freq, '.2f') + "</td></tr>\n"
else:
    str_webpage = str_webpage + "<tr><td>Cost/Income this hour:</td><td style=\"text-align:right;color:red\">$" + format(solar_cost * r_freq, '.2f') + "</td></tr>\n"

#-----------------------------------------------------
# Build Todays View
#-----------------------------------------------------
str_webpage = str_webpage + "<tr><th colspan=\"2\" style=\"background-color:dimgrey;\">Today: " + datetime.datetime.now().strftime('%d-%m-%Y') + "</th></tr>\n"

str_webpage = str_webpage + "<tr><td>Production Today:</td><td style=\"text-align:right\">" + format(p_today/1000, '.1f') + "kWh</td></tr>\n"
str_webpage = str_webpage + "<tr><td>Consumption Today:</td><td style=\"text-align:right\">" + format(c_today/1000, '.1f') + "kWh</td></tr>\n"

cursorObj.execute("""SELECT prodnow, connow FROM envoydata WHERE DATE(readdate) = DATE(DATETIME('now','localtime'))""")
records = cursorObj.fetchall()

Today_Data = CalculateTarrif(records)

if (Today_Data[0]-dayrate) >= 0:
    strColour = "green"
else:
    strColour = "red"

str_webpage = str_webpage + "<tr><td>Income Today(" + str(len(records)/r_freq) + "hrs):</td><td style=\"text-align:right;color:" + strColour + "\">$" + format(Today_Data[0]-dayrate, '.2f') + "</td></tr>\n"

#-----------------------------------------------------
# Build 7 Day View
#-----------------------------------------------------
str_webpage = str_webpage + "<tr><th colspan=\"2\" style=\"background-color:dimgrey;\">Last 7 days</th></tr>\n"
str_webpage = str_webpage + "<tr><td colspan=\"2\" style=\"text-align: center;\">\n<table align=\"center\" style=\"font-size: small;border-collapse: collapse;\">\n"


i = 1
str_row1 = ""
str_row2 = ""
str_row3 = ""
str_row4 = ""

while i < 8:
    previous_date = date.today() - timedelta(days=i)
    cursorObj.execute("""SELECT prodnow, connow FROM envoydata WHERE readdate >= DATE('now','-""" + str(i) + """ days','localtime') AND readdate < DATE('now','-""" + str(i - 1) + """ days','localtime')""")
    records = cursorObj.fetchall()

    Days_Data = CalculateTarrif(records)

    if Days_Data[0]-dayrate >= 0:
        strColour = "green"
    else:
        strColour = "red"

    str_row1 = str_row1 + "<td style=\"text-align: center;border:1px solid white;\">" + previous_date.strftime('%d') + "</td>\n"
    str_row2 = str_row2 + "<td style=\"font-size: 11px;text-align: right;background-color:" + strColour + ";border:1px solid white;\">$" + format(float(Days_Data[0]) - dayrate, '.2f') + "</td>\n"
    str_row3 = str_row3 + "<td style=\"font-size: 12px;text-align: right;border:1px solid white;\">" + format((Days_Data[1]/1000)/r_freq, '.2f') + "</td>\n"
    str_row4 = str_row4 + "<td style=\"font-size: 12px;text-align: right;border:1px solid white;\">" + format((Days_Data[2]/1000)/r_freq, '.2f') + "</td>\n"

    i = i + 1

str_webpage = str_webpage + "<tr>" + str_row1 + "</tr>\n"
str_webpage = str_webpage + "<tr>" + str_row2 + "</tr>\n"
str_webpage = str_webpage + "<tr>" + str_row3 + "</tr>\n"
str_webpage = str_webpage + "<tr>" + str_row4 + "</tr>\n"

str_webpage = str_webpage + "</table></td></tr>"

#-----------------------------------------------------
# Build Month View
#-----------------------------------------------------
str_webpage = str_webpage + "<tr><th colspan=\"2\" style=\"background-color:dimgrey;\">This Month (" + datetime.datetime.now().strftime('%B') + ")</th></tr>\n"
str_webpage = str_webpage + "<tr><td>Connection($" + format(dayrate, '.2f') + "/day):</td><td style=\"text-align:right\">$" + format(dayrate * datetime.datetime.now().day, '.2f') + "</td></tr>\n"

daycount = datetime.datetime.today().day

cursorObj.execute("""SELECT prodnow, connow FROM envoydata WHERE strftime('%m',readdate) = '""" + str(datetime.datetime.now().month).zfill(2) + "'""")
records = cursorObj.fetchall()

Month_Data = CalculateTarrif(records)

if Month_Data[0] >= 0 :
    strColour = "green"
else:
    strColour = "red"

str_webpage = str_webpage + "<tr><td>Cost/Income(" + str(daycount) + " days):</td><td style=\"text-align:right;color:" + strColour + ";\">$" + format(Month_Data[0], '.2f') + "</td></tr>\n"

if (dayrate * datetime.datetime.now().day) - Month_Data[0] >= 0:
    strColour = "red"
else:
    strColour = "green"

str_webpage = str_webpage + "<tr><td>Monthly Bill(to date):</td><td style=\"text-align:right;color:" + strColour + "\">$" + format((dayrate * datetime.datetime.now().day) - Month_Data[0], '.2f') + "</td></tr>\n</table>"
#-----------------------------------------------------
#End of Solar Page Build
#-----------------------------------------------------


#-----------------------------------------------------
#Check for front gate server and grab current status
#-----------------------------------------------------
try:
    response = requests.get(gate_url)
    soup = BeautifulSoup(response.text, "html.parser")
    gate_status = soup.find_all('p')[1]

    str_webpage = str_webpage + "<table><tr><td colspan=\"2\">Front Gate: " + str(gate_status)[3:-4] + "</th></tr>\n"
except:
    str_webpage = str_webpage + "<table><tr><td colspan=\"2\">Front Gate: Server Down!</th></tr>\n"

str_webpage = str_webpage + "<tr><th colspan=\"2\" style=\"background-color:dimgrey;font-size: small;\">Last Updated: " + str(datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')) + "</th></tr>\n"

str_webpage = str_webpage + "</table></body></html>"

#-----------------------------------------------------
#Write web page to file
#-----------------------------------------------------

f=open(webpage_path,"w")
f.write(str_webpage)
f.close()
cursorObj.close()

#-----------------------------------------------------
# END
#-----------------------------------------------------
