import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pathlib import Path
import logging
from usbhub import usbhubtool


BASE_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)


def main():
    usbhubtool.rescan()
    logger.info(usbhubtool.nested_mode)
    logger.info(usbhubtool.get_device_dict())
    logger.info(usbhubtool.get_device_list())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
