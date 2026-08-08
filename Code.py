import time
import subprocess
import serial
import serial.tools.list_ports

# Bezpečné importovanie OBS knižnice, ak ju nemáte nainštalovanú, skript nespadne
try:
    from obswebsocket import obsws, requests
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False
    print("Upozornenie: Knižnica 'obs-websocket-py' nie je nainštalovaná. OBS funkcie budú neaktívne.")

BAUD_RATE = 115200
HANDSHAKE_QUERY = "WHO_ARE_YOU"
HANDSHAKE_RESPONSE = "STREAM_DECK_OK"

# Konfigurácia pripojenia k OBS Studio (WebSocket plugin v OBS)
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "vase_obs_heslo" # Zmeňte na heslo, ktoré máte nastavené v OBS

def connect_obs():
    """Vytvorí pripojenie k OBS WebSocket, ak je k dispozícii."""
    if not OBS_AVAILABLE:
        return None
    try:
        client = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
        client.connect()
        print("Úspešne pripojené k OBS WebSocket.")
        return client
    except Exception as e:
        print(f"Nepodarilo sa pripojiť k OBS: {e} (OBS pravdepodobne nie je zapnuté)")
        return None

def auto_detect_port():
    """Automaticky prejde všetky COM porty v systéme a nájde ten, ktorý odpovie na handshake."""
    print("Prehľadávam sériové porty kvôli vyhľadaniu Stream Decku...")
    while True:
        ports = serial.tools.list_ports.comports()
        for port in ports:
            port_device = port.device
            try:
                # Otvoríme port s krátkym timeoutom
                with serial.Serial(port_device, BAUD_RATE, timeout=1) as ser:
                    time.sleep(2) # Počkáme na reset mikrokontroléra pri otvorení portu
                    ser.reset_input_buffer()
                    
                    # Pošleme výzvu na identifikáciu
                    ser.write((HANDSHAKE_QUERY + "\n").encode('utf-8'))
                    
                    # Čakáme na odpoveď max 1.5 sekundy
                    start_time = time.time()
                    while time.time() - start_time < 1.5:
                        if ser.in_waiting > 0:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if line == HANDSHAKE_RESPONSE:
                                print(f"[OK] Stream Deck úspešne rozpoznaný na porte: {port_device}")
                                return port_device
            except (serial.SerialException, OSError):
                # Port môže byť chránený systémom alebo obsadený inou appkou
                continue
        
        # Ak sa port nenašiel, počkáme a skúsime to znova (napr. ak ste zariadenie práve zapojili do USB)
        print("Stream Deck sa nenašiel. Skúšam opätovne o 3 sekundy...")
        time.sleep(3)

def handle_command(cmd, obs_client):
    """Spracuje prijatý textový reťazec z hardvéru a vykoná akciu v PC."""
    cmd = cmd.strip()
    if not cmd:
        return
    print(f"Prijatý príkaz z hardvéru: {cmd}")
    
    # 1. Spustenie Spotify
    if cmd == "CMD_SPOTIFY":
        try:
            # Pokus o spustenie cez štandardný Windows URI skratku
            subprocess.Popen(["cmd", "/c", "start spotify"])
            print("Spúšťam Spotify...")
        except Exception as e:
            print(f"Chyba pri spúšťaní Spotify: {e}")
        
    # 2. Stlmenie mikrofónu v OBS
    elif cmd == "CMD_MIC_MUTE":
        if obs_client:
            try:
                current_status = obs_client.call(requests.GetInputMute(inputName="Mic/Aux"))
                new_status = not current_status.getMuted()
                obs_client.call(requests.SetInputMute(inputName="Mic/Aux", inputMuted=new_status))
                print(f"OBS Mic Mute stav zmenený na: {new_status}")
            except Exception as e:
                print(f"Chyba pri komunikácii s OBS pre mikrofón: {e}")
        else:
            print("OBS nie je pripojené, nedá sa stlmiť mikrofón.")
            
    # 3. Prepnutie scény v OBS
    elif cmd == "CMD_OBS_SCENE2":
        if obs_client:
            try:
                obs_client.call(requests.SetCurrentProgramScene(sceneName="Hra Scene"))
                print("OBS scéna úspešne prepnutá na 'Hra Scene'.")
            except Exception as e:
                print(f"Chyba pri prepínaní scény v OBS: {e}")
        else:
            print("OBS nie je pripojené.")
            
    # 4. Spustenie akejkoľvek aplikácie (napr. Poznámkový blok / test)
    elif cmd == "CMD_LAUNCH_APP":
        try:
            subprocess.Popen(["notepad.exe"])
            print("Spustený Notepad.")
        except Exception as e:
            print(f"Chyba pri spúšťaní aplikácie: {e}")

def main():
    # Pokus o počiatočné pripojenie k OBS
    obs_client = connect_obs()
    
    while True:
        # Krok A: Automaticky nájsť port cez Handshake
        active_port = auto_detect_port()
        
        # Krok B: Spustiť hlavnú čítaciu slučku pre vybraný port
        try:
            with serial.Serial(active_port, BAUD_RATE, timeout=1) as ser:
                print(f"Počúvam príkazy na porte {active_port}...")
                while True:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8', errors='ignore')
                        if line:
                            handle_command(line, obs_client)
                    
                    time.sleep(0.01)
                    
        except (serial.SerialException, OSError):
            print("!! Spojenie so zariadením bolo stratené (zariadenie bolo odpojené). Spúšťam opätovné hľadanie...")
            time.sleep(2)

if __name__ == "__main__":
    main()
