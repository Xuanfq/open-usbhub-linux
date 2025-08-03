import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pathlib import Path
import logging
from serialport.remote import AsyncCmdServer,AsyncSerialAdminRemoteCmd
from serialport.remote.admin import AsyncUsbhubPortAdminRemoteCmd


BASE_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)


def main():
    # AsyncCmdServer("127.0.0.1", 8888, AsyncSerialAdminRemoteCmd).main()
    AsyncCmdServer("127.0.0.1", 8888, AsyncUsbhubPortAdminRemoteCmd).main()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
