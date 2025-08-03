import logging
from threading import Event, Thread
from abc import ABC, abstractmethod
import time
from usbhub import USBHUBDevice, USBHUBTool
from serialport.remote.server import AsyncCmdServer, SerialServer, SerialFactory
from serialport.remote.cmd import AsyncRemoteCmd
from serialport.remote import serial


class Admin(ABC):
    def get_usbhub_list(self) -> list[USBHUBDevice]:
        """get usbhub list"""
        return []

    def get_usbhub_port_list(self, usbhub: USBHUBDevice) -> list[int | str]:
        """get usbhub port list"""
        try:
            return usbhub.get_port_list()
        except Exception as e:
            logging.error(f"Get USBHUB Port List Failed: {e}")
            return []

    def get_usbhub_port_dev_list(
        self, usbhub: USBHUBDevice, port: int | str
    ) -> list[str]:
        """get usbhub single port's dev/serialport list"""
        try:
            return usbhub.get_port_devs(port=port, custom_dev_type="ttyUSB", deep=True)
        except Exception as e:
            logging.error(f"Get USBHUB Port Devs Failed: {e}")
            return []

    def get_usbhub_port_dev_status(
        self, usbhub: USBHUBDevice, port: int | str, dev: str
    ) -> str:
        """get usbhub single port's dev/serialport status"""
        try:
            devices = usbhub.get_port_devs(
                port=port, custom_dev_type="ttyUSB", deep=True
            )
            if dev not in devices:
                return "invalid"
            return "valid"
        except Exception as e:
            logging.error(f"Get USBHUB Port Devs Failed: {e}")
            return "error"

    def get_usbhub_port_dev_serial_settings(
        self, usbhub: USBHUBDevice, port: int | str, dev: str
    ) -> dict:
        """get usbhub single port's dev/serialport serial settings"""
        try:
            devices = usbhub.get_port_devs(
                port=port, custom_dev_type="ttyUSB", deep=True
            )
            if dev not in devices:
                pass
            return {}
        except Exception as e:
            logging.error(f"Get USBHUB Port Devs Failed: {e}")
            return {
                "baudrate": "unknown",
                "bytesize": "unknown",
                "parity": "unknown",
                "stopbits": "unknown",
                "flowcontrol": "unknown",
            }

    def set_usbhub_port_dev_serial_settings(
        self, usbhub: USBHUBDevice, port: int | str, dev: str, **kwargs
    ) -> dict:
        """get usbhub single port's dev/serialport serial settings"""
        try:
            devices = usbhub.get_port_devs(
                port=port, custom_dev_type="ttyUSB", deep=True
            )
            if dev not in devices:
                return False
            return True
        except Exception as e:
            logging.error(f"Get USBHUB Port Devs Failed: {e}")
            return {}

    def get_usbhub_port_dev_operate_settings(
        self, usbhub: USBHUBDevice, port: int | str, dev: str
    ) -> dict:
        """get usbhub single port's dev/serialport serial settings"""
        try:
            devices = usbhub.get_port_devs(
                port=port, custom_dev_type="ttyUSB", deep=True
            )
            if dev not in devices:
                pass
            return {}
        except Exception as e:
            logging.error(f"Get USBHUB Port Devs Failed: {e}")
            return {}

    def set_usbhub_port_dev_operate_settings(
        self, usbhub: USBHUBDevice, port: int | str, dev: str, **kwargs
    ) -> dict:
        """get usbhub single port's dev/serialport serial settings"""
        try:
            devices = usbhub.get_port_devs(
                port=port, custom_dev_type="ttyUSB", deep=True
            )
            if dev not in devices:
                return False
            return True
        except Exception as e:
            logging.error(f"Get USBHUB Port Devs Failed: {e}")
            return {}


