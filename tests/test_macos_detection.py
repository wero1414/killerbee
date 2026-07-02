# killerbee/tests/test_macos_detection.py
import glob as _glob
from killerbee import kbutils


def test_get_serial_ports_queries_macos_usbmodem(monkeypatch):
    seen = []
    def fake_glob(pat):
        seen.append(pat)
        return []
    monkeypatch.setattr(kbutils.glob, "glob", fake_glob)
    kbutils.get_serial_ports()
    assert "/dev/cu.usbmodem*" in seen
    assert "/dev/tty.usbmodem*" in seen


def test_devlist_survives_no_usb_backend(monkeypatch):
    import usb.core
    def boom(*a, **k):
        raise usb.core.NoBackendError("no libusb")
    monkeypatch.setattr(usb.core, "find", boom)
    # only a CatSniffer on a macOS-style port, no USB dongles
    monkeypatch.setattr(kbutils, "get_serial_ports",
                        lambda include=None: ["/dev/cu.usbmodem1101"])
    monkeypatch.setattr(kbutils, "iscatsniffer",
                        lambda dev: dev == "/dev/cu.usbmodem1101")
    dl = kbutils.devlist()  # must NOT raise
    assert any(e[0] == "/dev/cu.usbmodem1101" and "CatSniffer" in e[1] for e in dl)
