# Network Troubleshooting Guide for Forex Trading Bot

This guide helps you resolve network connectivity issues with your Telegram bot.

## Quick Diagnosis

Run the network troubleshooter to automatically diagnose issues:

```bash
python network_troubleshooter.py
```

## Common Issues and Solutions

### 1. DNS Resolution Issues (`getaddrinfo failed`)

**Symptoms:**
- `httpx.ConnectError: [Errno 11001] getaddrinfo failed`
- Cannot resolve `api.telegram.org`

**Solutions:**

#### Windows:
1. **Change DNS Settings:**
   - Open Network & Internet settings
   - Click "Change adapter options"
   - Right-click your network adapter → Properties
   - Select "Internet Protocol Version 4 (TCP/IPv4)" → Properties
   - Select "Use the following DNS server addresses"
   - Set Preferred DNS: `8.8.8.8`
   - Set Alternate DNS: `1.1.1.1`

2. **Flush DNS Cache:**
   ```cmd
   ipconfig /flushdns
   ```

#### Linux/macOS:
1. **Change DNS Settings:**
   ```bash
   # Linux
   sudo nano /etc/resolv.conf
   # Add: nameserver 8.8.8.8
   # Add: nameserver 1.1.1.1
   
   # macOS
   # System Preferences → Network → Advanced → DNS
   # Add: 8.8.8.8 and 1.1.1.1
   ```

### 2. Local API Server Issues

**Symptoms:**
- `local_server_down` errors
- Cannot connect to `http://127.0.0.1:8000`

**Solutions:**

1. **Start the Local Server:**
   ```bash
   python start_local_server.py
   ```

2. **Check if Port 8000 is Available:**
   ```bash
   # Windows
   netstat -an | findstr :8000
   
   # Linux/macOS
   lsof -i :8000
   ```

3. **Kill Process Using Port 8000:**
   ```bash
   # Find PID
   netstat -ano | findstr :8000
   
   # Kill process (replace PID with actual process ID)
   taskkill /PID <PID> /F
   ```

### 3. Firewall/Antivirus Issues

**Symptoms:**
- Connection timeouts
- Network errors despite good internet

**Solutions:**

#### Windows:
1. **Allow Python through Firewall:**
   - Open Windows Defender Firewall
   - Click "Allow an app or feature through Windows Defender Firewall"
   - Click "Change settings"
   - Find Python in the list or click "Allow another app"
   - Browse to your Python executable and add it

2. **Temporarily Disable Antivirus:**
   - Temporarily disable your antivirus to test
   - Add Python and your project folder to exclusions

#### Linux:
```bash
sudo ufw allow out 443/tcp  # HTTPS
sudo ufw allow out 80/tcp   # HTTP
```

### 4. Network Connectivity Issues

**Symptoms:**
- `httpx.ReadError`
- Connection timeouts
- Intermittent failures

**Solutions:**

1. **Test Internet Connection:**
   ```bash
   ping 8.8.8.8
   ping google.com
   ```

2. **Test Telegram API:**
   ```bash
   curl -I https://api.telegram.org
   ```

3. **Try Different Network:**
   - Use mobile hotspot to test
   - Check if corporate firewall is blocking

4. **Check Proxy Settings:**
   - If behind corporate proxy, configure Python to use it
   - Add proxy settings to your environment variables

### 5. Bot Token Issues

**Symptoms:**
- Authorization errors
- Bot not responding

**Solutions:**

1. **Verify Bot Token:**
   - Check if token is correct in your code
   - Ensure bot is not banned or restricted

2. **Test Bot Token:**
   ```bash
   curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
   ```

3. **Create New Bot:**
   - If token is compromised, create a new bot with @BotFather

## Step-by-Step Resolution Process

### Step 1: Run Diagnostics
```bash
python network_troubleshooter.py
```

### Step 2: Start Local Server
```bash
python start_local_server.py
```

### Step 3: Test Bot Connection
```bash
python app/telegram/bot.py
```

### Step 4: Check Logs
Look for specific error messages in the bot output and address them accordingly.

## Advanced Troubleshooting

### Check System Resources
```bash
# Windows
tasklist | findstr python
netstat -an | findstr :8000

# Linux/macOS
ps aux | grep python
lsof -i :8000
```

### Monitor Network Traffic
```bash
# Windows
netstat -an | findstr ESTABLISHED

# Linux
netstat -tuln
```

### Test API Endpoints Manually
```bash
# Test local server
curl http://127.0.0.1:8000/health

# Test Telegram API
curl https://api.telegram.org/bot<TOKEN>/getMe
```

## Environment Variables

Set these environment variables if needed:

```bash
# Windows
set PYTHONPATH=%PYTHONPATH%;C:\path\to\your\project
set HTTP_PROXY=http://proxy.company.com:8080
set HTTPS_PROXY=http://proxy.company.com:8080

# Linux/macOS
export PYTHONPATH=$PYTHONPATH:/path/to/your/project
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

## Common Error Messages and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `getaddrinfo failed` | DNS resolution issue | Change DNS to 8.8.8.8/1.1.1.1 |
| `Connection refused` | Local server not running | Start local server with `python start_local_server.py` |
| `Read timeout` | Network timeout | Increase timeout values or check network |
| `SSL certificate` | Certificate issues | Update Python or disable SSL verification (not recommended) |
| `Permission denied` | Firewall blocking | Allow Python through firewall |

## Getting Help

If you're still experiencing issues:

1. Run the network troubleshooter and share the output
2. Check the bot logs for specific error messages
3. Verify all prerequisites are met
4. Test with a simple network connection first

## Prerequisites

Before running the bot, ensure:

- ✅ Python 3.8+ installed
- ✅ All dependencies installed (`pip install -r requirements.txt`)
- ✅ Internet connection working
- ✅ Local API server running on port 8000
- ✅ Valid Telegram bot token
- ✅ Firewall allows Python connections
- ✅ DNS resolution working 