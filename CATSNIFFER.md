# Using KillerBee with the Electronic Cats CatSniffer

This fork adds the **Electronic Cats CatSniffer** (TI CC1352) as a first-class
KillerBee device. There is **no new KillerBee firmware** — the CatSniffer runs
the **FeralRF** firmware, and this fork's host-side `feralcat` driver speaks to
it over USB, so every KillerBee `zb*` tool can sniff / inject / jam 802.15.4.

```
KillerBee (zbdump / zbid / zbassocflood / …)
      │  killerbee/dev_feralcat.py  (FERALCAT driver)
      ▼
feralrf.Radio  ──USB-CDC──▶  CatSniffer CC1352 (FeralRF firmware)  ──▶ 2.4 GHz 802.15.4
```

What the fork adds:
- `killerbee/dev_feralcat.py` — the `FERALCAT` driver (wraps `feralrf.integrations.killerbee.KillerBeeFeralRF`)
- `killerbee/kbutils.py` — `iscatsniffer()` probe + device-list branch (+ macOS `cu/tty.usbmodem` support)
- `killerbee/config.py` — `DEV_ENABLE_CATSNIFFER` flag
- `killerbee/__init__.py` — dispatch for `hardware="feralcat"` (and serial auto-detect)
- Py2→Py3 fixes so the tools actually run: `zbdump`, `zbassocflood`, `zbrealign`, `zbpanidconflictflood`

---

## 1. Prerequisites

1. **A CatSniffer flashed with FeralRF firmware** (the stock `ti_sniffer` firmware
   will NOT respond to this driver).
   - FeralRF: <https://github.com/ElectronicCats/FeralRF> (branch
     `feature/killerbee-integration` — it carries the `feralrf.integrations.killerbee` adapter).
   - Build the hex in the provided Docker image, or use a prebuilt `feralrf_cc1352.hex`.
   - Flash with Electronic Cats' **catnip**: `catnip flash feralrf_cc1352.hex`
     (`catnip devices` lists sticks; `catnip flash -d <n> <hex>` targets one of several).
2. **The `feralrf` Python package** (from FeralRF's `python/` directory).
3. **This KillerBee fork.**
4. System: `libusb`; Python deps `pyusb pyserial pycryptodome rangeparser scapy`.

---

## 2. Install

```bash
# venv
python3 -m venv ~/kbvenv && source ~/kbvenv/bin/activate

# FeralRF python package (has feralrf.Radio + the killerbee integration adapter)
git clone -b feature/killerbee-integration https://github.com/ElectronicCats/FeralRF
pip install -e FeralRF/python

# this KillerBee fork
git clone -b catsniffer-integration https://github.com/wero1414/killerbee
pip install -e killerbee

# verify — your CatSniffer should be listed as a feralcat device
zbid
```

---

## 3. Which port?

The CatSniffer exposes **3 USB-CDC interfaces**; the **Cat-Bridge** one is the radio link:

| Interface | Linux | macOS |
|-----------|-------|-------|
| **Cat-Bridge (radio)** ← use this | `/dev/ttyACM0` | `/dev/cu.usbmodemXXXX` |
| Cat-LoRa | `/dev/ttyACM1` | … |
| Cat-Shell (config/reset) | `/dev/ttyACM2` | … |

With two CatSniffers, the second is `/dev/ttyACM3` (bridge) etc. `catnip devices`
maps them cleanly.

---

## 4. Usage

Pass the **bridge port** with `-i` and force the driver with `-d feralcat`:

```bash
# sniff Zigbee channel 25 to a pcap
zbdump -i /dev/ttyACM0 -d feralcat -c 25 -w capture.pcap

# discover / identify the interface
zbid

# association-flood DoS
zbassocflood -p 0xA087 -c 25 -i /dev/ttyACM0 -d feralcat

# coordinator-realignment spoof (802.15.4 MAC cmd 0x08)
zbrealign -i /dev/ttyACM0 -d feralcat -c 25 -p 0xA087 -s 0x0000 ...

# PAN-ID conflict flood — needs TWO CatSniffers (inject + sniff)
zbpanidconflictflood -c 25 -i /dev/ttyACM0 -l /dev/ttyACM3 -d feralcat
```

Programmatic (bypassing the CLI):
```python
from killerbee import KillerBee
kb = KillerBee(device="/dev/ttyACM0", hardware="feralcat")
kb.set_channel(25)
kb.sniffer_on()
pkt = kb.pnext()          # {0: bytes, 1: validcrc, 2: rssi, 'bytes':…, 'validcrc':…, …}
kb.inject(frame_bytes)    # raw 802.15.4 MPDU (firmware appends the FCS)
kb.close()
```

Jamming is exposed through the FeralRF `Radio.start_jam()` API (used by the
KillerBee jammer path / callable directly via `feralrf`).

---

## 5. Notes & gotchas

- **FeralRF firmware is mandatory** — the driver auto-detects the CatSniffer by
  its USB VID/PID (`0x1209:0xbabb`) and Cat-Bridge descriptor, but only FeralRF
  answers the COBS/CRC16 protocol.
- **Cannot TX while RX is active.** The radio is TX *or* RX; request/response
  tools transmit with RX off, then flip to RX to collect replies.
- **The firmware drops bad-CRC frames** (it does not deliver malformed captures).
- **Wedge recovery:** sustained TX can wedge the CC1352 (`Transmit frame failed` /
  `Response timeout`). Reset it via the **Cat-Shell** port (`boot`/`exit`) or, for a
  deep wedge, physically replug. A stale process holding the port shows as
  "multiple access on port" → `fuser -k /dev/ttyACM0`.
- **Channels:** 2.4 GHz Zigbee only, 11–26.
- **macOS:** ports are `/dev/cu.usbmodem*`; the fork's `kbutils` enumerates them
  and tolerates a missing USB backend.

---

## 6. Attribution

CatSniffer = Electronic Cats (CC1352P7 + RP2040). Firmware = FeralRF (GPL-3.0).
KillerBee = River Loop Security. This integration is a host-side adapter — it adds
no firmware, it teaches KillerBee to drive FeralRF.
