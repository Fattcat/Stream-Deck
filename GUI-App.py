import time
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import psutil

try:
    from obswebsocket import obsws, requests
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False

BAUD_RATE = 115200
HANDSHAKE_QUERY = "WHO_ARE_YOU"
HANDSHAKE_RESPONSE = "STREAM_DECK_OK"

# Konfigurácia OBS
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "vase_obs_heslo"

class StreamDeckApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DIY Stream Deck Manager")
        self.root.geometry("600x500")
        self.root.minsize(550, 450)
        
        # Premenné pre stav a pripojenie
        self.serial_connection = None
        self.is_running = True
        self.obs_client = None
        
        # Konfigurácia príkazov a aplikácií (Môžete si tu kedykoľvek upraviť cesty)
        self.button_actions = {
            "CMD_SPOTIFY": {
                "name": "Spotify",
                "type": "toggle_app",
                "path": "C:\\Users\\Public\\Desktop\\Spotify.exe", # Alebo príkaz pre spustenie
                "process": "Spotify.exe"
            },
            "CMD_MIC_MUTE": {
                "name": "Mic Mute (OBS)",
                "type": "obs_mic"
            },
            "CMD_OBS_SCENE2": {
                "name": "OBS Scene Switch",
                "type": "obs_scene",
                "scene": "Hra Scene"
            },
            "CMD_LAUNCH_APP": {
                "name": "Notepad (Toggle)",
                "type": "toggle_app",
                "path": "notepad.exe",
                "process": "notepad.exe"
            }
        }

        self.create_widgets()
        self.connect_obs_async()
        
        # Spustenie pozadia pre čítanie zo sériového portu v samostatnom vlákne
        self.serial_thread = threading.Thread(target=self.serial_worker, daemon=True)
        self.serial_thread.start()
        
        # Ukončenie okna bezpečne
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # 1. Horný panel so statusom pripojenia
        status_frame = tk.LabelFrame(self.root, text=" Stav zariadenia ", font=("Arial", 10, "bold"), padx=10, pady=10)
        status_frame.pack(fill="x", padx=15, pady=15)
        
        self.status_indicator = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.status_indicator.pack(side="left", padx=5)
        self.status_circle = self.status_indicator.create_oval(2, 2, 18, 18, fill="orange")
        
        self.status_label_text = tk.StringVar(value="Waiting for connection ...")
        self.status_label = tk.Label(status_frame, textvariable=self.status_label_text, font=("Arial", 11, "bold"))
        self.status_label.pack(side="left", padx=10)

        # 2. Stredná sekcia - Prehľad priradených tlačidiel
        config_frame = tk.LabelFrame(self.root, text=" Konfiguracija a mapovanie tlačidiel ", font=("Arial", 10, "bold"), padx=10, pady=10)
        config_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Tabuľka / Zoznam akcií
        columns = ("cmd", "action", "status")
        self.tree = ttk.Treeview(config_frame, columns=columns, show="headings", height=5)
        self.tree.heading("cmd", text="Sériový Príkaz")
        self.tree.heading("action", text="Priradená akcia / Aplikácia")
        self.tree.heading("status", text="Typ akcie")
        
        self.tree.column("cmd", width=130, anchor="w")
        self.tree.column("action", width=220, anchor="w")
        self.tree.column("status", width=130, anchor="w")
        
        for cmd, data in self.button_actions.items():
            self.tree.insert("", "end", values=(cmd, data["name"], data["type"]))
            
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # 3. Spodná sekcia - Log udalostí
        log_frame = tk.LabelFrame(self.root, text=" Systémový log ", font=("Arial", 10, "bold"), padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.log_text = tk.Text(log_frame, height=6, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)
        
    def log(self, message):
        """Bezpečné zapísanie správy do logovacieho okna v GUI."""
        def update():
            self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
            self.log_text.see("end")
        self.root.after(0, update)

    def set_status(self, text, color):
        """Aktualizácia stavového textu a farby svetielka v GUI."""
        def update():
            self.status_label_text.set(text)
            color_map = {
                "green": "#28a745",
                "orange": "#ffc107",
                "red": "#dc3545"
            }
            self.status_indicator.itemconfig(self.status_circle, fill=color_map.get(color, "gray"))
            if color == "green":
                self.status_label.config(fg="#28a745")
            elif color == "red":
                self.status_label.config(fg="#dc3545")
            else:
                self.status_label.config(fg="#e0a800")
        self.root.after(0, update)

    def connect_obs_async(self):
        """Pripojenie k OBS v pozadí, aby nezamrzlo GUI."""
        def worker():
            nonlocal self
            if not OBS_AVAILABLE:
                self.log("Knižnica obs-websocket-py nie je dostupná.")
                return
            try:
                self.obs_client = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
                self.obs_client.connect()
                self.log("Úspešne pripojené k OBS WebSocket.")
            except Exception as e:
                self.log(f"OBS sa nepodarilo pripojiť: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def is_process_running(self, process_name):
        """Skontroluje, či daný proces (napr. discord.exe) momentálne beží v OS."""
        for proc in psutil.process_iter(['name']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def toggle_application(self, exe_path, process_name):
        """Toggle logika: ak beží, zatvor ho. Ak nebeží, spusti ho."""
        if self.is_process_running(process_name):
            self.log(f"Aplikácia '{process_name}' beží. Zatváram ju...")
            terminated = False
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        p = psutil.Process(proc.info['pid'])
                        p.terminate()  # Alebo p.kill() pre vynútené ukončenie
                        terminated = True
                except Exception as e:
                    self.log(f"Chyba pri zatváraní procesu: {e}")
            if terminated:
                self.log(f"Proces '{process_name}' bol úspešne ukončený.")
        else:
            self.log(f"Spúšťam aplikáciu: {exe_path}")
            try:
                # Podporuje spustenie štandardných programov alebo systémových skratiek
                if " " in exe_path or "/" in exe_path or "\\" in exe_path:
                    subprocess.Popen([exe_path])
                else:
                    subprocess.Popen(["cmd", "/c", f"start {exe_path}"])
            except Exception as e:
                self.log(f"Chyba pri spúšťaní aplikácie: {e}")

    def execute_action(self, cmd):
        """Vykoná akciu priradenú k prijatému sériovému príkazu."""
        cmd = cmd.strip()
        if cmd not in self.button_actions:
            self.log(f"Neznámy príkaz prijatý zo zariadenia: {cmd}")
            return
            
        action_data = self.button_actions[cmd]
        self.log(f"Spracovávam akciu pre: {action_data['name']} ({cmd})")
        
        action_type = action_data["type"]
        
        if action_type == "toggle_app":
            self.toggle_application(action_data["path"], action_data["process"])
            
        elif action_type == "obs_mic":
            if self.obs_client:
                try:
                    current_status = self.obs_client.call(requests.GetInputMute(inputName="Mic/Aux"))
                    new_status = not current_status.getMuted()
                    self.obs_client.call(requests.SetInputMute(inputName="Mic/Aux", inputMuted=new_status))
                    self.log(f"OBS Mic Mute prepnutý na: {new_status}")
                except Exception as e:
                    self.log(f"Chyba OBS mikrofónu: {e}")
            else:
                self.log("OBS nie je pripojené!")
                
        elif action_type == "obs_scene":
            if self.obs_client:
                try:
                    scene_name = action_data["scene"]
                    self.obs_client.call(requests.SetCurrentProgramScene(sceneName=scene_name))
                    self.log(f"OBS scéna prepnutá na: {scene_name}")
                except Exception as e:
                    self.log(f"Chyba OBS scény: {e}")
            else:
                self.log("OBS nie je pripojené!")

    def auto_detect_port(self):
        """Automaticky prehľadáva porty a robí handshake."""
        while self.is_running:
            self.set_status("Waiting for connection ...", "orange")
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                port_device = port.device
                try:
                    with serial.Serial(port_device, BAUD_RATE, timeout=1) as ser:
                        time.sleep(2) # Počkáme na reset dosky
                        ser.reset_input_buffer()
                        ser.write((HANDSHAKE_QUERY + "\n").encode('utf-8'))
                        
                        start_time = time.time()
                        while time.time() - start_time < 1.5:
                            if ser.in_waiting > 0:
                                line = ser.readline().decode('utf-8', errors='ignore').strip()
                                if line == HANDSHAKE_RESPONSE:
                                    self.log(f"Zariadenie overené na porte: {port_device}")
                                    return port_device
                except (serial.SerialException, OSError):
                    continue
            
            time.sleep(2)

    def serial_worker(self):
        """Hlavná slučka bežiaca v pozadí, ktorá obsluhuje pripojenie a číta dáta."""
        while self.is_running:
            # 1. Nájdenie portu
            active_port = self.auto_detect_port()
            if not active_port:
                break
                
            self.set_status("DIY Stream Deck Connected", "green")
            
            # 2. Čítanie dát z portu
            try:
                with serial.Serial(active_port, BAUD_RATE, timeout=1) as ser:
                    while self.is_running:
                        if ser.in_waiting > 0:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if line:
                                self.execute_action(line)
                        time.sleep(0.01)
            except (serial.SerialException, OSError):
                self.log("Spojenie so zariadením bolo stratené.")
                self.set_status("Disconnected", "red")
                time.sleep(2)
                
        self.set_status("Error / Disconnected", "red")

    def on_close(self):
        """Bezpečné zatvorenie aplikácie a zastavenie vlákien."""
        self.is_running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk();
    app = StreamDeckApp(root)
    root.mainloop()
