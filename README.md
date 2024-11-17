# USBtingoGUI

USBtingoGUI is a graphical tool for sending and receiving CAN(-FD) messages using [USBtingo USB to CAN-FD interface](https://www.fischl.de/usbtingo/)
based on the [python-can-usbtingo](https://github.com/EmbedME/python-can-usbtingo) library.
- Cross-platform compatibility (Windows, MacOS, Linux)
- Send and receive CAN and CAN-FD messages
- Record logic levels on CAN RX (for analysis with sigrok/PulseView)
- Save logged messages to [CRTD](https://docs.openvehicles.com/en/latest/crtd/index.html) files
- Show CAN bus state and errors

![](https://raw.githubusercontent.com/EmbedME/USBtingoGUI/main/docs/usbtingogui_screenshot.png)

## Installation

```bash
pip install USBtingoGUI
```

## Usage

```bash
python -m USBtingoGUI
```

## Troubleshooting

### Linux: "LIBUSB_ERROR_ACCESS" as non-root

Add udev rule to give permissions to all users.
```
sudo bash -c $'echo \'SUBSYSTEM=="usb", ATTRS{product}=="USBtingo", MODE="0666"\' > /etc/udev/rules.d/50-USBtingo.rules'

sudo udevadm control --reload-rules
```
