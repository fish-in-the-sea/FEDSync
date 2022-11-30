import sys, time, serial
from threading import Thread
import matplotlib.pyplot as plt
import matplotlib.animation as anim
from serial.tools import list_ports


def get_avalible_ports():
    """
    Gets a list of all active serial
    """
    return [ports for ports, *_ in list_ports.comports() if ports != "COM3"]

port = get_avalible_ports()[0]

mySerial = serial.Serial(port, 57600)
#mySerial.write(b'Time\0')
#mySerial.write(bytes(f'{datetime.datetime.now().isoformat()}','utf-8'))
#mySerial.write(b'\0')
print(port)

def echo(port,n=5):
    text = 'a'*n + '\0'
    start = time.perf_counter()
    port.write(bytes(text,'utf-8'))
    while not port.in_waiting:
        pass
    port.read_until(b'\0')
    return time.perf_counter() - start

data_x = []
data_y = []



def fetch_data(data_x,data_y):
    with open('timeing.csv','w') as file:
        file.write("Number of Characters, Time (s)\n")
        time.sleep(1)
        for n in range(1,100,10):
            for i in range(10):
                timer = echo(mySerial)
                
                data_x.append(n)
                data_y.append(timer)
                file.write(f'{n}, {timer}\n')


t = Thread(target=fetch_data, args=[data_x,data_y])
t.start()

def get_data(data_x,data_y):
    def update(i):
        x = [*data_x]
        y = [*data_y]
        x = x[:min(len(x),len(y))]
        y = y[:min(len(x),len(y))]
        
        plt.clf()

        plt.scatter(x,y)
    ani = anim.FuncAnimation(plt.gcf(), update, interval=100)
    print("I was run")
    plt.show()

get_data(data_x,data_y)

t.join()