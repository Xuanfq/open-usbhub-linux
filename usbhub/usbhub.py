import logging
from usbhub import provider
from usbhub.interface.interface import USBHUBProvider
from usbhub.usb import USBDevice, USBDeviceTreeUtils

logger = logging.getLogger(__name__)


class USBHUBDevice:
    def __init__(
        self,
        vendor: str,
        product: str,
        device: USBDevice,
        port_mapping: dict[int | str, list[int]],
    ) -> None:
        self.vendor: str = vendor
        self.product: str = product
        self.device: USBDevice = device
        self.port_mapping: dict[int | str, list[int]] = port_mapping

    def __str__(self) -> str:
        return f"{self.vendor}@{self.product}|{self.device}"

    def get_name(self):
        return f"{self.vendor}@{self.product}|{self.device.get_id()}"

    def get_desc(self):
        return f"USB HUB: {self.vendor}@{self.product}\nVendor: {self.vendor}\nProduct: {self.product}\nPort Number: {self.get_port_num()}\nPort List: {self.get_port_list()}"

    def get_port_num(self):
        return len(self.port_mapping.keys())

    def get_port_list(self):
        return list(self.port_mapping.keys())

    def get_port_list_avaliable(self):
        return [
            port
            for port in self.get_port_list()
            if len(self.get_port_devices(port=port)) > 0
        ]

    def get_port_devs(
        self,
        port: str | int,
        custom_dev_type: str = "ttyUSB",
        deep: bool = False,
    ) -> list[str]:
        """Get port's dev list from path /dev/*

        Args:
            port (str|int): the port in port list from get_port_list()
            custom_dev_type (str): dev type, default is "ttyUSB", opt: "ttyUSB" | "tty" | "gpio" | "" ...
        """
        if port not in self.port_mapping:
            return None
        dev = self.device
        dev_i = 0
        res = []
        while dev_i < len(self.port_mapping[port]):
            for child in dev.children:
                if child.port == self.port_mapping[port][dev_i]:
                    if dev_i == len(self.port_mapping[port]) - 1:
                        if deep:
                            res.extend(
                                child.get_custom_dev_in_depth(
                                    custom_feature=custom_dev_type
                                )
                            )
                        else:
                            res.extend(
                                child.get_custom_dev(
                                    custom_feature=custom_dev_type)
                            )
                    dev = child
            dev_i += 1
        return res

    def get_port_devices(
        self,
        port: str | int,
    ) -> list[str]:
        """Get port's usb devices, include all the interface

        Args:
            port (str|int): the port in port list from get_port_list()
        """
        if port not in self.port_mapping:
            return None
        dev = self.device
        dev_i = 0
        res = []
        while dev_i < len(self.port_mapping[port]):
            for child in dev.children:
                if child.port == self.port_mapping[port][dev_i]:
                    if dev_i == len(self.port_mapping[port]) - 1:
                        res.append(child)
                    dev = child
            dev_i += 1
        return res


class USBHUBDeviceUtils:
    NESTED_MODE_COO = "coordination"
    NESTED_MODE_SUB = "subordination"
    udtutils = USBDeviceTreeUtils()

    def __init__(self, nested_mode_sub: bool = False) -> None:
        self.uhds: list[tuple[str, USBHUBDevice]] = (
            []
        )  # usbhub device list [(usb_device_id, usb_hub_device]
        self.uhdd: dict[str, list[USBHUBDevice]] = (
            {}
        )  # usbhub device dict {usb_device_id -> [usb_hub_device]}
        self.uhd_modules = {}  # vpmodules[vendor][product] = module
        # nested_mode: [co | sub] means [Coordination | Subordination]
        #   co : When multiple USB hubs are nested, they are used as a single USB hub.
        #   sub: When multiple USB hubs are nested, they are used as child devices and managed at the parent port.
        self.nested_mode = (
            self.NESTED_MODE_SUB if nested_mode_sub else self.NESTED_MODE_COO
        )  # [co | sub] means [Coordination | Subordination]
        # init module of provider
        # init parent and scan usb device
        super().__init__()
        # match usb hub devices
        self.rescan()

    def _match(self) -> None:
        # find the target device base on target features
        logger.info("Matching USB HUB...")
        uhds: list[tuple[str, USBHUBDevice]] = []
        uhdd: dict[str, list[USBHUBDevice]] = {}

        def callback(node, self, uhds, uhdd):
            for vendor in self.uhd_modules:
                for product in self.uhd_modules[vendor]:
                    product_module = self.uhd_modules[vendor][product]
                    success, _port_mapping = product_module.provider.match(
                        node)
                    port_mapping = _port_mapping.copy()
                    if not success:
                        continue
                    uhd = USBHUBDevice(
                        vendor=vendor,
                        product=product,
                        device=node,
                        port_mapping=port_mapping,
                    )
                    is_child = False
                    child_port = None
                    parent_uhd = None
                    for id, pre in uhds:
                        if self.udtutils.is_child(pre.device, uhd.device):
                            is_child = False
                            for port in pre.get_port_list():
                                for device in pre.get_port_devices(port=port):
                                    if self.udtutils.is_child(device, uhd.device):
                                        is_child = True
                                        parent_uhd = pre
                                        child_port = port
                            if not is_child:
                                # usb hub's usb device is same with "pre"
                                # ignore
                                pass
                            pass
                    if is_child:
                        if self.nested_mode == self.NESTED_MODE_COO:
                            # remove nested port
                            del parent_uhd.port_mapping[child_port]
                            uhds.append((uhd.device.get_id(), uhd))
                            if uhd.device.get_id() not in uhdd:
                                uhdd[uhd.device.get_id()] = [uhd]
                            else:
                                uhdd[uhd.device.get_id()].append(uhd)
                        elif self.nested_mode == self.NESTED_MODE_SUB:
                            pass
                        else:
                            pass
                    else:
                        uhds.append((uhd.device.get_id(), uhd))
                        if uhd.device.get_id() not in uhdd:
                            uhdd[uhd.device.get_id()] = [uhd]
                        else:
                            uhdd[uhd.device.get_id()].append(uhd)
                    logger.info(f"Found USB HUB: {uhd}, {uhd.get_desc()}")

        for bus_usb_device in self.udtutils.udts:
            self.udtutils.dfs(
                bus_usb_device, callback=callback, args=(self, uhds, uhdd)
            )
        self.uhds = uhds
        self.uhdd = uhdd

    def set_nested_mode(self, nested_mode_sub: bool = False):
        # nested_mode: [co | sub] means [Coordination | Subordination]
        #   co : When multiple USB hubs are nested, they are used as a single USB hub.
        #   sub: When multiple USB hubs are nested, they are used as child devices and managed at the parent port.
        self.nested_mode = (
            self.NESTED_MODE_SUB if nested_mode_sub else self.NESTED_MODE_COO
        )  # [co | sub] means [Coordination | Subordination]

    def rescan(self):
        self.uhd_modules = provider.get_modules_with_vp()
        self.udtutils.build()
        self._match()

    def get_device_dict(self):
        return self.uhdd

    def get_device_list(self):
        return self.uhds


class USBHUBTool(USBHUBDeviceUtils):
    def __init__(self, nested_mode_sub: bool = False) -> None:
        super().__init__(nested_mode_sub)
