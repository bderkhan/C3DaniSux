# C3DaniSux 🚗

A custom fork of [sunnypilot](https://github.com/sunnypilot/sunnypilot) specifically for **comma 3 (C3)** testing and modifications.

## 📋 Repository Information

- **Base Branch**: `staging-tici` (sunnypilot's comma 3 branch)
- **Current Branch**: `custom-staging-c3`
- **Device Support**: comma 3 (C3/TICI) only
- **Purpose**: Testing and custom modifications
- **Repository**: https://github.com/bderkhan/C3DaniSux

## 🌞 About sunnypilot

[sunnypilot](https://github.com/sunnyhaibin/sunnypilot) is a fork of comma.ai's openpilot, an open source driver assistance system. sunnypilot offers a unique driving experience for over 300+ supported car makes and models with modified behaviors of driving assist engagements.

This repository is based on sunnypilot's `staging-tici` branch, which is specifically maintained for comma 3 devices.

## ⚠️ Important Notes

- **MUST USE `staging-tici` BRANCH ONLY** - This repository is based on `staging-tici` which is specifically for comma 3 devices. Do not use branches intended for comma 3X or other devices.
- This repository is **independent** and not connected to the upstream sunnypilot repository
- Based on `staging-tici` branch which is specifically for comma 3 devices
- This is a **testing/modification repository** - use at your own risk
- **THIS IS ALPHA QUALITY SOFTWARE FOR RESEARCH PURPOSES ONLY**

## 🚘 Device Requirements

- [comma three](https://comma.ai/shop/products/three) device
- One of [the 300+ supported cars](https://github.com/commaai/openpilot/blob/master/docs/CARS.md)
- A [car harness](https://comma.ai/shop/products/car-harness) to connect to your car

## 📦 Installation

To install this custom version on your comma 3 device:

### First Time Installation

1. On your comma three, go to `Settings` ▶️ `Software`
2. Select `Custom Software` when prompted
3. Enter the installation URL:
   ```
   https://github.com/bderkhan/C3DaniSux.git
   ```
4. Specify the branch: `custom-staging-c3`
5. Complete the rest of the installation following the onscreen instructions

### Updating Existing Installation

If you already have this software installed:

1. On your comma three, go to `Settings` ▶️ `Software`
2. At the `Download` option, press `CHECK` to fetch the latest updates
3. At the `Target Branch` option, press `SELECT` and choose `custom-staging-c3`
4. The device will download and install the latest version

### Installation URL Format

- **Repository URL**: `https://github.com/bderkhan/C3DaniSux.git`
- **Branch**: `custom-staging-c3`
- **Alternative format**: `bderkhan/C3DaniSux/custom-staging-c3` (if supported by your device)

> [!IMPORTANT]
> **You MUST use the `staging-tici` based branch (`custom-staging-c3`) only. Do not attempt to use branches intended for comma 3X or other devices, as they are not compatible with comma 3.**

> [!NOTE]
> This is a custom branch for testing purposes. Standard sunnypilot installation instructions may not apply.

## 🔧 Development

This repository is set up for independent development and testing. Make modifications as needed and push to your own branch.

> [!WARNING]
> **CRITICAL**: Always base your work on `staging-tici` branch only. This repository is specifically for comma 3 devices. Do not merge or use code from branches intended for comma 3X or other devices.

### Cloning and Setting Up

To clone this repository:

```bash
git clone https://github.com/bderkhan/C3DaniSux.git
cd C3DaniSux
git checkout custom-staging-c3
```

**Important**: The `custom-staging-c3` branch is based on `staging-tici`. When pulling updates or creating new branches, always ensure you're working from `staging-tici` base.

### Pushing Changes

To push your changes to this repository:

```bash
# Make your changes, then:
git add .
git commit -m "Your commit message"
git push origin custom-staging-c3
```

The remote is already configured to point to: `https://github.com/bderkhan/C3DaniSux.git`

### Branch Structure

- `custom-staging-c3` - Main development branch based on `staging-tici`

## 📄 License

This repository maintains the same licensing as sunnypilot:

- sunnypilot is released under the [MIT License](LICENSE)
- Includes code derived from [openpilot by comma.ai](https://github.com/commaai/openpilot), also MIT licensed

**DISCLAIMER**: THIS IS ALPHA QUALITY SOFTWARE FOR RESEARCH PURPOSES ONLY. THIS IS NOT A PRODUCT. YOU ARE RESPONSIBLE FOR COMPLYING WITH LOCAL LAWS AND REGULATIONS. NO WARRANTY EXPRESSED OR IMPLIED.

## 🔗 Links

- Original sunnypilot: https://github.com/sunnypilot/sunnypilot
- sunnypilot Documentation: https://docs.sunnypilot.ai/
- sunnypilot Discord: https://discord.gg/sunnypilot
- comma.ai openpilot: https://github.com/commaai/openpilot

---

**Repository Owner**: bderkhan  
**Repository Name**: C3DaniSux

