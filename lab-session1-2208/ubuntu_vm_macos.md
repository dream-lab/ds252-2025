# Guide: Launching Ubuntu VM on macOS using UTM

## Prerequisites

- A Mac running macOS (Intel or Apple Silicon)
- Stable internet connection
- At least 20GB free disk space

---

## Step 1: Download UTM

- Visit [https://mac.getutm.app](https://mac.getutm.app)
- Download and install the latest UTM release for macOS
- Move the UTM app to **Applications**

---

## Step 2: Download Ubuntu ISO

- Go to [Ubuntu Downloads](https://ubuntu.com/download/desktop)
- Choose the version based on your Mac:
  - **Apple Silicon (M1/M2/M3):** Select ARM64 (Ubuntu for ARM)
  - **Intel Macs:** Select AMD64 (Ubuntu for x86\_64)
- Save the ISO file to your Mac

---

## Step 3: Create a New VM in UTM

1. Open the **UTM app**
2. Click **Create a New Virtual Machine**
3. Choose **Virtualize** (recommended if architecture matches)
   - If not, select **Emulate** (slower)
4. Select **Linux** as the operating system
5. Attach the **Ubuntu ISO** file you downloaded

---

## Step 4: Configure the VM

- **CPU & Memory:** Assign at least 2 CPU cores and 4GB RAM (more if available)
- **Storage:** Create a virtual disk (20GB+ recommended)
- **Shared Features:** Enable clipboard sharing if desired

---

## Step 5: Boot and Install Ubuntu

1. Start the VM from UTM
2. Ubuntu installer will load
3. Select **Install Ubuntu**
4. Follow on-screen installation steps:
   - Choose language, keyboard layout, Wi-Fi, etc.
   - Partition the virtual disk automatically (default)
   - Create a user account and password

---

## Step 6: Post-Installation

- After installation, restart the VM when prompted
- Remove the ISO from the virtual CD drive in UTM settings
- Login with your created credentials

---

## Step 7: (Optional) Enhance Experience

- In UTM, enable **Display scaling** for better resolution
- Adjust CPU/RAM in VM settings if performance is slow
- Install Ubuntu updates:
  ```bash
  sudo apt update && sudo apt upgrade -y
  ```

---

