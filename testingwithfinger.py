import explorerhat
import time
import pygame
import serial
import adafruit_fingerprint

# --- SETUP ---
pygame.mixer.init()
pygame.mixer.music.load("larm.mp3")

uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

def check_finger():
    """Kollar om fingret finns i minnet och ger feedback"""
    i = finger.get_image()
    if i == adafruit_fingerprint.OK:
        if finger.image_2_tz(1) == adafruit_fingerprint.OK:
            if finger.finger_search() == adafruit_fingerprint.OK:
                return True
            else:
                # Fingret lästes men fanns inte i databasen
                print("\n[!] Ej Beviljad - Okänt finger")
                return False
    return False

def enroll_finger(location):
    """Sparar ett nytt finger"""
    for img_num in range(1, 3):
        print(f"Sätt fingret på läsaren (prov {img_num} av 2)...", end="")
        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Bild tagen")
                break
        
        if finger.image_2_tz(img_num) != adafruit_fingerprint.OK:
            print("Kunde inte skapa mall.")
            return False
        
        if img_num == 1:
            print("Ta bort fingret...")
            time.sleep(2)
            while finger.get_image() != adafruit_fingerprint.NOFINGER:
                pass

    if finger.create_model() == adafruit_fingerprint.OK:
        if finger.store_model(location) == adafruit_fingerprint.OK:
            print(f"Sparat på ID #{location}!")
            return True
    print("Misslyckades med att spara.")
    return False

# --- HUVUDPROGRAM ---
try:
    while True:
        print("\n--- MENY ---")
        print("e) Registrera nytt finger (Enroll)")
        print("o) Starta larmet (Arm system)")
        print("q) Avsluta")
        val = input("> ")

        if val == "e":
            try:
                id_nr = int(input("Välj ID-nummer (0-161): "))
                enroll_finger(id_nr)
            except ValueError:
                print("Ange ett giltigt nummer.")

        elif val == "o":
            print("\n[SYSTEMET ÄR NU LADDAT] Väntar på rörelse...")
            armed = True
            while armed:
                if explorerhat.input.one.read() == 0:
                    print("\n>>> RÖRELSE DETEKTERAD! 20 sekunder kvar...")
                    
                    access_granted = False
                    start_tid = time.time()
                    
                    while time.time() - start_tid < 20:
                        print(f"Tid: {int(20 - (time.time() - start_tid))}s", end="\r")
                        
                        if check_finger():
                            print("\n[OK] Åtkomst beviljad. Systemet avlarmat.")
                            access_granted = True
                            armed = False
                            break
                        
                        time.sleep(0.1)

                    if not access_granted:
                        print("\n!!! LARM STARTAR !!!")
                        pygame.mixer.music.play(-1)
                        print("Scanna rätt finger för att tysta larmet...")
                        while not check_finger():
                            time.sleep(0.2)
                        
                        pygame.mixer.music.stop()
                        print("[OK] Larm stoppat. Systemet avlarmat.")
                        armed = False
                
                time.sleep(0.05)

        elif val == "q":
            break

except KeyboardInterrupt:
    print("\nAvslutar.")
