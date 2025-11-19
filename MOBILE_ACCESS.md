# Mobile Access Guide

## How to Access Dashboard on Your Phone

### Step 1: Find Your Computer's IP Address
Your computer's IP address is: **10.14.20.186**

### Step 2: Connect Your Phone
1. Make sure your phone is connected to the **same WiFi network** as your computer
2. Open your phone's web browser (Chrome, Safari, etc.)

### Step 3: Access the Dashboard
Type this URL in your phone's browser:
```
http://10.14.20.186:5173
```

### Step 4: Navigate to Mobile View
Once loaded, click on "Mobile view" in the sidebar, or go directly to:
```
http://10.14.20.186:5173/mobile
```

## Troubleshooting

### Can't Access?
1. **Check Firewall**: Make sure Windows Firewall allows connections on port 5173
2. **Check Network**: Ensure phone and computer are on the same WiFi
3. **Try Different IP**: If 10.14.20.186 doesn't work, try the other IP: 172.27.48.1
4. **Check Docker**: Make sure frontend container is running: `docker-compose ps`

### Firewall Fix (Windows)
1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Click "Inbound Rules" → "New Rule"
4. Select "Port" → Next
5. Select "TCP" and enter port "5173"
6. Allow the connection
7. Apply to all profiles
8. Name it "WQAM Frontend"

## Alternative: Use Your Computer's Browser
If mobile access doesn't work, you can still use the mobile view on your computer:
1. Open http://localhost:5173
2. Click "Mobile view" in the sidebar
3. The view will automatically adapt to your screen size

