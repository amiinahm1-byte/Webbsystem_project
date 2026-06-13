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
PC_IP = "192.168.1.4"  # Skriv din dators IP-adress här
DB_USER = "pi_user"
DB_PASS = "skola123"
DB_NAME = "security_db"

# --- INITIALISERING ---
pygame.mixer.init()
pygame.mixer.music.load("larm.mp3")

# MQTT Setup med Last Will och Heartbeat
mqttc = mqtt.Client()

# 1. Definiera "Sista viljan" (Last Will) om Pajen dör plötsligt
# Om anslutningen bryts kommer HiveMQ automatiskt skicka "Offline" till hemsidan
mqttc.will_set("security/heartbeat", "Offline", retain=True)

# 2. Anslut med keepalive=15 (Brokern kollar var 15:e sekund att vi lever)
mqttc.connect("broker.hivemq.com", 1883, keepalive=15) 
mqttc.loop_start()

# 3. Skicka direkt ut att systemet är Online och uppkopplat nu
mqttc.publish("security/heartbeat", "Online", retain=True)

# Fingeravtrycksläsare Setup
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)


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
                            print(f"\n[OK] Welcome Back {row[0]}!")
                            return True
                    except Exception as e:
                        print(f"Databasfel: {e}")
                        return True
                else:
                    print("\n[!] No access! Only the person that armed it can disarm it.")
            else:
                print("\n[!] No access - Unknown finger")
    return False
    
