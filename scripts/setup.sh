#!/bin/bash

# Student Services Platform - Interactive Setup Script
# This script sets up the entire platform with user input

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to prompt for input with default value
prompt_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " input
        if [ -z "$input" ]; then
            input="$default"
        fi
    else
        read -p "$prompt: " input
        while [ -z "$input" ]; do
            echo "This field is required!"
            read -p "$prompt: " input
        done
    fi
    
    eval "$var_name='$input'"
}

# Function to prompt for password
prompt_password() {
    local prompt="$1"
    local var_name="$2"
    
    read -s -p "$prompt: " input
    echo
    while [ -z "$input" ]; do
        echo "Password is required!"
        read -s -p "$prompt: " input
        echo
    done
    
    eval "$var_name='$input'"
}

# Function to generate random string
generate_random() {
    openssl rand -hex 32
}

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. This is not recommended for production."
        read -p "Continue anyway? (y/N): " continue_root
        if [ "$continue_root" != "y" ] && [ "$continue_root" != "Y" ]; then
            exit 1
        fi
    fi
}

# Check system requirements
check_requirements() {
    print_header "Checking System Requirements"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    if [ "$(printf '%s\n' "3.8" "$python_version" | sort -V | head -n1)" != "3.8" ]; then
        print_error "Python 3.8 or higher is required"
        exit 1
    fi
    
    print_status "Python $python_version found"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        print_error "git is not installed"
        exit 1
    fi
    
    print_status "All requirements satisfied"
}

# Install system dependencies
install_system_deps() {
    print_header "Installing System Dependencies"
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y python3-venv python3-pip postgresql postgresql-contrib nginx redis-server supervisor
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y python3-venv python3-pip postgresql postgresql-server nginx redis supervisor
    else
        print_warning "Unknown package manager. Please install dependencies manually:"
        print_warning "- Python 3.8+"
        print_warning "- PostgreSQL"
        print_warning "- Nginx"
        print_warning "- Redis"
        print_warning "- Supervisor"
    fi
}

# Setup Python virtual environment
setup_venv() {
    print_header "Setting up Python Virtual Environment"
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Remove and recreate? (y/N): " recreate_venv
        if [ "$recreate_venv" = "y" ] || [ "$recreate_venv" = "Y" ]; then
            rm -rf venv
        else
            return
        fi
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    print_status "Installing Python packages..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_status "Virtual environment created successfully"
}

# Collect configuration
collect_config() {
    print_header "Configuration Setup"
    
    echo "Please provide the following configuration details:"
    echo
    
    # Basic settings
    prompt_input "Environment (development/production)" "production" ENV
    prompt_input "Debug mode (true/false)" "false" DEBUG
    prompt_input "Application URL" "https://yourdomain.com" APP_URL
    
    echo
    print_status "Database Configuration"
    prompt_input "Database host" "localhost" DB_HOST
    prompt_input "Database port" "5432" DB_PORT
    prompt_input "Database name" "student_services" DB_NAME
    prompt_input "Database user" "student_services" DB_USER
    prompt_password "Database password" DB_PASSWORD
    
    echo
    print_status "Telegram Bot Configuration"
    prompt_input "Telegram Bot Token (from @BotFather)" "" TELEGRAM_BOT_TOKEN
    prompt_input "Telegram Admin ID (your user ID)" "" TELEGRAM_ADMIN_ID
    
    echo
    print_status "Stripe Payment Configuration"
    prompt_input "Stripe Public Key" "" STRIPE_PUBLIC_KEY
    prompt_input "Stripe Secret Key" "" STRIPE_SECRET_KEY
    prompt_input "Stripe Webhook Secret" "" STRIPE_WEBHOOK_SECRET
    
    echo
    print_status "Email Configuration (Optional)"
    prompt_input "SMTP Host" "smtp.gmail.com" SMTP_HOST
    prompt_input "SMTP Port" "587" SMTP_PORT
    prompt_input "SMTP User" "" SMTP_USER
    prompt_password "SMTP Password" SMTP_PASSWORD
    
    echo
    print_status "Security Configuration"
    SECRET_KEY=$(generate_random)
    print_status "Generated secret key: ${SECRET_KEY:0:16}..."
    
    echo
    print_status "Bank Transfer Details"
    prompt_input "Bank Name" "Your Bank" BANK_NAME
    prompt_input "Account Name" "Your Company" BANK_ACCOUNT_NAME
    prompt_input "Account Number" "" BANK_ACCOUNT_NUMBER
    prompt_input "IBAN" "" BANK_IBAN
    prompt_input "SWIFT Code" "" BANK_SWIFT
}

