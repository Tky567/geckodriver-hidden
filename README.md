<div align="center">

# geckodriver_hidden v1.0.8

A Firefox Selenium WebDriver that copies Firefox and patches `libxul` so the usual automation marker is harder to read. This fork drops `psutil`, so it can be installed on Termux.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

Fork of [undetected-geckodriver](https://github.com/bytexenon/undetected_geckodriver) by ByteXenon. The upstream project is archived. This package keeps the same patch idea and renames the import to `geckodriver_hidden`.

PyPI badges can be added after the first release. The distribution name is `geckodriver-hidden`. The import name stays `geckodriver_hidden`.

## Overview

> [!NOTE]
> Linux only, including Termux when `platform.system()` reports `Linux` or `Android`. Windows and macOS paths from the original project were never finished.

Selenium drives Firefox through geckodriver. While that session is active, Firefox sets properties defined by the WebDriver specification. Pages can read `navigator.webdriver` and treat the session as automated. Services such as Cloudflare use that kind of check.

`geckodriver_hidden.Firefox()` sits between your code and Selenium. Creating an instance does two things:

1. Locate the Firefox installation, copy it, and replace the `webdriver` marker inside the copied `libxul` with a random string of the same length.
2. Start a Selenium session against that copied binary.

The installed Firefox is not modified. The copy lives under `$HOME/.cache/undetected_firefox/`.

You can compare a normal Selenium Firefox session with this package on a bot-detection page such as [BrowserScan](https://www.browserscan.net/bot-detection). Passing that page does not mean every site will allow the session.

The `libxul` marker was written for desktop Linux builds. A Termux Firefox build (Bionic, usually `aarch64`) may not contain the same bytes, so the copy can still be detected or fail to start. Removing `psutil` only fixes the install error on Termux. It does not make the patch match a Termux build.

## Installation

Python 3.6+ and Firefox are required. The only runtime dependency is `selenium>=4.10.0`.

After this project is published on PyPI:

```bash
pip install geckodriver-hidden
```

The import name uses an underscore, because a Python module cannot contain a hyphen:

```python
from geckodriver_hidden import Firefox
```

`pip` treats `geckodriver_hidden` and `geckodriver-hidden` as the same project name. Register and document the hyphenated name only.

Until the package is on PyPI, install from git or from a local archive. Replace `USER` with the GitHub account that owns the repository:

```bash
pip install "git+https://github.com/USER/geckodriver_hidden.git"
pip install .
```

A built sdist or wheel installs the same metadata from `pyproject.toml`:

```bash
pip install geckodriver_hidden-1.0.8.tar.gz
pip install geckodriver_hidden-1.0.8-py3-none-any.whl
```

Build and upload when the PyPI name `geckodriver-hidden` is free:

```bash
python -m pip install build twine
python -m build
python -m twine upload dist/*
```

Publishing also runs from the `Publish Python Package` workflow on a GitHub release, using the `PYPI_API_TOKEN` secret.

### Why psutil was removed

Upstream 1.0.7 depends on `psutil>=5.8.0`. On Termux with Python 3.13, `pip install psutil` fails while building the wheel: upstream reports `platform android is not supported`. `psutil` was not part of the patch. It was only the last-resort search for the Firefox directory: start Firefox, read the process executable, then stop it.

This package does that with the standard library:

1. `shutil.which()` finds `firefox` or `firefox-bin` on `PATH`.
2. `os.fork()` and `os.execv()` start `firefox --headless --new-instance` in a child.
3. `os.readlink("/proc/<pid>/exe")` reads the executable path. `os.kill()` stops the child.

`os.getlogin()` is not used. Termux often has no controlling terminal, so that call raises. The cache path uses `$HOME` and `$USER`. The search list also includes `/data/data/com.termux/files/usr/lib/firefox`. If `platform.system()` returns `Android`, it is treated as Linux.

## Usage

This package is an interface for Selenium. Replace `selenium.webdriver.Firefox` with `geckodriver_hidden.Firefox`. The rest of the Selenium API is unchanged.

1. **Open a page**

   ```python
   from geckodriver_hidden import Firefox

   driver = Firefox()
   driver.get("https://www.example.com")
   driver.quit()
   ```

2. **Search on Google**

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

`example/example.py` is the short form of the first pattern. For the rest of the API, see the [Selenium documentation](https://www.selenium.dev/documentation/).

## Requirements

- Firefox
- Python >= 3.6
- Selenium >= 4.10.0

`psutil` is not required as of 1.0.8.

## FAQ

### The browser is still detected. What should I do?

The patch only rewrites one marker in a copied `libxul`. Other signals are unchanged: IP address, TLS, canvas, WebGL, and behavior. A site can still block the session. The marker may also be missing on a Firefox build this package was not written for. Open an issue with the site URL, Firefox version, and operating system if a desktop Linux build is still flagged only because of `navigator.webdriver`.

### Why patch the Firefox binary?

When Firefox is controlled remotely, it sets properties described by the WebDriver specification. Selenium does not set `navigator.webdriver` itself. The package copies Firefox and edits the copied `libxul` so that marker is replaced with a random string of the same length.

### Why this name?

The import is `geckodriver_hidden` because the package hides the usual WebDriver marker in the copied Firefox libraries. It is not a separate geckodriver binary. The PyPI project name is `geckodriver-hidden`: hyphens are the distribution-name form, underscores are only for the import.

### Why use this instead of undetected-chromedriver?

[undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) targets Chrome and Edge. This package is the Firefox path, continued after upstream archived [undetected-geckodriver](https://github.com/bytexenon/undetected_geckodriver), with the `psutil` dependency removed.

## Roadmap

**Done in this fork:**

- [x] Spoof the `webdriver` marker in a copied `libxul.so`.
- [x] Drop `psutil` and find Firefox with `PATH` plus `/proc/<pid>/exe`.
- [x] Treat Android as Linux and search the Termux Firefox library path.

**Not done:**

- [ ] Windows and macOS. The path tables exist only as comments in `constants.py`.
- [ ] Helpers for CAPTCHA or Cloudflare challenges.
- [ ] Selenium Wire support.

## Contributing

Issues and pull requests are welcome, especially a confirmed `libxul` marker for a Firefox build this package misses, or a Windows or macOS path table that has been tested.

## License

MIT. See [LICENSE](LICENSE). Copyright (c) 2024 ByteXenon.

## Acknowledgments

- Selenium contributors.
- ByteXenon, author of the archived upstream project.
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver), which inspired the upstream project.