def verify_user_credentials(pseudo, password):
    """Kontrollerar användarens uppgifter och returnerar deras fingerprint_id. 
    Används även för att bekräfta att användaren finns vid finger-registrering."""
    try:
        db = MySQLdb.connect(host=PC_IP, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db.cursor()
        cur.execute("SELECT fingerprint_id FROM users WHERE pseudo=%s AND password=%s", (pseudo, password))
        row = cur.fetchone()
        db.close()
        if row:
            # Returnerar ID om det finns, eller strängen "NONE_ASSIGNED" om fältet är NULL (nytt konto)
            return row[0] if row[0] is not None else "NONE_ASSIGNED"
    except Exception as e:
        print(f"Couldn't verify with DB: {e}")
    return None

def enroll_finger_with_db(location, pseudo):
    """Kopplar ett sparat finger till en redan existerande webb-användare"""
    for img_num in range(1, 3):
        print(f"Put your finger in the sensor (prov {img_num})...", end="")
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
                print(f"Done! Finger (ID {location}) is now connected to {pseudo}.")
                return True
            except Exception as e:
                print(f"Couldn't save to DB: {e}")
    return False

def delete_all_users_except_admin(pseudo, password):
    """Verifierar admin och raderar alla vanliga användares fingrar från sensorn och DB"""
    try:
        db = MySQLdb.connect(host=PC_IP, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db.cursor()
        
        # 1. Kontrollera om inloggad person är admin
        cur.execute("SELECT role FROM users WHERE pseudo=%s AND password=%s", (pseudo, password))
        user_row = cur.fetchone()
        
        if not user_row or user_row[0] != "admin":
            print("[!] Access Denied: Only the administrator can remove.")
            db.close()
            return

        print("\n[OK] Admin verified. Start removing...")
        
        # 2. Hämta alla fingerprint_id som INTE tillhör admins och inte är NULL
        cur.execute("SELECT fingerprint_id, pseudo FROM users WHERE role != 'admin' AND fingerprint_id IS NOT NULL")
        users_to_delete = cur.fetchall()
        
        # 3. Loopa och radera från hårdvarusensorn
        deleted_count = 0
        for row in users_to_delete:
            f_id = row[0]
            user_pseudo = row[1]
            
            if finger.delete_model(f_id) == adafruit_fingerprint.OK:
                print(f" -> Removed finger-ID {f_id} ({user_pseudo}) from sensor.")
                deleted_count += 1
            else:
                print(f" -> [!] Couldn't remove finger-ID {f_id} from sensor (maybe already empty).")

        # 4. Radera kopplingarna i databasen för alla som inte är admin
        cur.execute("UPDATE users SET fingerprint_id = NULL WHERE role != 'admin'")
        db.commit()
        db.close()
        
        print(f"\nRemoving Done! Total {deleted_count} fingers removed. Database is restored.")
        
    except Exception as e:
        print(f"Error happened when removing: {e}")

# --- HUVUDLOOP ---
try:
    while True:
        send_realtime_data() # Uppdatera Progress Bar hela tiden
        print("\n--- SYSTEM-MENY ---")
        print("e) Register finger to user")
        print("o) Activate larm")
        print("d) Remove all user fingers (Only Admin)")
        print("q) End")
        val = input("> ")

        if val == "e":
            print("\n--- Need to verify before registering finger ---")
            pseudo = input("Username (pseudo): ")
            password = input("Password: ")
            
            # Kontrollera om användarnamnet och lösenordet är rätt
            account_check = verify_user_credentials(pseudo, password)
            
            if account_check is None:
                print("[!] Wrong username or password. Registering was interrupted.")
                continue # Hoppa tillbaka till huvudmenyn
                
            id_nr = int(input("Choose ID-nummer on sensor (1-161): "))
            enroll_finger_with_db(id_nr, pseudo)

        elif val == "d":
            print("\n--- Access Check ---")
            admin_pseudo = input("Enter Admin-username: ")
            admin_password = input("Enter Admin-password: ")
            delete_all_users_except_admin(admin_pseudo, admin_password)

        elif val == "o":
            print("\n--- Need to verify before activating larm ---")
            pseudo = input("Username: ")
            password = input("Password: ")
            
            # Kontrollera om användaren finns och hämta deras ID
            expected_id = verify_user_credentials(pseudo, password)
            
            # Om kontot är helt nytt kan id vara "NONE_ASSIGNED", vilket också ska blockeras vid larmstart
            if expected_id is None or expected_id == "NONE_ASSIGNED":
                print("[!] Wrong information or the account has not registered finger ye.")
                continue 
                
            # Hämta tidpunkt för aktivering
            time_now = datetime.now().strftime("%H:%M:%S")
            
            # Skicka till webbsidan via MQTT
            mqttc.publish("security/status", f"Larm by {pseudo}")
            mqttc.publish("security/time_armed", time_now)
            
            print(f"\n[Larm Activated by {pseudo} at {time_now}] Waiting for movement...")
            armed = True
            while armed:
                send_realtime_data()
                if explorerhat.input.one.read() == 0:
                    time.sleep(0.1) # Debounce
                    if explorerhat.input.one.read() == 0:
                        # Rörelse upptäckt! Hämta tidpunkt
                        motion_time = datetime.now().strftime("%H:%M:%S")
                        mqttc.publish("security/status", "MOVEMENT DETECTED!")
                        mqttc.publish("security/time_motion", motion_time)
                        
                        print(f"\n>>> MOVEMENT DETECTED at {motion_time}! 20 seconds to disarm...")
                        start_tid = time.time()
                        access = False
                        
                        while time.time() - start_tid < 20:
                            send_realtime_data()
                            tid_kvar = int(20 - (time.time() - start_tid))
                            print(f"Time left to disarm: {tid_kvar} seconds...    ", end="\r")
                            
                            # Skicka nedräkningen live till hemsidan!
                            mqttc.publish("security/countdown", str(tid_kvar))
                            
                            if check_finger(expected_id): # Skicka med det förväntade ID:t
                                print("\n[OK] Disarmed.")
                                disarm_time = datetime.now().strftime("%H:%M:%S")
                                mqttc.publish("security/status", "Green System - Secured")
                                mqttc.publish("security/time_disarmed", disarm_time)
                                mqttc.publish("security/countdown", "0")
                                access = True
                                armed = False
                                break
                            time.sleep(0.1)

                        if not access:
                            print("\nLARM STARTED!")
                            mqttc.publish("security/status", "LARM STARTED!")
                            pygame.mixer.music.play(-1)
                            
                            while not check_finger(expected_id):
                                send_realtime_data()
                                time.sleep(0.2)
                                
                            pygame.mixer.music.stop()
                            print("[OK] Larm Disarmed.")
                            disarm_time = datetime.now().strftime("%H:%M:%S")
                            mqttc.publish("security/status", "Green System - Restored after larm")
                            mqttc.publish("security/time_disarmed", disarm_time)
                            mqttc.publish("security/countdown", "0")
                            armed = False
                time.sleep(0.05)
        elif val == "q": break

except KeyboardInterrupt:
    print("\nEnding...")
