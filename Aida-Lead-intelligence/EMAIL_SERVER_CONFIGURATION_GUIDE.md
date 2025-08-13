# Email Server Configuration Guide

## 🎯 **Overview**

This guide helps you configure email servers for sending tracked emails through the Aida Lead Intelligence Platform. The system supports various email providers and SMTP configurations.

## 📧 **Supported Email Providers**

### **1. Gmail**
```
SMTP Server: smtp.gmail.com
Port: 587
Security: TLS (not SSL)
Username: your-email@gmail.com
Password: App Password (not regular password)
```

**Setup Instructions:**
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use the generated 16-character app password

**Configuration:**
- ✅ Use TLS: Yes
- ❌ Use SSL: No
- Port: 587

### **2. Outlook/Hotmail**
```
SMTP Server: smtp-mail.outlook.com
Port: 587
Security: TLS
Username: your-email@outlook.com
Password: Your regular password
```

**Configuration:**
- ✅ Use TLS: Yes
- ❌ Use SSL: No
- Port: 587

### **3. Yahoo Mail**
```
SMTP Server: smtp.mail.yahoo.com
Port: 587
Security: TLS
Username: your-email@yahoo.com
Password: App Password (recommended)
```

**Configuration:**
- ✅ Use TLS: Yes
- ❌ Use SSL: No
- Port: 587

### **4. Hostinger**
```
SMTP Server: smtp.hostinger.com
Port: 587
Security: TLS
Username: your-email@yourdomain.com
Password: Your email password
```

**Configuration:**
- ✅ Use TLS: Yes
- ❌ Use SSL: No
- Port: 587

### **5. Custom SMTP Server**
```
SMTP Server: your-smtp-server.com
Port: 587 (or 465 for SSL)
Security: TLS or SSL (check with your provider)
Username: your-email@domain.com
Password: Your email password
```

## 🔧 **Configuration Settings Explained**

### **SSL vs TLS**

#### **SSL (Secure Sockets Layer)**
- **When to use**: When your provider requires SSL connection
- **Port**: Usually 465
- **Configuration**: 
  - ✅ Use SSL: Yes
  - ❌ Use TLS: No
  - Port: 465

#### **TLS (Transport Layer Security)**
- **When to use**: Most modern email providers (recommended)
- **Port**: Usually 587
- **Configuration**:
  - ❌ Use SSL: No
  - ✅ Use TLS: Yes
  - Port: 587

### **Common Port Numbers**
- **587**: Standard port for TLS (most common)
- **465**: Standard port for SSL
- **25**: Unencrypted SMTP (not recommended)

## 🛠️ **Troubleshooting Common Issues**

### **1. "Wrong Version Number" Error**
**Problem**: SSL connection fails with wrong version number
**Solution**: 
- Use TLS instead of SSL
- Change port from 465 to 587
- Uncheck "Use SSL" and check "Use TLS"

### **2. "Authentication Failed" Error**
**Problem**: Login fails even with correct credentials
**Solutions**:
- **Gmail**: Use App Password instead of regular password
- **Yahoo**: Generate App Password
- **Other providers**: Check if 2FA is enabled and use app password
- **Custom SMTP**: Verify username/password with provider

### **3. "Connection Refused" Error**
**Problem**: Cannot connect to SMTP server
**Solutions**:
- Verify SMTP server address
- Check if port is correct
- Try alternative ports (587 vs 465)
- Check firewall settings

### **4. "STARTTLS" Error**
**Problem**: TLS handshake fails
**Solutions**:
- Try without TLS (uncheck "Use TLS")
- Verify server supports TLS
- Check if port 587 is correct

## 📋 **Step-by-Step Configuration**

### **For Gmail Users:**

1. **Enable 2FA**:
   - Go to Google Account Settings
   - Security → 2-Step Verification → Turn on

2. **Generate App Password**:
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and generate password

3. **Configure in Platform**:
   ```
   Name: Gmail
   SMTP Server: smtp.gmail.com
   Port: 587
   Sender Email: your-email@gmail.com
   Password: [16-character app password]
   Sender Name: Your Name
   Use SSL: ❌ No
   Use TLS: ✅ Yes
   ```

### **For Outlook/Hotmail Users:**

1. **Configure in Platform**:
   ```
   Name: Outlook
   SMTP Server: smtp-mail.outlook.com
   Port: 587
   Sender Email: your-email@outlook.com
   Password: [your regular password]
   Sender Name: Your Name
   Use SSL: ❌ No
   Use TLS: ✅ Yes
   ```

### **For Hostinger Users:**

1. **Configure in Platform**:
   ```
   Name: Hostinger
   SMTP Server: smtp.hostinger.com
   Port: 587
   Sender Email: your-email@yourdomain.com
   Password: [your email password]
   Sender Name: Your Name
   Use SSL: ❌ No
   Use TLS: ✅ Yes
   ```

## 🧪 **Testing Your Configuration**

### **1. Test Connection**
- Click "Test Connection" button
- Should show "✓ Connection successful"
- Should show "✓ Login successful"

### **2. Send Test Email**
- Enter recipient email address
- Click "Send Test Email"
- Check recipient's inbox
- Verify tracking pixel loads (check email tracking dashboard)

### **3. Check Tracking**
- Go to Email Tracking dashboard
- Look for test email in tracking list
- Verify events are recorded when email is opened

## 🔒 **Security Best Practices**

### **1. Password Security**
- Use App Passwords for Gmail/Yahoo
- Never use regular passwords for 2FA-enabled accounts
- Store passwords securely

### **2. Connection Security**
- Always use TLS or SSL
- Avoid unencrypted connections (port 25)
- Verify server certificates

### **3. Account Security**
- Enable 2-Factor Authentication
- Use strong, unique passwords
- Monitor account activity

## 📊 **Provider-Specific Notes**

### **Gmail**
- Requires App Password for 2FA accounts
- Daily sending limits apply
- Good for testing and small campaigns

### **Outlook/Hotmail**
- Generally reliable
- Good for business emails
- Moderate sending limits

### **Yahoo**
- Requires App Password
- Good for personal use
- Moderate sending limits

### **Hostinger**
- Good for business domains
- Custom domain emails
- Professional appearance

### **Custom SMTP**
- Check with your provider for settings
- May have specific requirements
- Test thoroughly before using

## 🚀 **Advanced Configuration**

### **Custom SMTP with SSL**
```
Name: Custom SSL
SMTP Server: your-server.com
Port: 465
Use SSL: ✅ Yes
Use TLS: ❌ No
```

### **Custom SMTP with TLS**
```
Name: Custom TLS
SMTP Server: your-server.com
Port: 587
Use SSL: ❌ No
Use TLS: ✅ Yes
```

### **Legacy SMTP (Not Recommended)**
```
Name: Legacy
SMTP Server: your-server.com
Port: 25
Use SSL: ❌ No
Use TLS: ❌ No
```

## 📞 **Getting Help**

If you encounter issues:

1. **Check Provider Documentation**: Each email provider has specific setup instructions
2. **Verify Credentials**: Ensure username/password are correct
3. **Test Connection**: Use the test connection feature
4. **Check Firewall**: Ensure port 587/465 is not blocked
5. **Contact Support**: If issues persist, contact your email provider

## ✅ **Success Checklist**

Before sending campaigns, verify:

- [ ] Connection test passes
- [ ] Test email sends successfully
- [ ] Test email is received
- [ ] Tracking pixel loads (check tracking dashboard)
- [ ] Events are recorded when email is opened
- [ ] Configuration is marked as active

This configuration guide ensures your email server is properly set up for sending tracked emails through the Aida Lead Intelligence Platform. 