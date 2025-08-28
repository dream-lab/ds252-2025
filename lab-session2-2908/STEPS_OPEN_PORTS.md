# Opening Port 5001 for HTTPS Traffic

## AWS - Opening Port 5001

### A. AWS Console Steps

1. **Navigate to EC2 Dashboard**
   - Log in to [AWS Console](https://console.aws.amazon.com/)
   - Go to **EC2 → Instances**

2. **Find Your Security Group**
   - Select your running instance
   - Click on the **Security** tab
   - Click on the security group link (e.g., `sg-xxxxxxxxx`)

3. **Edit Inbound Rules**
   - Click **Edit inbound rules**
   - Click **Add rule**
   - Configure the rule:
     - **Type**: Custom TCP
     - **Port range**: 5001
     - **Source**: 0.0.0.0/0 (Anywhere IPv4)
     - **Description**: HTTPS traffic on port 5001
   - Click **Save rules**

### B. AWS CLI Steps

```bash
# 1. Get your instance's security group ID
aws ec2 describe-instances --instance-ids <INSTANCE_ID> --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text

# 2. Add inbound rule for port 5001
aws ec2 authorize-security-group-ingress \
  --group-id <SECURITY_GROUP_ID> \
  --protocol tcp \
  --port 5001 \
  --cidr 0.0.0.0/0

# 3. Verify the rule was added
aws ec2 describe-security-groups --group-ids <SECURITY_GROUP_ID> --query 'SecurityGroups[0].IpPermissions'
```

---

## Azure - Opening Port 5001

### A. Azure Console Steps

1. **Navigate to Virtual Machines**
   - Log in to [Azure Portal](https://portal.azure.com/)
   - Go to **Virtual machines**

2. **Access Network Security Group**
   - Select your VM (e.g., `LabVM`)
   - Click **Networking** in the left sidebar
   - Click on the Network Security Group name

3. **Add Inbound Security Rule**
   - Click **Inbound security rules**
   - Click **+ Add**
   - Configure the rule:
     - **Source**: Any
     - **Source port ranges**: *
     - **Destination**: Any
     - **Service**: Custom
     - **Destination port ranges**: 5001
     - **Protocol**: TCP
     - **Action**: Allow
     - **Priority**: 1010 (or any available priority)
     - **Name**: Allow-HTTPS-5001
     - **Description**: Allow HTTPS traffic on port 5001
   - Click **Add**

### B. Azure CLI Steps

```bash
# 1. Open port 5001 in the network security group
az network nsg rule create \
  --resource-group LabGroup \
  --nsg-name LabVMNSG \
  --name Allow-HTTPS-5001 \
  --protocol tcp \
  --priority 1010 \
  --destination-port-range 5001 \
  --access allow

# 2. Verify the rule was created
az network nsg rule list \
  --resource-group LabGroup \
  --nsg-name LabVMNSG \
  --query '[?name==`Allow-HTTPS-5001`]' \
  --output table
```

---

## Testing Port Access

After opening the port, you can test if it's accessible:

```bash
# Test from your local machine (replace with your VM's public IP)
telnet <PUBLIC_IP> 5001

# Or use curl to test HTTP/HTTPS connectivity
curl -I http://<PUBLIC_IP>:5001
curl -I https://<PUBLIC_IP>:5001
```

---

## Security Notes

⚠️ **Important**: Opening ports to `0.0.0.0/0` (anywhere) allows traffic from any IP address. For production environments, consider:

- Restricting source IPs to specific ranges
- Using Application Load Balancers/Application Gateways
- Implementing proper SSL/TLS certificates
- Adding authentication and authorization layers

---

## Cleanup

To remove the port access when no longer needed:

**AWS CLI:**
```bash
aws ec2 revoke-security-group-ingress \
  --group-name lab-secure \
  --protocol tcp \
  --port 5001 \
  --cidr 0.0.0.0/0
```

**Azure CLI:**
```bash
az network nsg rule delete \
  --resource-group LabGroup \
  --nsg-name LabVMNSG \
  --name Allow-HTTPS-5001
```
