
# Provider Implement Template

- __init__.py

```python
from interface.interface import USBHUBProvider, USBDevice


class SipolarUSBHUBProvider(USBHUBProvider):
    def __init__(self) -> None:
        super().__init__()
        self.device_port_topo = {
            1: [1, 2, 3, 4],
            2: [2, 3, 4],
            3: [2, 3, 4],
            4: [1, 2, 3, 4],
            6: [1, 2, 4],
            7: [1, 2, 3],
        }
        self.device_topo = {
            "clazz": "hub",
            "vendor_id": "1a40",
            "product_id": "0201",
            "driver": "7p",
            "children": [
                {
                    "port": 1,
                    "clazz": "hub",
                    "vendor_id": "1a40",
                    "product_id": "0101",
                    "driver": "4p",
                },
                {
                    "port": 2,
                    "clazz": "hub",
                    "vendor_id": "1a40",
                    "product_id": "0101",
                    "driver": "4p",
                },
                {
                    "port": 3,
                    "clazz": "hub",
                    "vendor_id": "1a40",
                    "product_id": "0101",
                    "driver": "4p",
                },
                {
                    "port": 4,
                    "clazz": "hub",
                    "vendor_id": "1a40",
                    "product_id": "0101",
                    "driver": "4p",
                },
                {
                    "port": 6,
                    "clazz": "hub",
                    "vendor_id": "1a40",
                    "product_id": "0101",
                    "driver": "4p",
                },
                {
                    "port": 7,
                    "clazz": "hub",
                    "vendor_id": "1a40",
                    "product_id": "0101",
                    "driver": "4p",
                },
            ],
        }
        self.port_mapping = {
            1: [7, 1],
            2: [7, 2],
            3: [7, 3],
            4: [3, 2],
            5: [3, 3],
            6: [3, 4],
            7: [4, 1],
            8: [4, 2],
            9: [4, 3],
            10: [4, 4],
            11: [6, 1],
            12: [6, 2],
            13: [6, 3],
            14: [2, 2],
            15: [2, 3],
            16: [2, 4],
            17: [1, 1],
            18: [1, 2],
            19: [1, 3],
            20: [1, 4],
        }

    def match(
        self,
        device: USBDevice,
        provider_device_topo: dict = None,
        provider_port_mapping: dict = None,
    ) -> tuple[bool, dict[int | str, list[int]]]:
        return super().match(device=device)


# interface: 
provider = SipolarUSBHUBProvider()
```