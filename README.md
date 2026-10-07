<div align="center">

# geckodriver_hidden

A Selenium Firefox driver that patches a copy of Firefox's `libxul` so the `navigator.webdriver` marker is harder to detect. This fork removes the `psutil` dependency, so it installs on Termux.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

Fork of [undetected-geckodriver](https://github.com/bytexenon/undetected_geckodriver) by ByteXenon. The upstream project is archived. This fork keeps the same patching approach and renames the import to `geckodriver_hidden`.

| | Name |
|---|---|
| PyPI distribution | `geckodriver-hidden` |
| Python import | `geckodriver_hidden` |

## Overview

> [!NOTE]
> Linux only. Termux is supported when `platform.system()` reports `Linux` or `Android`. The Windows and macOS code paths inherited from the original project were never finished.

While Selenium drives Firefox through geckodriver, Firefox exposes the properties defined by the WebDriver specification. One of them is `navigator.webdriver`, which pages (and services such as Cloudflare) can read to tell that a session is automated.

`geckodriver_hidden.Firefox()` wraps Selenium's Firefox driver. Creating an instance does two things:

1. Finds the Firefox installation, copies it, and replaces the `webdriver` string inside the copied `libxul` with a random string of the same length.
2. Starts a Selenium session using the copied binary.

Your installed Firefox is not modified. The copy is stored in `$HOME/.cache/undetected_firefox/`.

You can compare a normal Selenium session with this package on a bot-detection page such as [BrowserScan](https://www.browserscan.net/bot-detection). Passing that page does not guarantee that every site will accept the session.

> [!WARNING]
> The `libxul` patch was written for desktop Linux builds. Termux builds of Firefox (Bionic libc, usually `aarch64`) may not contain the same bytes, so the browser can still be detected or fail to start. Removing `psutil` only fixes the install error on Termux. It does not make the patch match a Termux build.

## Requirements

- Linux (including Termux)
- Firefox
- Python 3.7+
- `selenium>=4.10.0` (the only runtime dependency)

## Installation

```bash
pip install geckodriver-hidden
```

```bash
git clone https://github.com/Tky567/geckodriver_hidden.git
cd geckodriver_hidden
pip install .
```

Or install directly from git without cloning:

```bash
pip install "git+https://github.com/Tky567/geckodriver_hidden.git"
```

Python module names cannot contain hyphens, so the import uses an underscore:

```python
from geckodriver_hidden import Firefox
```

## Usage

Replace `selenium.webdriver.Firefox` with `geckodriver_hidden.Firefox`. The rest of the Selenium API is unchanged.

**Open a page**

```python
from geckodriver_hidden import Firefox

driver = Firefox()
driver.get("https://www.example.com")
driver.quit()
```

**Search on Google**

```python
import time
from geckodriver_hidden import Firefox
from selenium.webdriver.common.by import By

driver = Firefox()
driver.get("https://www.google.com")

search_box = driver.find_element(By.NAME, "q")
search_box.send_keys("geckodriver_hidden")
search_box.submit()

time.sleep(2)
print("Current URL:", driver.current_url)
driver.quit()
```

`example/example.py` contains the first example. For the rest of the API, see the [Selenium documentation](https://www.selenium.dev/documentation/).

## Why `psutil` was removed

Upstream 1.0.7 depends on `psutil>=5.8.0`. On Termux with Python 3.13, `pip install psutil` fails while building the wheel with `platform android is not supported`.

`psutil` was not part of the patch itself. It was only used as a last resort to locate the Firefox directory (start Firefox, read the process executable, stop it). This package does the same with the standard library:

1. `shutil.which()` looks for `firefox` or `firefox-bin` on `PATH`.
2. `os.fork()` and `os.execv()` start `firefox --headless --new-instance` in a child process.
3. `os.readlink("/proc/<pid>/exe")` reads the executable path, then `os.kill()` stops the child.

Other Termux-related changes:

- `os.getlogin()` is not used, because it raises an error when there is no controlling terminal (common on Termux). The cache path is built from `$HOME` and `$USER` instead.
- The search list includes `/data/data/com.termux/files/usr/lib/firefox`.
- `Android` is treated as `Linux`.

## FAQ

### The browser is still detected. What should I do?

The patch only rewrites one marker in a copied `libxul`. Other signals are unchanged: IP address, TLS fingerprint, canvas, WebGL, and behavior. A site can still block the session for any of these reasons. The marker may also be missing from a Firefox build this package was not written for.

If a desktop Linux build is flagged only because of `navigator.webdriver`, open an issue with the site URL, Firefox version, and operating system.

### Why patch the Firefox binary?

When Firefox is remotely controlled, it sets `navigator.webdriver` as required by the WebDriver specification. Selenium does not set it, so it cannot be turned off from the Selenium side. This package copies Firefox and replaces the marker in the copied `libxul` with a random string of the same length.

### Why this name?

The package hides the WebDriver marker in the copied Firefox libraries. It is not a separate geckodriver binary. Hyphens are the PyPI distribution-name form (`geckodriver-hidden`), and underscores are used only for the import (`geckodriver_hidden`).

### How is this different from undetected-chromedriver?

[undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) targets Chrome. This package targets Firefox. It continues [undetected-geckodriver](https://github.com/bytexenon/undetected_geckodriver) after upstream was archived, with the `psutil` dependency removed.

## Roadmap

**Done in this fork**

- [x] Spoof the `webdriver` marker in a copied `libxul.so`.
- [x] Drop `psutil`; find Firefox using `PATH` and `/proc/<pid>/exe`.
- [x] Treat Android as Linux and search the Termux Firefox library path.

**Not done**

- [ ] Windows and macOS support. The path tables exist only as comments in `constants.py`.
- [ ] Helpers for CAPTCHA or Cloudflare challenges.
- [ ] Selenium Wire support.

## Contributing

Issues and pull requests are welcome. Most useful are:

- a confirmed `libxul` marker for a Firefox build this package misses;
- a tested Windows or macOS path table.

## License

MIT. See [LICENSE](LICENSE). Copyright (c) 2024 ByteXenon.

## Acknowledgments

- Selenium contributors.
- ByteXenon, author of the archived upstream project.
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver), which inspired the upstream project.
