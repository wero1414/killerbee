"""KillerBee driver for the FeralRF CatSniffer (CC1352).

The implementation lives in the feralrf package
(feralrf.integrations.killerbee.KillerBeeFeralRF) so it is versioned with the
firmware/host stack. This module exposes it under KillerBee's dev_* driver
convention as FERALCAT, which killerbee/__init__.py instantiates as
FERALCAT(device).

Requires: pip install feralrf   (or feralrf[killerbee])
"""
from feralrf.integrations.killerbee import KillerBeeFeralRF as FERALCAT

__all__ = ["FERALCAT"]
