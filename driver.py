# Imports #
import os
import shutil
import time

from selenium.webdriver.common.driver_finder import DriverFinder
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.remote_connection import FirefoxRemoteConnection
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

from .constants import TO_REPLACE_STRING
from .mixins import WebDriverMixin
from .utils import (
    generate_random_string,
    get_platform_dependent_params,
    get_webdriver_instance,
)


# Main class #
class Firefox(RemoteWebDriver, WebDriverMixin):
    """
    A custom Firefox WebDriver that attempts to avoid detection by web services.
    """

    def __init__(
        self, options: Options = None, service: Service = None, keep_alive: bool = True
    ) -> None:
        self.webdriver: WebDriver = get_webdriver_instance()
        self._platform_dependent_params: dict = get_platform_dependent_params()
        self._firefox_path: str = self._get_firefox_installation_path()
        self._undetected_path: str = self._get_undetected_firefox_path()

        self._setup_firefox_environment()

        self.service: Service = service or Service()
        self.options: Options = options or Options()
        self.options.binary_location = self._find_platform_dependent_executable()
        self.keep_alive: bool = keep_alive

        self._initialize_service()

    def _setup_firefox_environment(self) -> None:
        """Set up the undetected Firefox environment."""
        self._create_undetected_firefox_directory()
        self._patch_libxul_file()

    def _initialize_service(self) -> None:
        """Initialize the Firefox service and remote connection."""
        finder = DriverFinder(self.service, self.options)
        self.service.path = finder.get_driver_path()
        self.service.start()

        executor = FirefoxRemoteConnection(
            remote_server_addr=self.service.service_url,
            keep_alive=self.keep_alive,
            ignore_proxy=self.options._ignore_local_proxy,
        )
        try:
            super().__init__(command_executor=executor, options=self.options)
        except Exception:
            self.quit()
            raise

        self._is_remote = False

    def _firefox_dir_from_proc(self, exe: str) -> str:
        """Launch Firefox briefly and read its executable path from /proc."""
        pid = os.fork()
        if pid == 0:
            devnull = os.open(os.devnull, os.O_RDWR)
            os.dup2(devnull, 0)
            os.dup2(devnull, 1)
            os.dup2(devnull, 2)
            os.execv(exe, [exe, "--headless", "--new-instance"])

        time.sleep(0.2)
        try:
            return os.path.dirname(os.readlink(f"/proc/{pid}/exe"))
        finally:
            os.kill(pid, 9)
            os.waitpid(pid, 0)

    def _get_firefox_installation_path(self) -> str:
        """
        Unlike _get_binary_location, this method returns the path to the
        directory containing the Firefox binary and its libraries.
        Normally, it's located in `/usr/lib/firefox`.
        """

        firefox_paths: list = self._platform_dependent_params["firefox_paths"]
        for path in firefox_paths:
            if os.path.exists(path):
                return path

        # Last resort: run Firefox and read /proc/<pid>/exe.
        # Replaces psutil so Termux does not need a package that rejects Android.
        for firefox_exec in self._platform_dependent_params["firefox_execs"]:
            exe = shutil.which(firefox_exec)
            if exe:
                return self._firefox_dir_from_proc(exe)

        raise FileNotFoundError("Could not find Firefox installation path")

    def _get_undetected_firefox_path(self) -> str:
        """Get the path for the undetected Firefox."""
        home = os.environ.get("HOME") or os.path.expanduser("~")
        user = os.environ.get("USER") or os.environ.get("LOGNAME") or "user"
        return self._platform_dependent_params["undetected_path"].format(
            USER=user,
            HOME=home,
        )

    def _create_undetected_firefox_directory(self) -> str:
        """Create a directory for the undetected Firefox if it doesn't exist."""
        if not os.path.exists(self._undetected_path):
            shutil.copytree(self._firefox_path, self._undetected_path)
        return self._undetected_path

    def _patch_libxul_file(self) -> None:
        """Patch the libxul file in the undetected Firefox directory."""
        xul: str = self._platform_dependent_params["xul"]
        libxul_path: str = os.path.join(self._undetected_path, xul)
        if not os.path.exists(libxul_path):
            raise FileNotFoundError(f"Could not find {xul}")

        with open(libxul_path, "rb") as file:
            libxul_data = file.read()

        random_string: str = generate_random_string(len(TO_REPLACE_STRING))
        random_bytes: bytes = random_string.encode()
        libxul_data: bytes = libxul_data.replace(TO_REPLACE_STRING, random_bytes)
        with open(libxul_path, "wb") as file:
            file.write(libxul_data)

    def _find_platform_dependent_executable(self) -> str:
        """Find the platform-dependent executable for patched Firefox."""
        for executable in self._platform_dependent_params["firefox_execs"]:
            full_path: str = os.path.join(self._undetected_path, executable)
            if os.path.exists(full_path):
                return full_path
        raise FileNotFoundError("Could not find Firefox executable")
