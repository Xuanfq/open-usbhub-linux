import subprocess
import re
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class USBDevice:
    def __init__(
        self,
        bus: int = -1,
        port: int = -1,
        dev: int = -1,
        interface: int = -1,
        clazz: str = None,
        driver: str = None,
        speed: int = 0,
        vendor_id: str = None,
        product_id: str = None,
        info: str = None,
        text: str = "",
        topo_level: int = -1,
        usb_device_path: str = "/sys/bus/usb/devices",
    ) -> None:
        self._id = ""
        self.bus = int(bus)
        self.port = int(port)
        self.dev = int(dev)
        self.interface = int(interface)
        self.clazz = clazz
        self.driver = driver
        self.speed = int(speed)
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.info = info
        self.text = text
        self.topo_level = topo_level
        self.usb_device_path = usb_device_path
        self.parent: USBDevice = None
        self.children: list[USBDevice] = []  # children from scanning
        # others
        self.preset_children: list[USBDevice] = (
            []
        )  # it has multi ports if it's a hub, preset them.

    def __str__(self) -> str:
        s = f'{self.get_id()}[bus={self.bus} port={self.port} dev={self.dev} if={self.interface} class="{self.clazz}" driver="{self.driver}" speed={self.speed}M vendor_id={self.vendor_id} product_id={self.product_id} info="{self.info}"]'
        return s

    def set_parent(self, parent):
        """
        set device's parent, only one parent device node, and bus does not have any parents.
        """
        self.parent = parent
        # update id (device path)
        device_path = f"{self.port}:1.{self.interface}"
        tp = self.parent
        while tp is not None:
            if tp.parent is not None:
                device_path = f"{tp.port}.{device_path}"
            else:
                device_path = f"{tp.bus}-{device_path}"
            tp = tp.parent
        self._id = device_path

    def add_child(self, child):
        """
        add device's child, device node has multi children
        """
        self.children.append(child)

    def get_id(self):
        """
        Get id of device, id is defined as the directory name under /sys/bus/usb/devices/
        """
        if self.parent is None:
            device_path = f"{self.bus}-0:1.0"
        else:
            device_path = f"{self.port}:1.{self.interface}"
            tp = self.parent
            while tp is not None:
                if tp.parent is not None:
                    device_path = f"{tp.port}.{device_path}"
                else:
                    device_path = f"{tp.bus}-{device_path}"
                tp = tp.parent
        self._id = device_path
        return self._id

    def get_dev(self):
        """
        Get dev under the current device tree node but do not include its subnodes
        """
        device = os.listdir(f"{self.usb_device_path}/{self.get_id()}")
        dev = os.listdir("/dev/")
        res = set(device).intersection(dev)
        return [f"/dev/{item}" for item in res]

    def get_dev_in_depth(self):
        """
        Get all dev under the current device tree node and its subnodes
        """
        list = self.get_dev()
        for child in self.children:
            list.extend(child.get_dev_in_depth())
        return list

    def get_tty_dev(self):
        """
        Get tty dev under the current device tree node but do not include its subnodes
        """
        device = os.listdir(f"{self.usb_device_path}/{self.get_id()}")
        dev = os.listdir("/dev/")
        res = set(device).intersection(dev)
        return [f"/dev/{item}" for item in res if item.count("tty") > 0]

    def get_tty_dev_in_depth(self):
        """
        Get all tty dev under the current device tree node and its subnodes
        """
        list = self.get_tty_dev()
        for child in self.children:
            list.extend(child.get_tty_dev_in_depth())
        return list

    def get_ttyusb_dev(self):
        """
        Get tty dev under the current device tree node but do not include its subnodes
        """
        device = os.listdir(f"{self.usb_device_path}/{self.get_id()}")
        dev = os.listdir("/dev/")
        res = set(device).intersection(dev)
        return [f"/dev/{item}" for item in res if item.count("ttyUSB") > 0]

    def get_ttyusb_dev_in_depth(self):
        """
        Get all tty dev under the current device tree node and its subnodes
        """
        list = self.get_ttyusb_dev()
        for child in self.children:
            list.extend(child.get_ttyusb_dev_in_depth())
        return list

    def get_custom_dev(self, custom_feature: str):
        """
        Get tty dev under the current device tree node but do not include its subnodes
        """
        device = os.listdir(f"{self.usb_device_path}/{self.get_id()}")
        dev = os.listdir("/dev/")
        res = set(device).intersection(dev)
        return [f"/dev/{item}" for item in res if item.count(custom_feature) > 0]

    def get_custom_dev_in_depth(self, custom_feature: str):
        """
        Get all tty dev under the current device tree node and its subnodes
        """
        list = self.get_custom_dev(custom_feature)
        for child in self.children:
            list.extend(child.get_custom_dev_in_depth(custom_feature))
        return list


