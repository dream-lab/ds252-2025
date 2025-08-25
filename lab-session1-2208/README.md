# Lab Session Prerequisites: Ubuntu VM Setup and Dependencies

All participants must complete the following setup **before the lab session on Friday**.

---

## 1. Ubuntu VM Setup

### macOS Users

* Follow the [Ubuntu VM on macOS guide](https://github.com/dream-lab/ds252-2025/blob/main/lab-session1-2208/macos_vm_setup.md) provided.
* Use **UTM** for creating and running the Ubuntu virtual machine.

###

### Windows Users

* Follow the [Ubuntu VM on Windows guide](https://github.com/dream-lab/ds252-2025/blob/main/lab-session1-2208/windows_vm_setup.md) provided.

### Ubuntu User

* Install the dependencies in step 2 on bare metal.

###

---

## 2. Dependency Installation (Inside Ubuntu VM)
``` bash
# Install Docker
sudo apt-get update
sudo apt-get install docker.io -y
sudo systemctl enable docker --now
sudo usermod -aG docker $USER
 
# Install KVM and Virt-Manager
sudo apt-get install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager -y
 
# Download Ubuntu 22.04 ISO for VM
wget https://releases.ubuntu.com/22.04/ubuntu-22.04.5-live-server-amd64.iso

```


## 3. Verification

* Ensure your VM boots correctly.
* Verify dependencies are installed with no errors.
* Be ready to run demo scripts from the repository during the lab.

---

