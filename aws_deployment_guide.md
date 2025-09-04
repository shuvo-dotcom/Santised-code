# AWS Deployment Guide for NFG Analytics Application

This guide will walk you through deploying the NFG Analytics application to an AWS Ubuntu server that already has n8n running.

## Prerequisites

- AWS Ubuntu server with SSH access
- Docker and Docker Compose installed on the server
- Git installed on the server
- n8n already running on the server
- OpenAI API key

## Step 1: Connect to Your AWS Server

```bash
ssh username@your-aws-server-ip
```

## Step 2: Create a Deployment Directory

```bash
mkdir -p ~/nfg-analytics
cd ~/nfg-analytics
```

## Step 3: Set Up Git and Clone the Repository

If you have your code in a Git repository:

```bash
git clone your-git-repository-url .
```

If not, you'll need to transfer your code to the server:

### Option A: Using SCP (from your local machine)

```bash
# Run this on your local machine
cd /path/to/your/local/project
scp -r ./* username@your-aws-server-ip:~/nfg-analytics/
```

### Option B: Using SFTP

```bash
# Run this on your local machine
cd /path/to/your/local/project
sftp username@your-aws-server-ip
cd ~/nfg-analytics
put -r ./*
exit
```

## Step 4: Create Environment Variables File

On your AWS server:

```bash
cd ~/nfg-analytics
touch .env
```

Edit the .env file using nano or vim:

```bash
nano .env
```

Add the following environment variables:

```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5-mini
DATA_FOLDER=/app/data
PORT=8000
LOG_LEVEL=INFO
```

Save and exit the editor.

## Step 5: Update Port Configuration (if needed)

If port 8000 is already in use by n8n or another service, you'll need to modify the `docker-compose.yml` file to use a different port:

```bash
nano docker-compose.yml
```

Change the port mapping (for example, from 8000:8000 to 9000:8000):

```yaml
ports:
  - "9000:8000"
```

Save and exit the editor.

## Step 6: Build and Start the Docker Container

```bash
docker-compose up -d
```

This will build the Docker image and start the container in detached mode.

## Step 7: Verify the Deployment

Check if the container is running:

```bash
docker-compose ps
```

Check the logs:

```bash
docker-compose logs -f nfg-analyst
```

Test the API:

```bash
curl http://localhost:9000/health
```

## Step 8: Set Up a Reverse Proxy (Optional)

If you want to expose your API to the internet and already have Nginx installed:

```bash
sudo nano /etc/nginx/sites-available/nfg-analytics
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name your-domain-or-server-ip;

    location /nfg-api/ {
        proxy_pass http://localhost:9000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Create a symbolic link:

```bash
sudo ln -s /etc/nginx/sites-available/nfg-analytics /etc/nginx/sites-enabled/
```

Test the configuration:

```bash
sudo nginx -t
```

Reload Nginx:

```bash
sudo systemctl reload nginx
```

## Step 9: Set Up Automatic Startup (Optional)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/nfg-analytics.service
```

Add the following content:

```
[Unit]
Description=NFG Analytics Docker Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/username/nfg-analytics
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable nfg-analytics.service
sudo systemctl start nfg-analytics.service
```

## Step 10: Set Up Monitoring (Optional)

If you want to monitor your application:

```bash
docker-compose exec nfg-analyst curl localhost:8000/metrics
```

You can integrate this with Prometheus if you have it installed.

## Troubleshooting

### Container not starting

Check the logs:

```bash
docker-compose logs nfg-analyst
```

### API not accessible

Check if the container is running and the port is correctly mapped:

```bash
docker ps
netstat -tuln | grep 9000
```

### Permission issues

Make sure the data folder has the correct permissions:

```bash
sudo chown -R 1000:1000 ~/nfg-analytics/data
```

## Maintenance

### Updating the application

```bash
cd ~/nfg-analytics
git pull  # If using git
docker-compose build
docker-compose up -d
```

### Backing up data

```bash
cd ~/nfg-analytics
tar -czvf nfg-data-backup-$(date +%Y%m%d).tar.gz ./data
```

### Checking logs

```bash
docker-compose logs -f nfg-analyst
```