class USBDeviceTreeUtils:
    def __init__(self) -> None:
        self.udts: list[USBDevice] = []  # usb device tree list [bus1, bus2, ...]
        self.devs: list[USBDevice] = []  # device list
        self.deep = 0
        self.build()

    def __str__(self):
        # get the str by dfs
        s = ["_ \n"]

        def callback(node: USBDevice, s: list):
            s.append(node.topo_level * "    " + "|__ " + str(node) + "\n")

        for node in self.udts:
            self.dfs(node, callback, kwargs={"s": s})
        return "".join(s)

    def build(self):
        ret = subprocess.run(
            ["lsusb", "-t", "-v"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if ret.returncode == 0:
            # success
            res = ret.stdout.decode().strip()
            # logger.debug(res)
        else:
            # error
            error = ret.stderr.decode()
            logger.error(error)
            return False
        dts = []
        devices = []
        current_level = 0
        current_node = None
        last_node = None
        for line in res.split("\n"):
            logger.debug(line)
            if line.count("/:") > 0:
                # root
                current_level = 0
                pattern = r"Bus (\d+)\.Port (\d+): Dev (\d+), Class=([^,]+), Driver=([^,]+), (\d+)M"
                match = re.search(pattern, line)
                if match:
                    bus = match.group(1)
                    port = match.group(2)
                    dev = match.group(3)
                    clazz = match.group(4)
                    driver = match.group(5)
                    speed = match.group(6)
                    current_node = USBDevice(
                        bus=bus,
                        port=port,
                        dev=dev,
                        clazz=clazz,
                        driver=driver,
                        speed=speed,
                        topo_level=current_level,
                        text=line,
                    )
                else:
                    logger.error(
                        f'Failed to recognize/catch output of "lsusb -t -v": {line}'
                    )
                    current_node = USBDevice(
                        topo_level=current_level,
                        text=line,
                    )
                dts.append(current_node)
                devices.append(current_node)
                last_node = current_node
            elif line.count("|__") > 0:
                pattern = r"Port (\d+): Dev (\d+), If (\d+), Class=([^,]+), Driver=([^,]+), (\d+)M"
                match = re.search(pattern, line)
                if match:
                    port = match.group(1)
                    dev = match.group(2)
                    interface = match.group(3)
                    clazz = match.group(4)
                    driver = match.group(5)
                    speed = match.group(6)
                    current_node = USBDevice(
                        bus=last_node.bus,
                        port=port,
                        dev=dev,
                        interface=interface,
                        clazz=clazz,
                        driver=driver,
                        speed=speed,
                        text=line,
                    )
                else:
                    logger.error(
                        f'Failed to recognize/catch output of "lsusb -t -v": {line}'
                    )
                    current_node = USBDevice(
                        bus=last_node.bus,
                        text=line,
                    )
                if line.count((current_level + 1) * "    " + "|__") > 0:
                    current_level += 1
                    current_node.set_parent(last_node)
                    last_node.add_child(current_node)
                else:
                    parent = last_node.parent
                    while line.count((current_level) * "    " + "|__") == 0:
                        current_level -= 1
                        parent = parent.parent
                    current_node.set_parent(parent)
                    if parent is not None:
                        parent.add_child(current_node)
                current_node.topo_level = current_level
                devices.append(current_node)
                last_node = current_node
            else:
                pattern = r"ID (\w+):(\w+) (.+)"
                match = re.search(pattern, line)
                if match:
                    vendor_id = match.group(1)
                    product_id = match.group(2)
                    device_info = match.group(3)
                    current_node.vendor_id = vendor_id
                    current_node.product_id = product_id
                    current_node.info = device_info
                else:
                    logger.error(
                        f'Failed to recognize/catch output of "lsusb -t -v": {line}'
                    )
                current_node.text += f"\n{line}"
            if current_level + 1 > self.deep:
                self.deep = current_level + 1
        self.udts = dts
        self.devs = devices

    def get_bus_num(self) -> int:
        return len(self.udts)

    def get_device_num(self) -> int:
        return len(self.devs)

    def get_tree_deep(self) -> int:
        return self.deep

    def get_device_list(self) -> list[USBDevice]:
        return self.devs

    def bfs(
        self,
        nodes: list[USBDevice] | USBDevice,
        callback: Callable[[USBDevice], None] = None,
        args=(),
        kwargs={},
    ):
        if type(nodes) == list:
            if len(nodes) == 0:
                return
        else:
            if nodes is None:
                return
            nodes = [nodes]
        next_nodes = []
        for node in nodes:
            if callback is not None:
                callback(node, *args, **kwargs)
            for child in node.children:
                next_nodes.append(child)
        self.bfs(nodes=next_nodes, callback=callback, args=args, kwargs=kwargs)

    def dfs(
        self,
        node: USBDevice,
        callback: Callable[[USBDevice], None] = None,
        args=(),
        kwargs={},
    ):
        if node is None:
            return
        if callback is not None:
            callback(node, *args, **kwargs)
        for child in node.children:
            self.dfs(node=child, callback=callback, args=args, kwargs=kwargs)

    def is_child(self, parent: USBDevice, child: USBDevice) -> bool:
        """
        Checks if a child node is indeed a child of its parent node.
        ** Notice: if parent == child: return True
        """
        if parent is None or child is None:
            return False
        if parent.get_id() == child.get_id():
            return True
        for c in parent.children:
            if self.is_child(c, child):
                return True
        return False
