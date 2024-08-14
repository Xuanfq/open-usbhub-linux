import os


def is_package(directory):
    """
    Checks if a given directory is a Python package
    """
    # Python 3.3+ can use importlib.util.find_spec to check
    init_path = os.path.join(directory, "__init__.py")
    return os.path.exists(init_path) or (  # exist __init__.py
        # exist __pycache__
        os.path.isdir(os.path.join(directory, "__pycache__"))
        and any(
            name.startswith("__init__") and name.endswith(".pyc")
            for name in os.listdir(os.path.join(directory, "__pycache__"))
        )  # __init__.pyc in __pycache__ dir
    )


def find_packages(directory, prefix=""):
    """
    Recursively find and list all Python packages
    """
    packages = []
    for item in os.listdir(directory):
        path = os.path.join(directory, item)
        if os.path.isdir(path):
            if is_package(path):
                packages.append(prefix + item)
            sub_packages = find_packages(path, prefix + item + ".")
            packages.extend(sub_packages)
    return packages
