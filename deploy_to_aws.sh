#!/bin/bash
# deploy_to_aws.sh - Script to deploy NFG Analytics to AWS server

# Set your AWS server details
AWS_USER="ubuntu"
AWS_HOST="your-aws-server-ip"
DEPLOY_DIR="/home/ubuntu/nfg-analytics"
SSH_KEY_PATH="~/.ssh/your_aws_key.pem"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===== NFG Analytics AWS Deployment Script =====${NC}"

# Check if AWS connection details are set
if [ "$AWS_HOST" == "your-aws-server-ip" ]; then
    echo -e "${RED}Error: Please edit this script and set your actual AWS server details.${NC}"
    exit 1
fi

# Function to run SSH commands
run_ssh_command() {
    ssh -i "$SSH_KEY_PATH" "$AWS_USER@$AWS_HOST" "$1"
    return $?
}

# Function to check if command was successful
check_success() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}Step 1: Creating deployment directory on AWS server${NC}"
run_ssh_command "mkdir -p $DEPLOY_DIR"
check_success $?

echo -e "${YELLOW}Step 2: Preparing project files for transfer${NC}"
# Create a temporary directory for the project
TMP_DIR=$(mktemp -d)
cp -r ./* "$TMP_DIR/"

# Ensure .env file exists with placeholders
if [ ! -f ".env" ]; then
    echo "OPENAI_API_KEY=your_openai_api_key_here" > "$TMP_DIR/.env"
    echo "OPENAI_MODEL=gpt-5-mini" >> "$TMP_DIR/.env"
    echo "DATA_FOLDER=/app/data" >> "$TMP_DIR/.env"
    echo "PORT=8000" >> "$TMP_DIR/.env"
    echo "LOG_LEVEL=INFO" >> "$TMP_DIR/.env"
else
    cp .env "$TMP_DIR/.env"
fi

echo -e "${YELLOW}Step 3: Transferring files to AWS server${NC}"
scp -i "$SSH_KEY_PATH" -r "$TMP_DIR"/* "$AWS_USER@$AWS_HOST:$DEPLOY_DIR/"
check_success $?

# Clean up temporary directory
rm -rf "$TMP_DIR"

echo -e "${YELLOW}Step 4: Setting up Docker and Docker Compose on AWS server${NC}"
run_ssh_command "
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo 'Installing Docker...'
        sudo apt update
        sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        sudo add-apt-repository 'deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable'
        sudo apt update
        sudo apt install -y docker-ce
        sudo usermod -aG docker \$USER
    else
        echo 'Docker already installed'
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        echo 'Installing Docker Compose...'
        sudo curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    else
        echo 'Docker Compose already installed'
    fi
"
check_success $?

echo -e "${YELLOW}Step 5: Setting up environment variables${NC}"
read -p "Enter your OpenAI API key: " OPENAI_API_KEY

run_ssh_command "
    cd $DEPLOY_DIR
    sed -i 's/your_openai_api_key_here/$OPENAI_API_KEY/g' .env
"
check_success $?

echo -e "${YELLOW}Step 6: Building and starting the Docker containers${NC}"
run_ssh_command "
    cd $DEPLOY_DIR
    docker-compose up -d
"
check_success $?

echo -e "${YELLOW}Step 7: Verifying deployment${NC}"
run_ssh_command "
    cd $DEPLOY_DIR
    docker-compose ps
    echo 'Checking application logs...'
    docker-compose logs --tail=20 nfg-analyst
"

echo -e "${GREEN}===== Deployment Complete! =====${NC}"
echo -e "Your NFG Analytics application is now running on your AWS server."
echo -e "Access the API at: http://$AWS_HOST:8000"
echo -e "\nTo check logs:"
echo -e "  ssh -i $SSH_KEY_PATH $AWS_USER@$AWS_HOST 'cd $DEPLOY_DIR && docker-compose logs -f nfg-analyst'"
echo -e "\nTo stop the application:"
echo -e "  ssh -i $SSH_KEY_PATH $AWS_USER@$AWS_HOST 'cd $DEPLOY_DIR && docker-compose down'"
