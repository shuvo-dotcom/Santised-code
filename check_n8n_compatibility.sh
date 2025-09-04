#!/bin/bash
# check_n8n_compatibility.sh - Script to check compatibility with existing n8n setup

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===== NFG Analytics Compatibility Check for n8n =====${NC}"

# Function to check if a port is in use
check_port() {
    if netstat -tuln | grep -q ":$1 "; then
        echo -e "${RED}Port $1 is already in use${NC}"
        USED_PORTS+=($1)
        return 1
    else
        echo -e "${GREEN}Port $1 is available${NC}"
        return 0
    fi
}

# Check if n8n is running
echo -e "\n${YELLOW}Checking if n8n is running...${NC}"
if pgrep -f "n8n" > /dev/null; then
    echo -e "${GREEN}n8n is running${NC}"
    N8N_RUNNING=true
else
    echo -e "${YELLOW}n8n doesn't appear to be running${NC}"
    N8N_RUNNING=false
fi

# Check Docker status
echo -e "\n${YELLOW}Checking Docker status...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}Docker is installed${NC}"
    DOCKER_INSTALLED=true
    
    # Check if Docker is running
    if docker info &> /dev/null; then
        echo -e "${GREEN}Docker is running${NC}"
        DOCKER_RUNNING=true
    else
        echo -e "${RED}Docker is installed but not running${NC}"
        DOCKER_RUNNING=false
    fi
else
    echo -e "${RED}Docker is not installed${NC}"
    DOCKER_INSTALLED=false
    DOCKER_RUNNING=false
fi

# Check port availability
echo -e "\n${YELLOW}Checking port availability...${NC}"
USED_PORTS=()

# Check common ports used by NFG Analytics and n8n
check_port 8000  # Default NFG Analytics port
check_port 5678  # Default n8n port
check_port 80    # HTTP port
check_port 443   # HTTPS port

# Check system resources
echo -e "\n${YELLOW}Checking system resources...${NC}"

# Check CPU
CPU_CORES=$(nproc --all)
echo -e "CPU Cores: $CPU_CORES"
if [ $CPU_CORES -lt 2 ]; then
    echo -e "${YELLOW}Warning: Less than 2 CPU cores available. Performance may be affected.${NC}"
fi

# Check RAM
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
FREE_RAM=$(free -m | awk '/^Mem:/{print $4}')
echo -e "Total RAM: ${TOTAL_RAM}MB, Free RAM: ${FREE_RAM}MB"
if [ $FREE_RAM -lt 1024 ]; then
    echo -e "${YELLOW}Warning: Less than 1GB of free RAM available. Performance may be affected.${NC}"
fi

# Check disk space
DISK_SPACE=$(df -h / | awk 'NR==2 {print $4}')
echo -e "Available disk space: $DISK_SPACE"

# Check Docker network configuration
echo -e "\n${YELLOW}Checking Docker network configuration...${NC}"
if [ "$DOCKER_RUNNING" = true ]; then
    NETWORK_EXISTS=$(docker network ls | grep shared-network || echo "")
    if [ -z "$NETWORK_EXISTS" ]; then
        echo -e "${YELLOW}Shared Docker network not found. Will need to create one.${NC}"
    else
        echo -e "${GREEN}Shared Docker network exists${NC}"
    fi
fi

# Check if Nginx is installed
echo -e "\n${YELLOW}Checking if Nginx is installed (for reverse proxy)...${NC}"
if command -v nginx &> /dev/null; then
    echo -e "${GREEN}Nginx is installed${NC}"
    NGINX_INSTALLED=true
else
    echo -e "${YELLOW}Nginx is not installed. Consider installing for reverse proxy setup.${NC}"
    NGINX_INSTALLED=false
fi

# Generate compatibility report
echo -e "\n${YELLOW}===== Compatibility Report =====${NC}"

# Calculate overall compatibility score
SCORE=0
MAX_SCORE=5
if [ "$N8N_RUNNING" = true ]; then SCORE=$((SCORE+1)); fi
if [ "$DOCKER_INSTALLED" = true ]; then SCORE=$((SCORE+1)); fi
if [ "$DOCKER_RUNNING" = true ]; then SCORE=$((SCORE+1)); fi
if [ ${#USED_PORTS[@]} -eq 0 ]; then SCORE=$((SCORE+1)); fi
if [ $FREE_RAM -ge 1024 ]; then SCORE=$((SCORE+1)); fi

# Display results
echo -e "Compatibility score: $SCORE/$MAX_SCORE"

if [ $SCORE -eq $MAX_SCORE ]; then
    echo -e "${GREEN}Perfect compatibility! You can proceed with installation.${NC}"
elif [ $SCORE -ge 3 ]; then
    echo -e "${YELLOW}Good compatibility. Review warnings before proceeding.${NC}"
else
    echo -e "${RED}Poor compatibility. Address issues before proceeding.${NC}"
fi

# Display action items
echo -e "\n${YELLOW}===== Action Items =====${NC}"

# Port conflicts
if [ ${#USED_PORTS[@]} -gt 0 ]; then
    echo -e "${RED}Port conflicts: ${USED_PORTS[*]}${NC}"
    echo -e "Action: Modify docker-compose.yml to use different ports"
fi

# Docker issues
if [ "$DOCKER_INSTALLED" = false ]; then
    echo -e "${RED}Docker not installed${NC}"
    echo -e "Action: Install Docker using the following commands:"
    echo -e "  sudo apt update"
    echo -e "  sudo apt install -y apt-transport-https ca-certificates curl software-properties-common"
    echo -e "  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -"
    echo -e "  sudo add-apt-repository 'deb [arch=amd64] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable'"
    echo -e "  sudo apt update"
    echo -e "  sudo apt install -y docker-ce"
elif [ "$DOCKER_RUNNING" = false ]; then
    echo -e "${RED}Docker not running${NC}"
    echo -e "Action: Start Docker using the following command:"
    echo -e "  sudo systemctl start docker"
fi

# Nginx for reverse proxy
if [ "$NGINX_INSTALLED" = false ]; then
    echo -e "${YELLOW}Consider installing Nginx for reverse proxy${NC}"
    echo -e "Action: Install Nginx using the following command:"
    echo -e "  sudo apt install -y nginx"
fi

# Docker network
if [ "$DOCKER_RUNNING" = true ] && [ -z "$NETWORK_EXISTS" ]; then
    echo -e "${YELLOW}Create shared Docker network${NC}"
    echo -e "Action: Create shared network using the following command:"
    echo -e "  docker network create shared-network"
fi

# Resource warnings
if [ $CPU_CORES -lt 2 ]; then
    echo -e "${YELLOW}Limited CPU resources${NC}"
    echo -e "Action: Consider upgrading your server or optimizing resource usage"
fi

if [ $FREE_RAM -lt 1024 ]; then
    echo -e "${YELLOW}Limited RAM available${NC}"
    echo -e "Action: Consider freeing up RAM or upgrading your server"
fi

echo -e "\n${YELLOW}===== Next Steps =====${NC}"
echo -e "1. Address any issues mentioned in the Action Items section"
echo -e "2. Follow the deployment guide in aws_deployment_guide.md"
echo -e "3. Configure the integration between NFG Analytics and n8n as described in n8n_integration_guide.md"

echo -e "\n${YELLOW}===== End of Report =====${NC}"
