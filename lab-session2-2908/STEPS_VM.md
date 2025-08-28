# Lab Session: Creating VMs on AWS & Azure

## Part 1. AWS Virtual Machines

### A. AWS UI Steps

1. Log in to [AWS Console](https://console.aws.amazon.com/).
2. Navigate to **EC2 → Launch Instance**.
3. Choose an **Amazon Machine Image (AMI)** → e.g., **Ubuntu Server 22.04 LTS**.
4. Select instance type: **t2.micro** (Free Tier).
5. Configure key pair → create or select an SSH key.
6. Configure security group → allow **SSH (port 22)**.
7. Launch the instance.
8. Copy the **Public IP** from the instance details.
9. Connect via terminal:

   ```bash
   ssh -i LabKey.pem ubuntu@<PUBLIC_IP>
   ```

---

### B. AWS CLI Steps

⚠️ **SECURITY WARNING**: Never use `--security-groups default` as it may have overly permissive rules that expose your instance to the entire internet!

```bash
# 1. Create a key pair (download PEM file)
aws ec2 create-key-pair --key-name LabKey --query "KeyMaterial" --output text > LabKey.pem
chmod 400 LabKey.pem

# 2. Create a secure security group first (IMPORTANT!)
aws ec2 create-security-group \
  --group-name lab-secure \
  --description "Secure group for lab - SSH only"

# Add only SSH access (port 22)
aws ec2 authorize-security-group-ingress \
  --group-name lab-secure \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# 3. Launch instance with the secure security group
aws ec2 run-instances \
  --image-id ami-07f07a6e1060cd2a8 \
  --count 1 \
  --instance-type t2.micro \
  --key-name LabKey \
  --security-groups lab-secure

# 4. Get instance details
aws ec2 describe-instances --query "Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress]" --output table

# 5. Connect via SSH
ssh -i LabKey.pem ubuntu@<PUBLIC_IP>
```

---

## Part 2. Azure Virtual Machines

### A. Azure UI Steps

1. Log in to [Azure Portal](https://portal.azure.com/).
2. Navigate: **Virtual Machines → Create → Azure Virtual Machine**.
3. Basics:

   * Resource Group → create `LabGroup`.
   * VM Name → `LabVM`.
   * Region → `East US` (or nearest).
   * Image → **Ubuntu 22.04 LTS**.
   * Size → `B1s` (low-cost).
   * Authentication → SSH key.
4. Networking → allow **SSH (port 22)**.
5. Review + Create.
6. Copy the **Public IP** and connect:

   ```bash
   ssh azureuser@<PUBLIC_IP>
   ```

---

### B. Azure CLI Steps

```bash
# 1. Create a resource group
az group create --name LabGroup --location eastus

# 2. Create a VM
az vm create \
  --resource-group LabGroup \
  --name LabVM \
  --image Ubuntu2204 \
  --admin-username azureuser \
  --generate-ssh-keys

# 3. Get public IP
az vm show -d -g LabGroup -n LabVM --query publicIps -o tsv

# 4. Connect via SSH
ssh azureuser@<PUBLIC_IP>
```

---

## Part 3. Cleanup (to avoid charges)

* **AWS:**

```bash
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>
```

* **Azure:**

```bash
az vm delete --resource-group LabGroup --name LabVM --yes
az group delete --name LabGroup --yes --no-wait
```

---

End of Lab: Students will have launched, connected, and terminated VMs on both AWS and Azure via UI and CLI.
