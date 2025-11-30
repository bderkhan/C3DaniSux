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

**C3 install URL (custom software):** `https://github.com/bderkhan/C3DaniSux.git` with branch `custom-staging-c3`

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

### Driver Monitoring (DM) experiment

- Default behavior on this branch is **DM disabled** for C3 testing. A new toggle lives under `Settings ▸ Device ▸ Settings ▸ Disable Driver Monitoring (Dani)`.
- When off, we publish stub driver monitoring/model messages, suppress DM alerts/force-decel, and keep the driver cam/IR off by default. Turn the toggle off and reboot to keep DM off; turn it on and reboot to re-enable the camera/DM path.
- This is a temporary shim while the new driver monitor is being developed.
- A second option, `Gentle Driver Reminder (3 min)`, keeps DM very light: a single beep every 3 minutes of no attention, no disengage or steering shake. Looking back resets the 3-minute timer.

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

## 🧪 Testing & Debugging

### Connecting to Your Device

#### SSH Access (Recommended)

1. **Enable SSH on your device:**
   - Go to `Settings` ▶️ `Software`
   - Enable SSH
   - Enter your GitHub username (device will fetch your SSH keys)

2. **Connect via WiFi:**
   
   **Option A: Device in tethered/hotspot mode:**
   - When device acts as WiFi hotspot, use: `192.168.43.1`
   ```bash
   ssh comma@192.168.43.1
   ```
   
   **Option B: Device connected to your router:**
   - Find the device IP on your network (shown on device screen or check router admin)
   - Example if your router uses `192.168.86.XXX`:
   ```bash
   ssh comma@192.168.86.XXX
   ```
   - Or scan your network:
   ```bash
   # On macOS/Linux
   arp -a | grep -i comma
   # Or use nmap
   nmap -sn 192.168.86.0/24
   ```

