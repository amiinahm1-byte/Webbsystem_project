import explorerhat
import time
import pygame
import serial
import adafruit_fingerprint
import paho.mqtt.client as mqtt
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
from datetime import datetime

# --- INSTÄLLNINGAR (ÄNDRA DESSA) ---
PC_IP = "192.168.1.2"  # Skriv din dators IP-adress här
#PC_IP = "192.168.0.101"  # Skriv din dators IP-adress här
DB_USER = "pi_user"
DB_PASS = "skola123"
DB_NAME = "security_db"

# --- INITIALISERING ---
pygame.mixer.init()
pygame.mixer.music.load("larm.mp3")

# MQTT Setup för Progress Bar [cite: 426, 437]
mqttc = mqtt.Client()
mqttc.connect("broker.hivemq.com", 1883) 
mqttc.loop_start()

# Fingeravtrycksläsare Setup
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

def send_realtime_data():
    """Läser analog sensor och skickar till Progress Bar via MQTT [cite: 458, 488]"""
    try:
        voltage = explorerhat.analog.one.read()
        percent = int((voltage / 5.0) * 100)
        mqttc.publish("security/sensor", str(percent))
    except:
        pass

def check_finger(expected_id):
    """Kollar om fingret finns i sensorn OCH om det matchar personen som larmade på"""
    if finger.get_image() == adafruit_fingerprint.OK:
        if finger.image_2_tz(1) == adafruit_fingerprint.OK:
            if finger.finger_search() == adafruit_fingerprint.OK:
                # Kolla om fingret som scannas har samma ID som personen som larmade på
                if finger.finger_id == expected_id:
                    try:
                        db = MySQLdb.connect(host=PC_IP, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
                        cur = db.cursor()
                        cur.execute("SELECT pseudo FROM users WHERE fingerprint_id=%s", (finger.finger_id,))
                        row = cur.fetchone()
                        db.close()
                        if row:
                            print(f"\n[OK] Välkommen tillbaka {row[0]}!")
                            return True
                    except Exception as e:
                        print(f"Databasfel: {e}")
                        return True
                else:
                    print("\n[!] Åtkomst nekad! Endast personen som aktiverade larmet kan stänga av det.")
            else:
                print("\n[!] Ej Beviljad - Okänt finger")
    return False
    
def verify_user_credentials(pseudo, password):
    """Kontrollerar användarens uppgifter och returnerar deras fingerprint_id"""
    try:
        db = MySQLdb.connect(host=PC_IP, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db.cursor()
        cur.execute("SELECT fingerprint_id FROM users WHERE pseudo=%s AND password=%s", (pseudo, password))
        row = cur.fetchone()
        db.close()
        if row:
            return row[0] # Returnerar t.ex. 65
    except Exception as e:
        print(f"Kunde inte verifiera mot DB: {e}")
    return None

def enroll_finger_with_db(location, pseudo):
    """Kopplar ett sparat finger till en redan existerande webb-användare"""
    for img_num in range(1, 3):
        print(f"Sätt finger på läsaren (prov {img_num})...", end="")
        while True:
            send_realtime_data()
            if finger.get_image() == adafruit_fingerprint.OK:
                print("Bild tagen")
                break
        if finger.image_2_tz(img_num) != adafruit_fingerprint.OK: return False
        if img_num == 1:
            time.sleep(2)
            while finger.get_image() != adafruit_fingerprint.NOFINGER: pass

    if finger.create_model() == adafruit_fingerprint.OK:
        if finger.store_model(location) == adafruit_fingerprint.OK:
            try:
                db = MySQLdb.connect(host=PC_IP, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
                cur = db.cursor()
                
                # UPDATE letar upp användaren som skapades på webben och lägger till ID:t
                sql = "UPDATE users SET fingerprint_id=%s WHERE pseudo=%s"
                cur.execute(sql, (location, pseudo))
                
                db.commit()
                db.close()
                print(f"Klart! Fingret (ID {location}) är nu kopplat till {pseudo}.")
                return True
            except Exception as e:
                print(f"Kunde inte spara i DB: {e}")
    return False

# --- HUVUDLOOP ---
try:
    while True:
        send_realtime_data() # Uppdatera Progress Bar hela tiden [cite: 357]
        print("\n--- SYSTEM-MENY ---")
        print("e) Registrera finger till användare")
        print("o) Aktivera larm")
        print("q) Avsluta")
        val = input("> ")

        if val == "e":
            pseudo = input("Ange användarnamn (pseudo) för en person som redan skapat konto på hemsidan: ")
            id_nr = int(input("Välj ID-nummer i sensorn (0-161): "))
            
            enroll_finger_with_db(id_nr, pseudo)

        elif val == "o":
            print("\n--- VERIFIERING KRÄVS FÖR ATT AKTIVERA LARM ---")
            pseudo = input("Användarnamn: ")
            password = input("Lösenord: ")
            
            # Kontrollera om användaren finns och hämta deras ID
            expected_id = verify_user_credentials(pseudo, password)
            
            if expected_id is None:
                print("[!] Fel användarnamn eller lösenord. Larmet kunde inte aktiveras.")
                continue # Hoppa tillbaka till huvudmenyn
                
            # Hämta tidpunkt för aktivering
            time_now = datetime.now().strftime("%H:%M:%S")
            
            # Skicka till webbsidan via MQTT
            mqttc.publish("security/status", f"Larmat av {pseudo}")
            mqttc.publish("security/time_armed", time_now)
            
            print(f"\n[LARM AKTIVERAT av {pseudo} kl {time_now}] Väntar på rörelse...")
            armed = True
            while armed:
                send_realtime_data()
                if explorerhat.input.one.read() == 0:
                    time.sleep(0.1) # Debounce
                    if explorerhat.input.one.read() == 0:
                        # Rörelse upptäckt! Hämta tidpunkt
                        motion_time = datetime.now().strftime("%H:%M:%S")
                        mqttc.publish("security/status", "🚨 RÖRELSE DETEKTERAD!")
                        mqttc.publish("security/time_motion", motion_time)
                        
                        print(f"\n>>> RÖRELSE DETEKTERAD kl {motion_time}! 20 sekunder på dig...")
                        start_tid = time.time()
                        access = False
                        
                        while time.time() - start_tid < 20:
                            send_realtime_data()
                            tid_kvar = int(20 - (time.time() - start_tid))
                            print(f"Tid kvar att larma av: {tid_kvar} sekunder...    ", end="\r")
                            
                            # Skicka nedräkningen live till hemsidan!
                            mqttc.publish("security/countdown", str(tid_kvar))
                            
                            if check_finger(expected_id): # Skicka med det förväntade ID:t
                                print("\n[OK] Avlarmat.")
                                disarm_time = datetime.now().strftime("%H:%M:%S")
                                mqttc.publish("security/status", "Grönt system - Säkert")
                                mqttc.publish("security/time_disarmed", disarm_time)
                                mqttc.publish("security/countdown", "0")
                                access = True
                                armed = False
                                break
                            time.sleep(0.1)

                        if not access:
                            print("\n!!! LARM STARTAR !!!")
                            mqttc.publish("security/status", "💥 LARM UTALÖST!")
                            pygame.mixer.music.play(-1)
                            
                            while not check_finger(expected_id):
                                send_realtime_data()
                                time.sleep(0.2)
                                
                            pygame.mixer.music.stop()
                            print("[OK] Larm stoppat.")
                            disarm_time = datetime.now().strftime("%H:%M:%S")
                            mqttc.publish("security/status", "Grönt system - Återställt efter larm")
                            mqttc.publish("security/time_disarmed", disarm_time)
                            mqttc.publish("security/countdown", "0")
                            armed = False
                time.sleep(0.05)
        elif val == "q": break

except KeyboardInterrupt:
    print("\nAvslutar...")
