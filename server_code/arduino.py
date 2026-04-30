
import time
import serial

# ARDUINO LISTENER

# get the available ports from the computer
def get_ports():

    ports = serial.tools.list_ports.comports()
    return ports

# find the port that Arduino is connected to
def find_arduino(ports_found):

    communication_port = 'None'
    num_connections = len(ports_found)

    for i in range(0, num_connections):
        port = ports_found[i]
        str_port = str(port)

        if 'Arduino' in str_port:
            split_port = str_port.split(' ')
            communication_port = split_port[0]
    return communication_port

def serial_read(ser) -> str:
    while ser.in_waiting <= 0:
        time.sleep(1)
        pass
    serial_data = ser.readline().decode()

    return serial_data
