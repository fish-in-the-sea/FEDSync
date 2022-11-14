import datetime
import os.path
import queue
import sys
from threading import Thread

import serial
from PyQt5.QtCore import QObject, QSettings, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication
from serial.tools import list_ports


def time_stamp():
    """
    Generates a time stamp to use in logging
    Warning, this is not accurate to the fed unit events and is intead for when the computer
    Recives the time
    Accurate time stamps for FED events are pulled from serial
    """
    return datetime.datetime.now().time().isoformat("milliseconds")


headers = (
    ",".join([
        "MM:DD:YYYY hh:mm:ss",
        "LibaryVersion_Sketch",
        "Device_Number",
        "Battery_Voltage",
        "Motor_Turns",
        "Trial_Info",
        "FR",
        "Event",
        "Active_Poke",
        "Left_Poke_Count",
        "Right_Poke_Count",
        "Pellet_Count",
        "Block_Pellet_Count",
        "Retrieval_Time",
        "Poke_Time",
    ])
    + "\n"
)
"""
Headers for the CSV exported for the FED3 unit
"""


def get_avalible_ports():
    """
    Gets a list of all active serial
    """
    return [port for port, *_ in list_ports.comports() if port not in ["COM3"]]


def ids():
    count = 0
    while True:
        yield count
        count += 1
"""
Generator to create ID's for the fed units reading and writing to serial
"""

def next_file(file_name):
    if file_name[-1] == '/':
        path = f'{file_name.split(".")[0]}{datetime.datetime.today().strftime("%Y-%m-%d")}'
    else:
        path = f'{file_name.split(".")[0]}-{"-".join(str(i) for i in datetime.datetime.today().isocalendar())}'
    count = 1
    file = path + f'_run-{count}.csv'
    while os.path.exists(file):
        count +=1
        file = path + f'_run-{count}.csv'
    return file

class Serial_Manager:
    """
    Manager for the serial connection,
    allows blocking to happen between serial operations to prevent data mashing
    Implements a Queue system for reads and writes
    """
    
    def __init__(self, port):
        self.lock = False
        self.port = port
        self.serial = serial.Serial(self.port, 57600, timeout=2)
        self.call_queue = queue.Queue()
        self.uuid_gen = ids()

    def wait(self):
        """
        Waits till the serial connection is availible for use and blocks it
        Prevents overlapping on the connection
        """
        id = next(self.uuid_gen)
        self.call_queue.put(id)
        while self.call_queue.queue[0] != id:
            pass

    def next(self):
        """
        Releases the Serial connection for the next process
        """
        self.call_queue.get()

    def is_availible(self):
        """
        checks if there is serial data in the buffer
        """
        return self.serial.in_waiting

    def read(self):
        """
        Reads a string off the Serial Connection,
        The String must end in a null terminating byte
        """
        if self.lock:
            return
        self.wait()
        output = self.serial.read_until(b"\0").decode("utf-8")
        self.next()
        return output
    
    def send_time(self, time):
        """
        Syncronizes the FED3 unit to the System Time
        """
        if self.lock:
            return
        self.wait()  # pause till open queue
        self.serial.write(b"Time\0")
        self.serial.write(bytes(f"{datetime.datetime.now().isoformat()}\0", "utf-8"))
        output = self.serial.read_until(b"\0").decode("utf-8")
        self.next()  # allow the next tiem to queue
        return output

    def reset_fed(self):
        """
        Tells the FED3 unit to reset the internal counters
        """
        if self.lock:
            return
        self.wait()
        self.serial.write(b"Reset\0")
        self.next()

    def close(self):
        """
        Closes the Connection to the FED3 unit,
        Once this is called it will prevent new calls from being added to the queue
        It will attempt to finnish all communication currently on the queue and then close the connection
        """
        self.lock = True
        self.wait()

        self.serial.close()