# Create .env file
create_env_file() {
    print_header "Creating Environment File"
    
    cat > .env << EOF
# Environment Configuration
ENV=$ENV
DEBUG=$DEBUG
APP_URL=$APP_URL

# Database Configuration
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
REDIS_URL=redis://localhost:6379

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
telegram_bot_token=$TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_ID=$TELEGRAM_ADMIN_ID
telegram_admin_id=$TELEGRAM_ADMIN_ID

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=$SECRET_KEY
secret_key=$SECRET_KEY
ALGORITHM=HS256

# Stripe Payment Configuration
STRIPE_PUBLIC_KEY=$STRIPE_PUBLIC_KEY
stripe_public_key=$STRIPE_PUBLIC_KEY
STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY
stripe_secret_key=$STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK_SECRET

# Email Configuration
SMTP_HOST=$SMTP_HOST
SMTP_PORT=$SMTP_PORT
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASSWORD

# File Storage
UPLOAD_DIR=./static/uploads
DOWNLOAD_DIR=./static/downloads
MAX_FILE_SIZE=10485760

# Bank Transfer Details
BANK_NAME=$BANK_NAME
BANK_ACCOUNT_NAME=$BANK_ACCOUNT_NAME
BANK_ACCOUNT_NUMBER=$BANK_ACCOUNT_NUMBER
BANK_IBAN=$BANK_IBAN
BANK_SWIFT=$BANK_SWIFT

# Pricing Configuration
BASE_PRICE_ASSIGNMENT=20.0
BASE_PRICE_PROJECT=50.0
BASE_PRICE_PRESENTATION=30.0
URGENCY_MULTIPLIER_24H=2.0

# Business Settings
BUSINESS_NAME=Student Services Platform
SUPPORT_EMAIL=support@yourdomain.com
SUPPORT_TELEGRAM=@your_support
EOF

    print_status "Environment file created"
}

# Setup database
setup_database() {
    print_header "Setting up Database"
    
    # Check if PostgreSQL is running
    if ! systemctl is-active --quiet postgresql; then
        print_status "Starting PostgreSQL..."
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    fi
    
    # Create database and user
    print_status "Creating database and user..."
    sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;
\q
EOF
    
    # Initialize database tables
    print_status "Initializing database tables..."
    source venv/bin/activate
    python scripts/init_db.py
    
    print_status "Database setup completed"
}

