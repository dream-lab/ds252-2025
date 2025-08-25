
````markdown
# System Setup for Lab (Ubuntu)

Machines must be ready with AWS CLI, Azure CLI, and required dependencies.

## Step 1: Update System & Install Basics
```
sudo apt update && sudo apt upgrade -y
sudo apt install -y unzip curl wget jq git
````

## Step 2: Install AWS CLI

```
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

## Step 3: Install Azure CLI

```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az version
```

## Step 4: Configure AWS & Azure Credentials

* **AWS CLI Configuration**

```bash
aws configure
# Provide AWS Access Key, Secret Key, Default Region, and Output Format
```

* **Azure CLI Login**

```bash
az login
# Opens browser for login with Azure account credentials

