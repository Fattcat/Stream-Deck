# pip install pyserial
import serial.tools.list_ports

def find_stream_deck_port():
    # Príklad VID a PID pre čip CP2102 (upravte si podľa vášho mikrokontroléra)
    TARGET_VID = 0x10C4  # Silicon Labs CP2102
    TARGET_PID = 0xEA60
    
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"Nájdený port: {port.device} | Description: {port.description} | VID:PID = {port.vid}:{port.pid}")
        if port.vid == TARGET_VID and port.pid == TARGET_PID:
            print(f"-> Úspešne nájdený Stream Deck na porte: {port.device}")
            return port.device
            
    return None

port_name = find_stream_deck_port()
if not port_name:
    print("DIY Stream Deck NOT FOUND ! Check the connection")
