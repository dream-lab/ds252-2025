# 🐍 Python Environment Setup & Simple Flask Server

## 1. Create & Activate Python Virtual Environment
```bash
# First, update package repositories (IMPORTANT!)
sudo apt update

# Install Python development tools
sudo apt install -y python3-dev python3-pip

sudo apt install python3.10-venv
python3 -m venv flask-env

# Activate the environment
source flask-env/bin/activate

# Upgrade pip and install flask
pip install --upgrade pip
pip install flask
```

## 2. Run the Flask Server
```bash
# Make sure you're in the right directory and virtual environment is active
python flask_server.py
```

The server will start on `http://0.0.0.0:5001` and you should see:
```
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5001
* Running on http://[your-private-ip]:5001
```

## 3. Test the Flask Server from Your Local Machine

**Important:** Replace `<YOUR_SERVER_PUBLIC_IP>` with your actual VM's public IP address.

### Basic Connectivity Test
```bash
# Test if the server is reachable (from your local terminal)
curl -v http://<YOUR_SERVER_PUBLIC_IP>:5001/hello
```

### Test the /hello Endpoint with POST Request
```bash
# Test with a simple name
curl -X POST http://<YOUR_SERVER_PUBLIC_IP>:5001/hello \
  -H "Content-Type: application/json" \
  -d '{"name": "Student"}'
```

Expected response:
```json
{"message": "Hello, Student!"}
```

### Test with Different Names
```bash
# Test with your actual name
curl -X POST http://<YOUR_SERVER_PUBLIC_IP>:5001/hello \
  -H "Content-Type: application/json" \
  -d '{"name": "John"}'

# Test without providing a name (should default to "World")
curl -X POST http://<YOUR_SERVER_PUBLIC_IP>:5001/hello \
  -H "Content-Type: application/json" \
  -d '{}'
```

