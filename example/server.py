from threading import Thread, Lock
import serial
from serial import Serial
from serial.threaded import Protocol, ReaderThread
import socket
import logging

logger = logging.getLogger(__file__)


class SerialFactory(object):
    class ParityType:
        PARITY_NONE = "N"
        PARITY_EVEN = "E"
        PARITY_ODD = "O"
        PARITY_SPACE = "S"
        PARITY_MARK = "M"

    class FlowControl:
        FLOW_CONTROL_NONE = 0
        FLOW_CONTROL_RTS_CTS = 1
        FLOW_CONTROL_XON_XOFF = 2
        FLOW_CONTROL_DTR_DSR = 3

    class DataBits:
        DATA_BITS_5 = 5
        DATA_BITS_6 = 6
        DATA_BITS_7 = 7
        DATA_BITS_8 = 8

    class StopBits:
        STOP_BITS_1 = 1
        STOP_BITS_1_5 = 1.5
        STOP_BITS_2 = 2

    def __init__(
        self,
        device: str,
        baudrate: int = 115200,
        bytesize: int | DataBits = DataBits.DATA_BITS_8,
        parity: ParityType = ParityType.PARITY_NONE,
        stopbits: StopBits = StopBits.STOP_BITS_1,
        rtscts: bool = False,
        xonxoff: bool = False,
        rts: int = None,
        dtr: int = None,
    ) -> None:
        self.device = device
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.rtscts = rtscts
        self.xonxoff = xonxoff
        self.rts = rts
        self.dtr = dtr
        self.serial: Serial = None
        self.serial_lock = Lock()

    def connect(self):
        serial = serial.serial_for_url(self.device, do_not_open=True)
        serial.baudrate = self.baudrate
        serial.bytesize = self.bytesize
        serial.parity = self.parity
        serial.stopbits = self.stopbits
        serial.rtscts = self.rtscts
        serial.xonxoff = self.xonxoff

        if self.rts is not None:
            serial.rts = self.rts

        if self.dtr is not None:
            serial.dtr = self.dtr

        try:
            serial.open()
            with self.serial_lock:
                self.serial = serial
        except serial.SerialException as e:
            logger.error(
                f"Could not open serial port {self.serial.name}: {e}\n"
            )
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
                    logger.error(f"{e}")

    def get_serial(self):
        return self.serial


class SerialServer(Thread):

    def __init__(self, serialfactory: SerialFactory, bind_port: int, bind_ip: str = '127.0.0.1', clients_limit: int = 1) -> None:
        self.serial = None
        self.serialfactory = serialfactory
        # self.serial_reader = None
        self.socket = None
        self.clients = set()  # set((client_socket, client_address))
        self.clients_lock = Lock()
        self.clients_limit = clients_limit
        self.serial_monitor_thread = None
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        # self.error_handle_serial = False
        super().__init__()

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.bind_ip, self.bind_port))
        self.socket.listen(1)
        self.serial_monitor_thread = Thread(target=self._handle_serial)
        self.serial_monitor_thread.start()
        while True:
            try:
                socket, addr = self.socket.accept()
                logger.info(f'Server Connected by: {addr}')
                Thread(target=self._handle_client,
                       args=(socket, addr)).start()
            except Exception as e:
                logger.error(f"Client Handler Thread: {e}")

    def _handle_serial(self):
        while True:
            try:
                if not self.serial:
                    # check serial status
                    continue
                # read all that is there or wait for one byte (blocking)
                data = self.serial.read(self.serial.in_waiting or 1)
                for socket, addr in self.clients:
                    try:
                        socket.sendall(data)
                    except Exception as e:
                        logger.error(f"Serial to Client {addr} Error: {e}")
            except serial.SerialException as e:
                logger.error(f"Serial to Client Error: {e}")

    def _handle_client(self, socket, addr):
        try:
            # Faster detection of bad clients that quit without closing the connection:
            # After 1 second of inactivity, start sending TCP keep-alive packets every 1 second.
            # If 3 consecutive keep-alive packets fail, assume the client is gone and close the connection.
            socket.setsockopt(
                socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
            socket.setsockopt(
                socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
            socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
            socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except AttributeError:
            pass  # not available on windows
        socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        with self.clients_lock:
            if len(self.clients) < self.clients_limit:
                self.clients.add((socket, addr))
            is_main_client = len(self.clients) == 1
        try:
            # enter network <-> serial loop
            while True:
                if not is_main_client:
                    # only main client can input to serial
                    continue
                try:
                    data = socket.recv(1024)
                    if not data:
                        break
                    try:
                        # get a bunch of bytes and send them
                        self.serial.write(data)
                    except:
                        pass
                except socket.error as e:
                    logger.error(f'Client {addr} Error: {e}\n')
                    # probably got disconnected
                    break
        except socket.error as e:
            logger.error(f'Client {addr} Error: {e}\n')
        finally:
            logger.info(f'Client {addr} Disconnected')
            with self.clients_lock:
                self.clients.remove((socket, addr))
            socket.close()
