# pyparrot_windows

This is a fork of [pyparrot](https://github.com/amymcgovern/pyparrot) by Dr. Amy McGovern (MIT License) that adds **Bluetooth (BLE) support on Windows and macOS** for the Parrot Mambo and other minidrones. 

The original BLE code required Linux (`bluepy`). This fork replaces it with [bleak](https://github.com/hbldh/bleak), a modern, cross-platform BLE library.

## Key Changes vs. Upstream
* **Rewritten Connection Layer:** `pyparrot/networking/bleConnection.py` has been completely rewritten using `bleak` while maintaining the exact same public API and packet formats.
* **Stability Fixes:** Includes critical fixes for `bleak` ≥ 0.19 notification callbacks, a notification-thread deadlock bug, bounded write retries, and automatic re-subscription after a reconnection.
* **Drone Discovery Tool:** Includes `find_mambo.py` to easily scan and find your drone's specific BLE address.

---

## Installation Guide

Follow these steps to download and install the package reliably using an editable install:

### 1. Download the Package
Copy and paste this link into your web browser to download the source code zip archive:
```text
https://github.com/DAUST-CRAS/pyparrot_windows/archive/refs/heads/master.zip
```
Extract the downloaded `.zip` file on your computer.

### 2. Open Terminal and Enter the Folder
Open your terminal or command prompt, and navigate inside the unzipped folder:
```bash
cd pyparrot_windows-master/pyparrot_windows
```

### 3. Install via Python
Run the editable install. This links the package directly to your current Python environment and automatically installs any missing dependencies (like `bleak`):
```bash
python -m pip install -e .
```

## Getting Started

Get started by following the [turotial and Code Guide](tutorial.md).
