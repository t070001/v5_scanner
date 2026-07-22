# V5 Scanner VPS Deployment

## Option A: GitHub (Recommended)

```bash
# On your local machine (Windows):
cd "C:\AGENT P\alpha_scan v5"
git remote add origin https://github.com/YOUR_USER/v5-scanner.git
git push -u origin master

# On VPS (Ubuntu):
sudo apt install git python3 -y
git clone https://github.com/YOUR_USER/v5-scanner.git ~/v5_scanner
cd ~/v5_scanner

# Setup .env (IMPORTANT)
cp .env.example .env
nano .env  # Paste your Telegram Bot Token and Chat ID

# Test manually
python3 scanner.py

# Setup crontab (every 3 hours)
crontab -e
# Add this line:
0 */3 * * * cd ~/v5_scanner && python3 scanner.py 2>> logs/cron_error.log
```

## Option B: Direct SCP

```bash
# Local: Transfer ZIP to VPS
scp deploy/v5_scanner.zip ubuntu@YOUR_VPS_IP:~/

# On VPS:
sudo apt install python3 unzip -y
unzip ~/v5_scanner.zip -d ~/v5_scanner
cd ~/v5_scanner

# Setup .env
cp .env.example .env
nano .env  # Paste your Telegram Bot Token and Chat ID

# Test
python3 scanner.py
```

## After first successful scan:
- Check Telegram for Top 10 signals
- Verify CSV: `ls ~/v5_scanner/data/`
- Setup crontab (every 3 hours)

## Environment Variables (.env)
```
TELEGRAM_BOT_TOKEN=your_bot_token_from_@BotFather
TELEGRAM_CHAT_ID=your_chat_id
```
