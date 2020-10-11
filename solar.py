import urllib2, json, sqlite3, datetime

database_path = '/home/pi/solar/merge.db'
envoy_ip = '192.168.0.73'
frequency = 180
url = "http://" + envoy_ip + "/production.json"


#------------------------------------------------
# Connect with Envoy and grab JSON data
#------------------------------------------------

try:
    response = urllib2.urlopen(url)
    data = json.loads(response.read())

    p_now = data['production'][1]['wNow']
    p_today = data['production'][1]['whToday']
    c_now = data['consumption'][0]['wNow']
    c_today = data['consumption'][0]['whToday']
except:
    p_now = 0
    p_today = 0
    t_now = 0
    t_today = 0

con = sqlite3.connect(database_path)
cursorObj = con.cursor()

#------------------------------------------------
# Check if table exists, if not create a new one
#------------------------------------------------
cursorObj.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='envoydata' ''')
if cursorObj.fetchone()[0]!=1:
    cursorObj.execute("CREATE TABLE envoydata (id INTEGER PRIMARY KEY AUTOINCREMENT, readdate timestamp, prodnow NUMERIC, prodtoday NUMERIC, connow NUMERIC, contoday NUMERIC, freq NUMERIC)")

str_insert = """INSERT INTO 'envoydata' ('readdate', 'prodnow', 'prodtoday', 'connow', 'contoday', 'freq') VALUES (?, ?, ?, ?, ?, ?);"""
data_in = (datetime.datetime.now(),p_now,p_today,c_now,c_today,frequency)
cursorObj.execute(str_insert,data_in)
con.commit()
cursorObj.close()