3. **Connect via comma Prime (remote access):**
   - Requires [comma Prime subscription](https://comma.ai/connect)
   - Add to your `~/.ssh/config`:
     ```
     Host comma-*
       Port 22
       User comma
       IdentityFile ~/.ssh/my_github_key
       ProxyCommand ssh %h@ssh.comma.ai -W %h:%p

     Host ssh.comma.ai
       Hostname ssh.comma.ai
       Port 22
       IdentityFile ~/.ssh/my_github_key
     ```
   - Connect: `ssh comma-{dongle_id}`

#### ADB Access

1. **Enable ADB on your device:**
   - Plug device into constant power (port 2)
   - Enable ADB in `Settings` ▶️ `Software`
   - Plug USB cable into port 1

2. **Connect:**
   ```bash
   # Over USB
   adb shell
   
   # Over WiFi (tethered/hotspot mode)
   adb connect 192.168.43.1:5555
   
   # Over WiFi (router network - replace with device IP)
   adb connect 192.168.86.XXX:5555
   ```

#### Serial Console (Low-level debugging)

For comma three:
```bash
# From your local repo
tools/scripts/serial.sh
```
- Username: `comma`
- Password: `comma`

### Viewing Logs

#### On-Device Log Access

Once connected via SSH or ADB:

```bash
# View system logs
journalctl -u manager -f

# View specific process logs
journalctl -u controlsd -f
journalctl -u dmonitoringd -f
journalctl -u dmonitoringmodeld -f

# View all openpilot logs
journalctl -u manager -u controlsd -u dmonitoringd -f

# View recent boot logs
journalctl -b | tail -100
```

#### Accessing Recorded Routes

Routes are stored in `/data/media/0/realdata/`:

```bash
# List recent routes
ls -lth /data/media/0/realdata/ | head -20

# View route structure
ls -la /data/media/0/realdata/{route_name}/
```

Each route contains:
- `rlog.bz2` - All messages between processes (bzip2 compressed capnproto)
- `fcamera.hevc` - Road camera (H.265)
- `ecamera.hevc` - Wide road camera (H.265)
- `dcamera.hevc` - Driver camera (H.265)
- `qlog.bz2` - Decimated subset of rlog
- `qcamera.ts` - Lower res road camera (H.264)

#### Downloading Logs for Analysis

```bash
# From your local machine
scp comma@192.168.43.1:/data/media/0/realdata/{route_name}/* ./logs/

# Or use ADB
adb pull /data/media/0/realdata/{route_name} ./logs/
```

### Debugging Tools

#### Live CAN Message Streaming

1. **On device (SSH):**
   ```bash
   cd /data/openpilot/cereal/messaging/
   ./bridge &
   ```

2. **On your PC:**
   ```bash
   # Using Cabana (replace with device IP)
   # If tethered: cabana --zmq 192.168.43.1
   # If on router: cabana --zmq 192.168.86.XXX
   cabana --zmq <device_ip>
   ```

#### Live Camera Stream

1. **On device (SSH):**
   ```bash
   (
     cd /data/openpilot/cereal/messaging/
     ./bridge &

     cd /data/openpilot/system/camerad/
     ./camerad &

     cd /data/openpilot/system/loggerd/
     ./encoderd &

     wait
   ) ; trap 'kill $(jobs -p)' SIGINT
   ```

2. **On your PC:**
   ```bash
   # Decode stream (replace with device IP)
   cd tools/camerastream
   # If tethered: ./compressed_vipc.py 192.168.43.1
   # If on router: ./compressed_vipc.py 192.168.86.XXX
   ./compressed_vipc.py <device_ip>
   
   # View stream (separate terminal)
   cd selfdrive/ui
   ./watch3
   ```

#### Checking Process Status

```bash
# Check if processes are running
ps aux | grep -E "manager|controlsd|dmonitoring"

# Check process health
systemctl status manager
systemctl status controlsd
systemctl status dmonitoringd

# View process logs in real-time
tail -f /tmp/shm/logcat
```

### Testing Your Changes

#### Quick Test Workflow

1. **Make changes locally** and push to GitHub:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin custom-staging-c3
   ```

2. **On device, update to latest:**
   - Go to `Settings` ▶️ `Software`
   - Press `CHECK` at `Download`
   - Device will download and install latest commit

3. **Reboot device** to ensure clean state

4. **Test functionality:**
   - Drive and test your changes
   - Monitor logs via SSH if needed
   - Check for errors in `journalctl`

#### Testing DM Toggle

1. **Install/update** to latest version
2. **Reboot** device
3. **Navigate** to `Settings` ▶️ `Device` ▶️ `Settings`
4. **Toggle** "Disable Driver Monitoring (Dani)"
5. **Reboot** again (required for camera state changes)
6. **Verify:**
   - When disabled: No DM alerts, driver cam off
   - When enabled: DM alerts active, driver cam on
   - Check logs: `journalctl -u dmonitoringd -f`

### Common Issues & Troubleshooting

#### Device Won't Boot After Update

1. **Access serial console** (see above)
2. **Check boot logs:**
   ```bash
   journalctl -b | grep -i error
   ```
3. **Factory reset** if needed:
   - `Settings` ▶️ `Software` ▶️ `Uninstall`

#### Process Crashes

1. **Check crash logs:**
   ```bash
   journalctl -u manager --since "10 minutes ago" | grep -i error
   ```

2. **Check system resources:**
   ```bash
   df -h  # Check disk space
   free -h  # Check memory
   top  # Check CPU usage
   ```

#### DM Toggle Not Working

1. **Verify param is set:**
   ```bash
   # SSH into device
   cat /data/params/d/DisableDriverMonitoring
   ```

2. **Check dmonitoringd logs:**
   ```bash
   journalctl -u dmonitoringd -f
   ```

3. **Restart services:**
   ```bash
   systemctl restart manager
   ```

#### Can't Connect via SSH

1. **Verify SSH is enabled** in device settings
2. **Re-enter GitHub username** in settings (refreshes SSH keys)
3. **Find device IP:**
   - **Tethered mode**: Device shows IP on screen (usually `192.168.43.1`)
   - **Router network**: Check device screen or router admin panel for assigned IP (e.g., `192.168.86.XXX`)
   - **Scan network**: `arp -a | grep -i comma` or check router's connected devices list
4. **Verify network connectivity:**
   ```bash
   ping <device_ip>
   ```
5. **Try ADB instead** as alternative

### Additional Resources

- **openpilot Developer Docs**: https://docs.comma.ai/
- **openpilot Wiki**: https://github.com/commaai/openpilot/wiki
- **sunnypilot Discord**: https://discord.gg/sunnypilot (for community support)
- **Log Analysis Tools**: See `tools/lib/logreader.py` for reading logs programmatically

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
