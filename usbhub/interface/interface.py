import logging
from abc import abstractmethod, ABCMeta
from usbhub.usb import USBDevice

logger = logging.getLogger(__name__)


version = "1.0.0"


class USBHUBProvider:
    __meta_class__ = ABCMeta

    def __init__(self) -> None:
        self.device_topo = None
        self.port_mapping = {}

    @abstractmethod
    def match(
        self,
        device: USBDevice,
        provider_device_topo: dict = None,
        provider_port_mapping: dict = None,
    ) -> tuple[bool, dict[int | str, list[int]]]:
        """
        Check if the device is this vendor's product

        Params: device, provider_device_topo, provider_port_mapping
            device (USBDevice): usb device to be matched
            provider_device_topo (dict): device topology of provider to be matched
                {
                    "port":1,  # must
                    "product_id":"0201",  # option
                    "vendor_id":"1a40",  # option
                    "class":"Hub",  # option
                    "driver":"7p",  # option
                    "speed":"480M",  # option
                    "info":"Terminus Technology",  # option
                    "children":[],  # option
                }
            provider_port_mapping (dict[int|str, list[int]]): Keys are the USB HUB's ports and value is port topology route from device to USB HUB's port.

        Returns: match_result, port_mapping
            match_result (bool): True if the device is this vendor's product else False
            port_mapping (dict[int|str, list[int]]): Keys are the USB HUB's ports and value is port topology route from device to USB HUB's port.

        Example:

        """
        # handle params
        if provider_port_mapping is None:
            device_topo = self.device_topo.copy()
        else:
            device_topo = provider_port_mapping.copy()
        if provider_port_mapping is None:
            port_mapping = self.port_mapping.copy()
        else:
            port_mapping = provider_port_mapping.copy()

        # verify params
        if device_topo is None or device is None:
            return False, port_mapping

        # match
        def match_dev_devtopo(dev: USBDevice, devtopo: dict) -> bool:
            devtopo_must_keys = []
            for k in devtopo_must_keys:
                if k not in devtopo:
                    return False
                count = str(dev[k]).lower().count(str(devtopo[k]).lower())
                if count == 0:
                    return False
            devtopo_keys = [
                "port",
                "product_id",
                "vendor_id",
                "clazz",
                "driver",
                "speed",
                "info",
            ]
            for k in devtopo_keys:
                if k in devtopo:
                    count = str(getattr(dev, k)).lower().count(
                        str(devtopo[k]).lower())
                    if count == 0:
                        return False
            return True

        queue = [(device, device_topo)]
        while len(queue) > 0:
            dev, devtopo = queue.pop()
            if not match_dev_devtopo(dev=dev, devtopo=devtopo):
                return False, port_mapping
            if "children" not in devtopo:
                continue
            for childdevtopo in devtopo["children"]:
                mtc = False
                mtc_dev = None
                for childdev in dev.children:
                    if match_dev_devtopo(dev=childdev, devtopo=childdevtopo):
                        mtc = True
                        mtc_dev = childdev
                        break
                if not mtc:
                    return False, port_mapping
                queue.append((mtc_dev, childdevtopo))
        return True, port_mapping
