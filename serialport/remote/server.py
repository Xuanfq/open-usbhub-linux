import logging
import threading
import asyncio
import socket
import serial
from threading import Thread, Lock
from serialport.remote.cmd import AsyncStream, AsyncRemoteCmd
from serialport.remote.serial import SerialFactory


class AsyncCmdServer:
    def __init__(
        self,
        host: str,
        port: int,
        cmdcls: AsyncRemoteCmd,
        streamcls: AsyncStream = AsyncStream,
    ):
        self.host = host
        self.port = port
        self.cmdcls = cmdcls
        self.streamcls = streamcls
        self.server_thread = None
        self.stop_event = threading.Event()

    async def _handle_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        logging.info(f"Connection from {addr}")

        iostream = self.streamcls(reader, writer)
        shell = self.cmdcls(stdin=iostream, stdout=iostream)

        try:
            task = asyncio.create_task(shell.cmdloop())
            await task
            import time
            time.sleep(3)
        except asyncio.CancelledError:
            logging.info("Task was cancelled")
        except ConnectionError or Exception as e:
            logging.error(f"Error handling client: {e}")
        finally:
            logging.info(f"Closing connection from {addr}")
            try:
                writer.close()
                await writer.wait_closed()
            except Exception or ConnectionError or ConnectionResetError:
                pass
            logging.debug(f"Closed connection from {addr}")

    async def _run_fore(self):
        server = await asyncio.start_server(self._handle_client, self.host, self.port)

        addr = server.sockets[0].getsockname()

        logging.info(f"Serving on {addr}")
        logging.info(f"Type Ctrl + C to stop...")

        async with server:
            await server.serve_forever()

    async def _run_back(self):
        server = await asyncio.start_server(self._handle_client, self.host, self.port)

        addr = server.sockets[0].getsockname()

        logging.info(f"Serving on {addr}")

        async with server:
            while not self.stop_event.is_set():
                await asyncio.sleep(1)
            server.close()
            await server.wait_closed()

    def run_with_foreground(self):
        try:
            asyncio.run(self._run_fore())
        except KeyboardInterrupt:
            logging.warning("\nServer stopped.")

    def run_with_background(self):
        def run():
            asyncio.run(self._run_back())

        self.server_thread = threading.Thread(target=run)
        self.server_thread.start()

    def main(self):
        self.run_with_foreground()

    def stop(self):
        self.stop_event.set()


class SerialServer(Thread):

    def __init__(
        self,
        serialfactory: SerialFactory,
        bind_port: int,
        bind_ip: str = "127.0.0.1",
        clients_limit: int = 1,
    ) -> None:
        self.serial = None
        self.serialfactory = serialfactory
        self.serial_error = False
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
                logging.info(f"Server Connected by: {addr}")
                Thread(target=self._handle_client, args=(socket, addr)).start()
            except Exception as e:
                logging.error(f"Client Handler Thread: {e}")

    def _handle_serial(self):
        while True:
            try:
                if not self.serial:
                    # check serial status
                    if self.serialfactory.connect():
                        self.serial = self.serialfactory.get_serial()
                    else:
                        continue
                # read all that is there or wait for one byte (blocking)
                data = self.serial.read(self.serial.in_waiting or 1)
                for socket, addr in self.clients:
                    try:
                        socket.sendall(data)
                    except Exception as e:
                        logging.error(f"Serial to Client {addr} Error: {e}")
            except serial.SerialException as e:
                logging.error(f"Serial to Client Error: {e}")

    def _handle_client(self, socket, addr):
        try:
            # Faster detection of bad clients that quit without closing the connection:
            # After 1 second of inactivity, start sending TCP keep-alive packets every 1 second.
            # If 3 consecutive keep-alive packets fail, assume the client is gone and close the connection.
            socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
            socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
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
                        if self.serial:
                            self.serial.write(data)
                    except Exception as e:
                        raise Exception(f"Serial Write Error: {e}")
                except socket.error as e:
                    logging.error(f"Client {addr} Socket Error: {e}")
                    # probably got disconnected
                    break
                except Exception as e:
                    logging.error(f"Client {addr} Error: {e}")
                    self.serial_error = True
        except socket.error as e:
            logging.error(f"Client {addr} Error: {e}")
        finally:
            logging.info(f"Client {addr} Disconnected")
            with self.clients_lock:
                self.clients.remove((socket, addr))
            socket.close()
