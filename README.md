# ScanSnap Web

An application to control Fujitsu's SnapScan devices from browsers.

## Background
ScanSnap iX500 by Fujitsu is a compact and handy home scanner. Fujitsu provides drivers for Windows and Linux, but GUI is only available on Windows. This app will provide a Web-based UI to control a ScanSnap scanner connected via USB to a Linux PC running as a server. For the moment, the app is mainly intended to be used on a small local network and is geared toward family or a share house.

## Requirements:
- A Linux PC to use as a server backend (tested with Ubuntu 18.04 LTS)
  - Official ScanSnap driver from Fujitsu's website
  - ImageMagick (for generating PDF files from jpage images)
- A device that runs a modern browser, e.g. a smartphone, tablet, or PC