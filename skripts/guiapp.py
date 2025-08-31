class ArduinoApp:
    def connect(self):
        port = self.port_cb.get()
        self.ser = serial.Serial(port, 9600, timeout=1)
        self.running = True
        self.thread = threading.Thread(target=self.read_serial, daemon=True)
        self.thread.start()

    def send_params(self):
        lam = self.lambda_var.get()
        minw = self.min_width_var.get()
        maxw = self.max_width_var.get()
        cmd = f"LAMBDA:{lam};MINW:{minw};MAXW:{maxw}\n"
        self.ser.write(cmd.encode('utf-8'))

    def read_serial(self):
        while self.running:
            line = self.ser.readline().decode('utf-8').strip()
            if line.startswith("Impuls @"):
                self.update_stats(line)
            self.log(line)
