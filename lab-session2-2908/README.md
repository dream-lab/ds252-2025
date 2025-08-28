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
```

## Step 5: Understanding and Selecting AMIs (Amazon Machine Images)

### What is an AMI?
An **Amazon Machine Image (AMI)** is a pre-configured virtual machine template that contains:
- Operating system (Linux, Windows, etc.)
- Pre-installed software packages
- System configurations
- Storage mapping

Think of it as a "snapshot" or "template" that AWS uses to create your virtual machine instances.

### Why Choose the Right AMI?
- **Performance**: Different OS versions have different performance characteristics
- **Security**: Newer AMIs include latest security patches
- **Compatibility**: Your applications may require specific OS versions
- **Cost**: Some AMIs are free (like Ubuntu), others may have licensing costs

### How to Find and Select Ubuntu AMIs

**Option 1: Using AWS CLI (Recommended)**
```bash
# Find the latest Ubuntu 22.04 LTS AMIs
aws ec2 describe-images --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  "Name=state,Values=available" \
  --query 'Images | sort_by(@, &CreationDate) | reverse(@) | [0:5].[ImageId,Name,CreationDate]' \
  --output table
```

**Option 2: Using AWS Console**
1. Go to EC2 → Launch Instance
2. In "Application and OS Images" section, click **Browse more AMIs**
3. Search for "Ubuntu"
4. Filter by:
   - **Owner**: Canonical (099720109477)
   - **Architecture**: 64-bit (x86)
   - **Root device type**: EBS
5. Select the most recent Ubuntu 22.04 LTS version

### Recommended AMI IDs (as of August 2025)

| AMI ID | Description | Region | Creation Date |
|--------|-------------|---------|---------------|
| `ami-07f07a6e1060cd2a8` | Ubuntu 22.04 LTS (most recent) | us-east-1 | 2025-08-22 |
| `ami-05ffdc3c60b1be961` | Ubuntu 22.04 LTS | us-east-1 | 2025-08-19 |
| `ami-0add08d545f97eb70` | Ubuntu 22.04 LTS | us-east-1 | 2025-08-01 |

**⚠️ Important Notes:**
- AMI IDs are **region-specific** - the same Ubuntu version will have different AMI IDs in different AWS regions
- Always use the **most recent** AMI for latest security patches
- Ubuntu 22.04 LTS is recommended for stability and long-term support
- Owner ID `099720109477` is Canonical's official AWS account

### Alternative Operating Systems

If you prefer other operating systems:

**Amazon Linux 2:**
```bash
aws ec2 describe-images --owners amazon \
  --filters "Name=name,Values=amzn2-ami-hvm-*" "Name=state,Values=available" \
  --query 'Images | sort_by(@, &CreationDate) | reverse(@) | [0:3].[ImageId,Name]' \
  --output table
```

**CentOS/RHEL:**
```bash
aws ec2 describe-images --owners 125523088429 \
  --filters "Name=name,Values=CentOS*" "Name=state,Values=available" \
  --query 'Images | sort_by(@, &CreationDate) | reverse(@) | [0:3].[ImageId,Name]' \
  --output table
```