class AsyncUsbhubPortAdminRemoteCmd(AsyncRemoteCmd):
    prompt = "UsbhubPortAdmin$ "
    intro = None

    def __init__(
        self,
        completekey="tab",
        stdin=None,
        stdout=None,
        admin: Admin = None,
        usbhub: USBHUBDevice = None,
        port: int | str = None,
    ):
        self.admin = admin
        self.usbhub = usbhub
        self.port = port
        super().__init__(completekey, stdin, stdout)

    def do_show(self, arg):
        """\nshow <devices|default-settings>\n"""
        if arg == "devices":
            self.stdout.writelines(f"No device!")
        elif arg == "default-settings":
            self.stdout.writelines(f"No default settings!")
        else:
            self.stdout.writelines(f"Unknown Command!")

    def complete_show(self, *args):
        subcmds = ["devices", "default-settings"]
        return self.completetips(*args, tips=subcmds)

    def do_set(self, arg):
        """
        set <type> <key> <value>

        Modify specified setting.

        Example:
          set default baudrate <115200|19200|9600|...>
          set default bytesize <5|6|7|8>
          set default parity <N|E|O|M|S>
          set default stopbits <1|1.5|2>
          set default flowcontrol <None|RTS/CTS|DTR/DSR|XON/XOFF>
        """
        if arg == "devices":
            self.stdout.writelines(f"No device!")
        elif arg == "default-settings":
            self.stdout.writelines(f"No default settings!")
        else:
            self.stdout.writelines(f"Unknown Command!")

    def complete_set(self, *args):
        subcmds = {
            "default": {
                "baudrate": [4800, 9600, 19200, 38400, 57600, 115200, 230400],
                "bytesize": [5, 6, 7, 8],
                "parity": ["N", "E", "O", "M", "S"],
                "stopbits": [1, 1.5, 2],
                "flowcontrol": ["None", "RTS/CTS", "DTR/DSR", "XON/XOFF"],
            }
        }
        return self.completetips(*args, tips=subcmds)


class AsyncUsbhubAdminRemoteCmd(AsyncRemoteCmd):
    prompt = "UsbhubAdmin$ "
    intro = None

    def __init__(
        self,
        completekey="tab",
        stdin=None,
        stdout=None,
        admin=None,
        usbhub: USBHUBDevice = None,
    ):
        self.admin = admin
        self.usbhub = usbhub
        super().__init__(completekey, stdin, stdout)


class AsyncSerialAdminRemoteCmd(AsyncRemoteCmd):
    prompt = "SerialAdmin$ "
    intro = """
====================================================
                Open USBHUB Linux
                  Serial Server
====================================================

Welcome to the usbhub serial server shell!
Type help or ? to list commands.
    """

    def __init__(self, completekey="tab", stdin=None, stdout=None, admin=None):
        self.admin = admin
        super().__init__(completekey, stdin, stdout)


class SerialAdmin:
    def __init__(self, conf_path: str = "/etc/oul/", *args, **kwargs):
        self.conf_path: str = conf_path
        self.args = args
        self.kwargs = kwargs
        self.usbhubs: list[USBHUBDevice] = []
        self.usbhubs_server: list[AsyncCmdServer] = []
        self.usbhubs_port_server: dict[USBHUBDevice, list[AsyncCmdServer]] = []
        self.usbhubtool: USBHUBTool = None
        self.running_thread = None
        self.running_event = Event()
        self.running_stopped = True
        self.reset()

    def load_conf(self):
        if not self.conf_path:
            return
        pass

    def save_conf(self):
        if not self.conf_path:
            return
        pass

    def reset(self):
        # stop the running
        self.running_event.set()
        while not self.running_stopped:
            time.sleep(1)
        # reset configurations
        self.load_conf()
        # reset objects
        self.usbhubtool = USBHUBTool(
            nested_mode_sub=self.kwargs.get("nested_mode_sub", True)
        )
        # reset thread
        self.running_thread = Thread(target=self.run)
        self.running_event.clear()
        # start thread
        self.running_thread.start()

    def detect_usbhub_changing(self, usbhub_change_callback: callable = None):
        usbhubs: list[USBHUBDevice] = []
        usbhubtool: USBHUBTool = USBHUBTool(
            nested_mode_sub=self.usbhubtool.nested_mode == USBHUBTool.NESTED_MODE_SUB
        )
        usbhubs = self.usbhubtool.get_device_list()
        for uh in usbhubs:
            exist = False
            for ouh in self.usbhubs:
                if uh.get_name() == ouh.get_name():
                    exist = True
            if not exist:
                # self.usbhubs = usbhubs  # update my user
                if usbhub_change_callback:
                    usbhub_change_callback()
                else:
                    self.usbhub_change_callback()

    def usbhub_change_callback(self):
        pass

    def run(self):
        logging.info(f"start...")
        while not self.running_event.is_set():
            self.running_stopped = False
            self.detect_usbhub_changing()
            pass
        self.running_stopped = True
        logging.info(f"end...")
