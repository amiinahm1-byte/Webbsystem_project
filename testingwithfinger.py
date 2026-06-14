import explorerhat #handles hardware
import time #time tracking
import pygame #for audio files
import serial #handles serial port
import adafruit_fingerprint #provides library hooks for interfacing with the fingerprint reader
import paho.mqtt.client as mqtt #imports client communication engine for MQTT message passing
import pymysql #provides Python hooks to interface with MySQL databases
pymysql.install_as_MySQLdb()
import MySQLdb
from datetime import datetime


PC_IP = "192.168.1.4"  #target ip addresss
DB_USER = "pi_user"
DB_PASS = "skola123"
DB_NAME = "security_db"

#iniitlize and load audio
pygame.mixer.init()
pygame.mixer.music.load("larm.mp3")

#creates MQTT client instance
mqttc = mqtt.Client()
# set Offline when disconnected
mqttc.will_set("security/heartbeat", "Offline", retain=True)

#connects to MQTT broker
mqttc.connect("broker.hivemq.com", 1883, keepalive=15) 
mqttc.loop_start()

mqttc.publish("security/heartbeat", "Online", retain=True) # Publishes that system is online

uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1) #serial port for senso
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)


#verifies scanned finger with expeected ID
def check_finger(expected_id):
    
    if finger.get_image() == adafruit_fingerprint.OK: #capture finger image from sensor
        if finger.image_2_tz(1) == adafruit_fingerprint.OK: #converts image to data template
            if finger.finger_search() == adafruit_fingerprint.OK: #searches database on the sensor chip
                
                if finger.finger_id == expected_id: #scan matches expected ID
                    try:
                        """establishes a connection to the MySQL 
                        database, creates a query cursor, 
                        fetches the username matching the scanned 
                        fingerprint ID, and closes the connection.
                        """
                        db = MySQLdb.connect(host=PC_IP, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
                        cur = db.cursor()
                        cur.execute("SELECT pseudo FROM users WHERE fingerprint_id=%s", (finger.finger_id,))
                        row = cur.fetchone()
                        db.close()
                        if row:
                            print(f"\n[OK] Welcome Back {row[0]}!") #print user
                            return True
                    except Exception as e:
                        print(f"Databasfel: {e}")
                        return True
                else:
                    print("\n[!] No access! Only the person that armed it can disarm it.")
            else:
                print("\n[!] No access - Unknown finger")
    return False
    
"""
connects to the MySQL database to validate the users username and password.
Returns their registered fingerprint ID slot number, "NONE_ASSIGNED" if the account 
exists but has no finger enrolled yet, or None if the credentials are incorrect.
"""
def verify_user_credentials(pseudo, password):
    try:
        db = MySQLdb.connect(host=PC_IP, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db.cursor()
        cur.execute("SELECT fingerprint_id FROM users WHERE pseudo=%s AND password=%s", (pseudo, password))
        row = cur.fetchone()
        db.close()
        if row:
    
            return row[0] if row[0] is not None else "NONE_ASSIGNED"
    except Exception as e:
        print(f"Couldn't verify with DB: {e}")
    return None

"""saves new finger template to sensor and database"""
def enroll_finger_with_db(location, pseudo):

    for img_num in range(1, 3): #captures two print scans of finger
        print(f"Put your finger in the sensor (prov {img_num})...", end="")
        while True:
            if finger.get_image() == adafruit_fingerprint.OK: #check for successful capture 
                print("Bild tagen")
                break
        
        #fails if character conversion drops
        if finger.image_2_tz(img_num) != adafruit_fingerprint.OK: 
            return False
        
        if img_num == 1:
            time.sleep(2) #delay between scans
            #wait for user to  lift finger
            while finger.get_image() != adafruit_fingerprint.NOFINGER: pass 

    """combines both scans into a single print model"""
    if finger.create_model() == adafruit_fingerprint.OK: 
        if finger.store_model(location) == adafruit_fingerprint.OK: #save template to sensor memory
            try:
                #connect to database and store the new ID
                db = MySQLdb.connect(host=PC_IP, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
                cur = db.cursor()
                sql = "UPDATE users SET fingerprint_id=%s WHERE pseudo=%s"
                cur.execute(sql, (location, pseudo))
                db.commit()
                db.close()
                print(f"Done! Finger (ID {location}) is now connected to {pseudo}.")
                return True
            except Exception as e:
                print(f"Couldn't save to DB: {e}")
    return False

"""verifies admin and removes all users fingers from sensor memeory and database"""
def delete_all_users_except_admin(pseudo, password):
    
    try: #connect to database and fetch role
        db = MySQLdb.connect(host=PC_IP, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db.cursor()
        cur.execute("SELECT role FROM users WHERE pseudo=%s AND password=%s", (pseudo, password))
        user_row = cur.fetchone()
        
        #if not admin, deny access, and disconnect database stream
        if not user_row or user_row[0] != "admin": 
            print("[!] Access Denied: Only the administrator can remove.")
            db.close()
            return
        print("\n[OK] Admin verified. Start removing...")
        
        #get the IDs that are not admin 
        cur.execute("SELECT fingerprint_id, pseudo FROM users WHERE role != 'admin' AND fingerprint_id IS NOT NULL")
        users_to_delete = cur.fetchall() #list of targets
     
        deleted_count = 0
        for row in users_to_delete: #iterate through the list
            f_id = row[0] #extract sensor slot
            user_pseudo = row[1] #extract pseudo
            #delete from the sensors built in memory
            if finger.delete_model(f_id) == adafruit_fingerprint.OK: 
                print(f" -> Removed finger-ID {f_id} ({user_pseudo}) from sensor.")
                deleted_count += 1
            else:
                print(f" -> [!] Couldn't remove finger-ID {f_id} from sensor (maybe already empty).")

        #wipes the fingerprint_id from database 
        cur.execute("UPDATE users SET fingerprint_id = NULL WHERE role != 'admin'")
        db.commit()
        db.close()
        
        print(f"\nRemoving Done! Total {deleted_count} fingers removed. Database is restored.")
        
    except Exception as e:
        print(f"Error happened when removing: {e}")


"""main loop"""
try:
    while True:
        
        print("\n--- SYSTEM-MENU ---")
        print("e) Register finger to user")
        print("o) Activate larm")
        print("d) Remove all user fingers (Only Admin)")
        print("q) End")
        val = input("> ")

        #finger enroll
        if val == "e":
            print("\n--- Need to verify before registering finger ---")
            #input pseudo and password
            pseudo = input("Username (pseudo): ")
            password = input("Password: ")
            account_check = verify_user_credentials(pseudo, password) #verify
            
            if account_check is None: #if wrong credentials
                print("[!] Wrong username or password. Registering was interrupted.")
                continue
            
            #enter a number to store at that ID on sensor
            id_nr = int(input("Choose ID-nummer on sensor (1-161): "))
            enroll_finger_with_db(id_nr, pseudo) #enroll the slot to database and built in memeory

        elif val == "d": # "d" to remove all user fingers
            print("\n--- Access Check ---")
            admin_pseudo = input("Enter Admin-username: ")
            admin_password = input("Enter Admin-password: ")
            #verify with admin credtials
            delete_all_users_except_admin(admin_pseudo, admin_password)

        elif val == "o": #alarm arming
            print("\n--- Need to verify before activating larm ---")
            pseudo = input("Username: ")
            password = input("Password: ")
            #extract the expected fingerprint 
            expected_id = verify_user_credentials(pseudo, password)
           
           #blocks accounts missing registered fingerprints
            if expected_id is None or expected_id == "NONE_ASSIGNED":
                print("[!] Wrong information or the account has not registered finger ye.")
                continue 
                
            
            time_now = datetime.now().strftime("%H:%M:%S") #logs system activation timestamp
            
            mqttc.publish("security/status", f"Larm by {pseudo}") #alerts web panel who armed system
            mqttc.publish("security/time_armed", time_now)
            
            print(f"\n[Larm Activated by {pseudo} at {time_now}] Waiting for movement...")
            armed = True #turn armed state to true
            while armed:
                #reads voltage drops from motion pin 
                if explorerhat.input.one.read() == 0: 
                    time.sleep(0.1) # Debounce

                    #verifies signal drop is a real event
                    if explorerhat.input.one.read() == 0: 
                        #logs when movement detected
                        motion_time = datetime.now().strftime("%H:%M:%S")
                        #notice MQTT network channels
                        mqttc.publish("security/status", "MOVEMENT DETECTED!")
                        mqttc.publish("security/time_motion", motion_time)
                        
                        print(f"\n MOVEMENT DETECTED at {motion_time}! 20 seconds to disarm...")
                        start_tid = time.time()
                        access = False
                        
                        #20 second to disarm
                        while time.time() - start_tid < 20:
                            tid_kvar = int(20 - (time.time() - start_tid)) #compute seconds remaing
                            print(f"Time left to disarm: {tid_kvar} seconds...    ", end="\r")
                            
                            #broadcast countdown to webapage
                            mqttc.publish("security/countdown", str(tid_kvar))
                            
                            """
                            executes when the correct user successfully scans their finger to disarm the system.
                            Logs the event locally, broadcasts the secure status and timestamp to the web panel via MQTT,
                            resets the interface countdown timer, and breaks out of the alarm monitoring loop.
                            """
                            if check_finger(expected_id): 
                                print("\n[OK] Disarmed.")
                                disarm_time = datetime.now().strftime("%H:%M:%S")
                                mqttc.publish("security/status", "Green System - Secured")
                                mqttc.publish("security/time_disarmed", disarm_time)
                                mqttc.publish("security/countdown", "0")
                                access = True
                                armed = False
                                break
                            time.sleep(0.1)

                        """
                        triggers when the 20-second period expires without a valid fingerprint scan.
                        Broadcasts the alarm breach status, starts infinite loops of the siren audio,
                        until the correct authorized user scans to silence and disarm.
                        """

                        if not access:
                            print("\nLARM STARTED!")
                            mqttc.publish("security/status", "LARM STARTED!")
                            pygame.mixer.music.play(-1) #infinite loop
                            
                            while not check_finger(expected_id):
                                
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
