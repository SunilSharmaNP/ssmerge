# 🚀 MERGE-BOT VPS Deployment Guide (Improved Version)

## 📋 Prerequisites

### System Requirements
- **OS:** Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM:** Minimum 1GB (2GB recommended)
- **Storage:** Minimum 20GB free space
- **CPU:** 1 core minimum (2 cores recommended)
- **Network:** Stable internet connection

### Required Software
- Docker & Docker Compose
- Git
- Basic Linux knowledge

## 🔧 Step-by-Step Installation

### Step 1: Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install curl wget git unzip -y
```

### Step 2: Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add user to docker group
sudo usermod -aG docker $USER

# Reboot to apply changes
sudo reboot
```

### Step 3: Clone Repository
```bash
git clone https://github.com/yashoswalyo/MERGE-BOT.git
cd MERGE-BOT

# Replace original files with improved versions
# Copy all improved files provided in the analysis
```

### Step 4: Configuration Setup

#### 4.1 Create Environment File
```bash
cp .env.template .env
nano .env
```

#### 4.2 Fill Required Variables
```bash
# Essential variables (MUST fill these)
API_HASH=your_api_hash_from_telegram
BOT_TOKEN=your_bot_token_from_botfather  
TELEGRAM_API=your_api_id_from_telegram
OWNER=your_telegram_user_id
OWNER_USERNAME=your_telegram_username
DATABASE_URL=mongodb://mergebot:mergebot123@mongodb:27017/mergebot?authSource=admin
```

#### 4.3 Get Telegram Credentials
1. Go to https://my.telegram.org
2. Login with your phone number
3. Go to "API Development Tools"
4. Create new application
5. Copy `api_id` and `api_hash`

#### 4.4 Create Bot Token
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions
4. Copy the bot token

### Step 5: Deploy with Docker Compose

#### 5.1 Start Services
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f merge-bot
```

#### 5.2 Verify Deployment
```bash
# Check running containers
docker ps

# Check bot health
curl http://localhost:8080/health

# Monitor logs
docker-compose logs -f
```

## 🔍 Troubleshooting Common Issues

### Issue 1: Configuration Errors
**Symptoms:** Bot fails to start, config errors in logs

**Solution:**
```bash
# Check environment variables
docker-compose exec merge-bot env | grep -E "(API_HASH|BOT_TOKEN|TELEGRAM_API)"

# Validate config
docker-compose exec merge-bot python3 -c "from config import Config; Config.initialize()"
```

### Issue 2: MongoDB Connection Failed
**Symptoms:** Database connection errors

**Solution:**
```bash
# Check MongoDB status
docker-compose logs mongodb

# Test MongoDB connection
docker-compose exec mongodb mongosh -u mergebot -p mergebot123 --authenticationDatabase admin
```

### Issue 3: Permission Denied
**Symptoms:** File permission errors

**Solution:**
```bash
# Fix permissions
sudo chown -R $USER:$USER ./downloads ./logs
chmod -R 755 ./downloads ./logs

# Restart services
docker-compose restart
```

## 🛡️ Security Best Practices

### 1. Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d
```

## 🔧 Maintenance Commands

### View Logs
```bash
# Real-time logs
docker-compose logs -f merge-bot

# Last 100 lines
docker-compose logs --tail=100 merge-bot
```

### Restart Services
```bash
# Restart specific service
docker-compose restart merge-bot

# Restart all services
docker-compose restart
```

### Update Bot
```bash
# Pull latest changes
git pull origin master

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d
```

### Clean Up
```bash
# Remove old files
find ./downloads -type f -mtime +7 -delete

# Clean Docker
docker system prune -f
```

## ✅ Post-Installation Checklist

- [ ] Bot starts successfully
- [ ] Can send `/start` command
- [ ] Video merging works
- [ ] MongoDB connection stable  
- [ ] Logs are clean
- [ ] Resource usage acceptable
- [ ] Backups configured

---

**Happy Deploying! 🎉**

For issues or improvements, please create a GitHub issue with your logs.
