## Step 0: Account creation

AWS Account
1. Go to [AWS Signup](https://aws.amazon.com/free).
2. Click **Create a Free Account**.
3. Provide email, password, and account name.
4. Enter billing information (credit/debit card required, charges apply if free tier exceeded).
5. Verify phone number with OTP.
6. Choose the **Free Tier** plan.
7. Log in to [AWS Console](https://console.aws.amazon.com/).

Azure Account
1. Go to [Azure Signup](https://azure.microsoft.com/en-us/free).
2. Click **Start Free**.
3. Sign in with a Microsoft account or create one.
4. Provide billing information (credit/debit card required, charges apply if free credits are exhausted).
5. Verify phone number with OTP.
6. You get **$200 free credits for 30 days**.
7. Log in to [Azure Portal](https://portal.azure.com/).


## Step 1: Update System & Install Basics

````markdown
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

