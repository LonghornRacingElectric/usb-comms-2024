import sys
import glob
import serial
import time
import queue
import threading

codec = 'ascii'
baud = 115200


def available_serial_ports() -> list[str]:
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def ask_which_port(ports: list[str]) -> str:
    print()
    if len(ports) == 0:
        print("Nothing detected on any port.")
        exit(0)

    if len(ports) == 1:
        return ports[0]

    print("Choose a serial port:")
    for i in range(len(ports)):
        print(f"{i + 1} - {ports[i]}")
    print()

    i = int(input()) - 1
    if i >= 0 and i < len(ports):
        return ports[i]
    else:
        print("Invalid input.")
        exit(0)
        return ""


def open_connection(port: str) -> serial.Serial:
    cxn = serial.Serial(port, baudrate=baud, timeout=0.05)
    print(f"\nListening on serial port {port}...\n")
    return cxn


def close_connection(cxn: serial.Serial):
    cxn.close()
    print(f"\nClosed serial port {cxn.port}\n")


def loop(cxn: serial.Serial, input_queue: queue.Queue):
    while True:
        while cxn.in_waiting:
            b = cxn.read(cxn.in_waiting)
            try:
                s = b.decode(codec)
                print(s, end='', flush=True)
            except:
                pass

        if not input_queue.empty():
            user_input = input_queue.get() + "\n"
            if user_input == "\n":
                return
            cxn.write(bytes(user_input, codec))

        time.sleep(0.01)


def add_input(input_queue: queue.Queue):
    while True:
        input_queue.put(input())


def start_input_thread() -> queue.Queue:
    input_queue = queue.Queue()

    input_thread = threading.Thread(target=add_input, args=(input_queue,))
    input_thread.daemon = True
    input_thread.start()

    return input_queue


def main():
    ports = available_serial_ports()
    port = ask_which_port(ports)
    cxn = open_connection(port)
    input_queue = start_input_thread()
    loop(cxn, input_queue)
    close_connection(cxn)


main()
