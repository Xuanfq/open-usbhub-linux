import sys
import os
import logging
from pathlib import Path
from importlib import import_module
from usbhub.package import is_package
sys.path.append(os.path.dirname(__file__))

logger = logging.getLogger(__name__)


PROJ_PATH = Path(__file__).resolve().parent
PROVIDER_NAME = "devices"
PROVIDER_PATH = PROJ_PATH / PROVIDER_NAME
DEVICES_PATH = PROVIDER_PATH


def get_modules_with_vp() -> dict[str, dict[str, any]]:
    """
    Get module of USB hub devices provider with vendor and product

    Return:
        modules_vp (dict[str, dict[str, any]]): {"vendor_name": {"product_name": module}}
    """
    root = PROVIDER_NAME
    root_path = PROVIDER_PATH
    modules_vp = {}  # [vendor][product]=module
    modules = []
    for vendor in os.listdir(root_path):
        vendor_path = os.path.join(root_path, vendor)
        if os.path.isdir(vendor_path):
            for product in os.listdir(vendor_path):
                vendor_product_path = os.path.join(vendor_path, product)
                if is_package(vendor_product_path):
                    package_name = root + "." + vendor + "." + product
                    package = import_module(package_name)
                    if not hasattr(package, "provider"):
                        logger.info(
                            f"Provider {vendor}@{product}'s interface is not finish implement. Skip."
                        )
                        continue
                    if vendor not in modules_vp:
                        modules_vp[vendor] = {}
                    modules_vp[vendor][product] = package
                    modules.append(package)
    return modules_vp


def get_modules() -> list:
    """
    Get module of USB hub devices provider

    Return:
        modules (list): [module]
    """
    root = PROVIDER_NAME
    root_path = PROVIDER_PATH
    modules_vp = {}  # [vendor][product]=module
    modules = []
    for vendor in os.listdir(root_path):
        vendor_path = os.path.join(root_path, vendor)
        if os.path.isdir(vendor_path):
            for product in os.listdir(vendor_path):
                vendor_product_path = os.path.join(vendor_path, product)
                if is_package(vendor_product_path):
                    package_name = root + "." + vendor + "." + product
                    package = import_module(package_name)
                    if not hasattr(package, "provider"):
                        logger.info(
                            f"Provider {vendor}@{product}'s interface is not finish implement. Skip."
                        )
                        continue
                    if vendor not in modules_vp:
                        modules_vp[vendor] = {}
                    modules_vp[vendor][product] = package
                    modules.append(package)
    return modules