class Backend(QObject):
    """
    This is the class that allows the python code to interface with the GUI
    The GUI is defined in main.qml
    """

    load = pyqtSignal()
    """
    Signal sent to the GUI to say when the backend has been initialized
    """

    def __init__(self, engine):
        """
        Constructer for backend class
        Assigns default values for all the properties
        """
        super().__init__()
        self.record = False
        self.engine = engine
        self.log_lines = []
        self.file_name = ""
        self.file = None
        self.port = None
        self.ports = []
        self.serial = None

        engine.rootObjects()[0].setProperty("backend", self)
        self.load.emit()
        # attatches the backend to the QUI and emits the load signal

    @pyqtProperty(bool)
    def recording(self):
        """
        Signals to the GUI if the backend is recording
        """
        return self.record

    # used so the GUI can check if we are recording or not

    @pyqtSlot(int)
    def set_port(self, port):
        """
        Sets the port in from the GUI to the backend
        """
        self.port = self.ports[port]
        if self.serial and self.serial.port != self.port:
            self.serial.close()
            self.serial = Serial_Manager(self.port)

    @pyqtSlot()
    def get_file(self):
        """
        Gets the currently set file from the backend
        """
        return self.file_name

    @pyqtSlot(str)
    @pyqtSlot(str, bool)
    def set_file(self, file_name, quiet=True):
        """
            Sets the name of the file to the backend
        """
        if not quiet:
            self.log_lines.append("file path set")
            self.console_log(file_name)
        self.file_name = file_name
        if sys.platform.startswith("win"):
            self.file_name = self.file_name.lstrip("/")

    @pyqtSlot()
    def sync(self):
        """
        Tells the serial connection to send the time frame
        """
        if self.serial != None:
            time = self.serial.send_time(
                datetime.datetime.now().isoformat(timespec="milliseconds")
            )
            if time != None:
                self.log_lines.append("Synced time to")
                self.console_log(time)
            else:
                self.console_log("Failed to Sync")
                #failed to sync the time
        else:
            self.log_lines.append("Failed to Sync")
            self.console_log("Error: No Connection")
            #Errors if there is no serial connection

    @pyqtSlot()
    def record(self):
        """
        Initializes and stops the Recording
        When recording starts open the file and append the headers
        will reset the interal counters in the fed3 unit
        """
        if self.serial == None:
            self.log_lines.append("Failed to Record")
            self.console_log("Error: No Connection")
            return
            #If there in no serial connection error

        self.record = not self.record
        if self.record:
            if self.serial != None:
                self.serial.reset_fed()
                filename = next_file(self.file_name)
                self.file = open(filename, "w")
                self.file.write(headers)
        else:
            self.file.flush()
            self.file.close()
            #Closes the files if recording ended
        self.console_log("Recording Started" if self.record else "Recording Stopped")

    def set_options(self, options):
        """
        sets the port options to the backend
        """
        self.ports = options
        self.engine.rootObjects()[0].setProperty("options", options)
        if len(options):
            self.port = options[0]
            self.serial = Serial_Manager(self.port)

    def console_log(self, msg):
        """
        Used to log data to the console to the gui
        """
        self.log_lines.append(f"{msg:45}{time_stamp()}")
        while len(self.log_lines) > 100:
            del self.log_lines[0]
        self.engine.rootObjects()[0].setProperty(
            "log_text", "\n".join(self.log_lines + ["", ""])
        )

def watch_serial(backend, exit):
    """
    Watches the Serial connection to record data from the fed unit
    Runs in a seperate thread from the GUI
    """
    while exit[0]:
        if backend.serial != None:
            if backend.serial.is_availible():
                output = backend.serial.read()
                if output != None:
                    backend.console_log(output)
                    if backend.recording and backend.file:
                        backend.file.write(output.strip("\0"))

    if backend.serial != None:
        backend.serial.close()
    #once the gui terminates the serial should be closed

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("Haraway Lab")
    app.setOrganizationDomain("https://hardawaylab.org/")
    app.setApplicationName("FED3")
    #Settings about the app

    engine = QQmlApplicationEngine()
    engine.quit.connect(app.quit)
    engine.load("srcs/main.qml")
    #loads QML into the python to start the GUI

    backend = Backend(engine)
    #Attaches the Backend to the engine

    backend.set_options(get_avalible_ports())
    #Connects Ports to Backend

    running = [True]
    t = Thread(target=watch_serial, args=[backend, running])
    t.start()
    #Starts a tread to run the serial watch

    code = app.exec()
    running[0] = False
    t.join()
    #Once the GUI closes it will tell the serial watch to end
    #Close the app once it ends

    sys.exit(code)
    # Exits when the app is closed

if __name__ == "__main__":
    main()
