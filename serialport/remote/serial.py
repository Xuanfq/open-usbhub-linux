from threading import Thread, Lock
import serial
from serial import Serial
import logging


PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE = 'N', 'E', 'O', 'M', 'S'
STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO = (1, 1.5, 2)
FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS = (5, 6, 7, 8)
FLOWCTRL_NONE, FLOWCTRL_RTS_CTS, FLOWCTRL_DTR_DSR, FLOWCTRL_XON_XOFF = ('None', 'RTS/CTS', 'DTR/DSR', 'XON/XOFF')

PARITY_NAMES = {
    PARITY_NONE: 'None',
    PARITY_EVEN: 'Even',
    PARITY_ODD: 'Odd',
    PARITY_MARK: 'Mark',
    PARITY_SPACE: 'Space',
}


BAUDRATES = (50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 4800,
                9600, 19200, 38400, 57600, 115200, 230400, 460800, 500000,
                576000, 921600, 1000000, 1152000, 1500000, 2000000, 2500000,
                3000000, 3500000, 4000000)
PARITIES = (PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE)
BYTESIZES = (FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS)
STOPBITS = (STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO)
DATABITS = BYTESIZES
FLOWCTRLS = (FLOWCTRL_NONE, FLOWCTRL_RTS_CTS, FLOWCTRL_DTR_DSR, FLOWCTRL_XON_XOFF)


class SerialFactory(object):

    def __init__(
        self,
        device: str,
        baudrate: int = 115200,
        bytesize: int = EIGHTBITS,
        parity: str = PARITY_NONE,
        stopbits: int = STOPBITS_ONE,
        flowcontrol: str = FLOWCTRL_NONE,
        *args,
        **kwargs,
    ) -> None:
        self.device = device
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.flowcontrol = flowcontrol
        self.serial: Serial = None
        self.serial_lock = Lock()
        self.error: bool = False

    def get_setting(self):
        return {
            "baudrate": self.baudrate,
            "bytesize": self.bytesize,
            "parity": self.parity,
            "stopbits": self.stopbits,
            "flowcontrol": self.flowcontrol,
        }

    def set_setting(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def connect(self):
        serial = serial.serial_for_url(self.device, do_not_open=True)
        serial.baudrate = self.baudrate
        serial.bytesize = self.bytesize
        serial.parity = self.parity
        serial.stopbits = self.stopbits
        serial.rtscts = False
        serial.dsrdtr = False
        serial.xonxoff = False
        if self.flowcontrol == FLOWCTRL_RTS_CTS:
            serial.rtscts = True
        elif self.flowcontrol == FLOWCTRL_DTR_DSR:
            serial.dsrdtr = True
        elif self.flowcontrol == FLOWCTRL_XON_XOFF:
            serial.xonxoff = True
        try:
            serial.open()
            with self.serial_lock:
                self.serial = serial
            self.error = False
        except serial.SerialException as e:
            logging.error(f"Could not open serial port {self.serial.name}: {e}\n")
            self.error = True
            self.disconnect()
            return False
        return True

    def disconnect(self):
        with self.serial_lock:
            if self.serial:
                try:
                    self.serial.close()
                    self.serial.exit(1)
                    self.serial = None
                except Exception as e:
                    logging.error(f"{e}")

    def get_serial(self):
        return self.serial
