"""
Code Adopted from Radeon ProRender
"""
import platform
import site
import subprocess
import sys

OS = platform.system()
IS_WIN = OS == 'Windows'
IS_MAC = OS == 'Darwin'
IS_LINUX = OS == 'Linux'

# adding user site-packages path to sys.path
if site.getusersitepackages() not in sys.path:
    sys.path.append(site.getusersitepackages())


def run_module_call(*args):
    """Run Blender Python with arguments on user access level"""
    module_args = ('-m', *args, '--user')

    subprocess.check_call([sys.executable, *module_args], timeout=60.0)


def run_pip(*args):
    """Run 'pip install' with current user access level"""
    return run_module_call('pip', 'install', *args)


def has_libs():
    try:
        import py7zr
        import xmltodict
        return py7zr is not None and xmltodict is not None
    except ImportError:
        return False


def ensure_libs():
    try:
        import py7zr
        import xmltodict
        return py7zr is not None and xmltodict is not None
    except ImportError:
        try:
            if IS_MAC or IS_LINUX:
                run_module_call("ensurepip", '--upgrade')
            run_pip("--upgrade", "pip")
            run_pip("wheel")
            run_pip("py7zr")
            run_pip("xmltodict")
            return True
        except subprocess.SubprocessError as e:
            print("Something went wrong, unable to install py7zr", e)
        return False
