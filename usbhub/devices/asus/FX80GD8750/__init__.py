from usbhub.interface.interface import USBHUBProvider, USBDevice


class FX80GD8750USBHUBProvider(USBHUBProvider):
    def __init__(self) -> None:
        super().__init__()
        self.device_port_topo = {
            1: [1],
            2: [2],
            3: [3],
        }
        self.device_topo = {
            "clazz": "root_hub",
            "vendor_id": "1d6b",
            "product_id": "0002",
            "driver": "xhci_hcd/16p",
            "children": [
                {
                    "port": 7,
                    "clazz": "Video",
                    "vendor_id": "0408",
                    "product_id": "3043",
                    "driver": "uvcvideo",
                },
                {
                    "port": 14,
                    "clazz": "Wireless",
                    "vendor_id": "13d3",
                    "product_id": "3530",
                    "driver": "btusb",
                },
            ],
        }
        self.port_mapping = {
            1: [1],
            2: [2],
            3: [3],
        }

    def match(
        self,
        device: USBDevice,
        provider_device_topo: dict = None,
        provider_port_mapping: dict = None,
    ) -> tuple[bool, dict[int | str, list[int]]]:
        return super().match(device=device)


provider = FX80GD8750USBHUBProvider()