# Setup Nginx
setup_nginx() {
    print_header "Setting up Nginx"
    
    # Create Nginx configuration
    sudo tee /etc/nginx/sites-available/student-services << EOF
server {
    listen 80;
    server_name $APP_URL;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $APP_URL;
    
    # SSL Configuration (you'll need to add your certificates)
    # ssl_certificate /path/to/your/certificate.crt;
    # ssl_certificate_key /path/to/your/private.key;
    
    # For now, comment out SSL and use HTTP only
    listen 80;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias $(pwd)/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/student-services /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    sudo nginx -t
    
    # Restart Nginx
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    print_status "Nginx configured successfully"
}

# Setup systemd services
setup_services() {
    print_header "Setting up System Services"
    
    # Web application service
    sudo tee /etc/systemd/system/student-services-web.service << EOF
[Unit]
Description=Student Services Web Application
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/uvicorn app.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    # Telegram bot service
    sudo tee /etc/systemd/system/student-services-bot.service << EOF
[Unit]
Description=Student Services Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python app/bot/bot.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable services
    sudo systemctl daemon-reload
    sudo systemctl enable student-services-web
    sudo systemctl enable student-services-bot
    
    print_status "System services created"
}

# Start services
start_services() {
    print_header "Starting Services"
    
    # Start Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # Start web application
    sudo systemctl start student-services-web
    
    # Start bot
    sudo systemctl start student-services-bot
    
    # Check service status
    print_status "Service Status:"
    sudo systemctl status student-services-web --no-pager -l
    sudo systemctl status student-services-bot --no-pager -l
    
    print_status "All services started"
}

# Setup SSL (optional)
setup_ssl() {
    print_header "SSL Certificate Setup"
    
    read -p "Do you want to set up SSL with Let's Encrypt? (y/N): " setup_ssl_choice
    
    if [ "$setup_ssl_choice" = "y" ] || [ "$setup_ssl_choice" = "Y" ]; then
        # Install certbot
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y certbot python3-certbot-nginx
        elif command -v yum &> /dev/null; then
            sudo yum install -y certbot python3-certbot-nginx
        fi
        
        # Get certificate
        sudo certbot --nginx -d $APP_URL
        
        print_status "SSL certificate installed"
    else
        print_warning "SSL setup skipped. You can set it up later with: sudo certbot --nginx -d $APP_URL"
    fi
}

# Create backup script
create_backup_script() {
    print_header "Creating Backup Script"
    
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash

# Student Services Platform Backup Script

BACKUP_DIR="/var/backups/student-services"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump student_services > $BACKUP_DIR/database_$DATE.sql

# Backup uploaded files
tar -czf $BACKUP_DIR/files_$DATE.tar.gz static/uploads uploaded_works

# Backup configuration
cp .env $BACKUP_DIR/env_$DATE.backup

# Remove old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.backup" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR"
EOF
    
    chmod +x scripts/backup.sh
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/scripts/backup.sh") | crontab -
    
    print_status "Backup script created and scheduled"
}

# Final setup
final_setup() {
    print_header "Final Setup"
    
    # Create necessary directories
    mkdir -p logs static/uploads static/downloads uploaded_works
    
    # Set permissions
    chmod 755 static/uploads static/downloads uploaded_works
    
    # Create admin user (optional)
    read -p "Create admin user? (y/N): " create_admin
    if [ "$create_admin" = "y" ] || [ "$create_admin" = "Y" ]; then
        source venv/bin/activate
        python -c "
from app.models.database import get_db
from app.models.models import User
from datetime import datetime

db = next(get_db())
admin = User(
    telegram_id='$TELEGRAM_ADMIN_ID',
    full_name='Admin User',
    is_admin=True,
    created_at=datetime.utcnow()
)
db.add(admin)
db.commit()
print('Admin user created')
"
    fi
    
    print_status "Final setup completed"
}

# Main installation function
main() {
    print_header "Student Services Platform Setup"
    echo "This script will set up the complete Student Services Platform"
    echo
    
    read -p "Continue with installation? (y/N): " continue_install
    if [ "$continue_install" != "y" ] && [ "$continue_install" != "Y" ]; then
        echo "Installation cancelled"
        exit 0
    fi
    
    check_root
    check_requirements
    
    read -p "Install system dependencies? (y/N): " install_deps
    if [ "$install_deps" = "y" ] || [ "$install_deps" = "Y" ]; then
        install_system_deps
    fi
    
    setup_venv
    collect_config
    create_env_file
    setup_database
    
    read -p "Setup Nginx web server? (y/N): " setup_nginx_choice
    if [ "$setup_nginx_choice" = "y" ] || [ "$setup_nginx_choice" = "Y" ]; then
        setup_nginx
        setup_ssl
    fi
    
    setup_services
    start_services
    create_backup_script
    final_setup
    
    print_header "Installation Complete!"
    echo
    print_status "Your Student Services Platform is now running!"
    print_status "Web interface: http://$APP_URL"
    print_status "Admin panel: http://$APP_URL/admin"
    echo
    print_status "Service management commands:"
    echo "  sudo systemctl status student-services-web"
    echo "  sudo systemctl status student-services-bot"
    echo "  sudo systemctl restart student-services-web"
    echo "  sudo systemctl restart student-services-bot"
    echo
    print_status "Logs location:"
    echo "  Application: $(pwd)/logs/"
    echo "  System: sudo journalctl -u student-services-web -f"
    echo "  System: sudo journalctl -u student-services-bot -f"
    echo
    print_warning "Next steps:"
    echo "1. Test your Telegram bot by messaging it"
    echo "2. Configure your domain DNS to point to this server"
    echo "3. Set up SSL certificate if not done already"
    echo "4. Configure Stripe webhook URL in your Stripe dashboard"
    echo "5. Test the complete order flow"
    echo
    print_status "Setup completed successfully!"
}

# Run main function
main "$@"
