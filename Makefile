# Student Services Platform - Docker Management
.PHONY: help build up down restart logs shell db-init clean backup restore

# Default target
help:
	@echo "Student Services Platform - Docker Commands"
	@echo "==========================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup          - Initial setup (copy .env, build, start)"
	@echo "  build          - Build Docker images"
	@echo "  up             - Start all services"
	@echo "  down           - Stop all services"
	@echo "  restart        - Restart all services"
	@echo ""
	@echo "Management Commands:"
	@echo "  logs           - View logs from all services"
	@echo "  logs-web       - View web application logs"
	@echo "  logs-bot       - View Telegram bot logs"
	@echo "  logs-db        - View database logs"
	@echo "  shell          - Access web application shell"
	@echo "  db-shell       - Access database shell"
	@echo ""
	@echo "Database Commands:"
	@echo "  db-init        - Initialize database tables"
	@echo "  db-backup      - Create database backup"
	@echo "  db-restore     - Restore database from backup"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  status         - Show service status"
	@echo "  clean          - Remove containers and volumes"
	@echo "  clean-all      - Remove everything including images"
	@echo "  update         - Pull latest images and restart"

# Initial setup
setup:
	@echo "Setting up Student Services Platform..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file from template..."; \
		cp .env.example .env; \
		echo "⚠️  Please edit .env file with your configuration!"; \
	fi
	@make build
	@make up
	@echo "✅ Setup complete! Edit .env file and run 'make restart'"

# Build Docker images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "🌐 Web: http://localhost"
	@echo "📊 Admin: http://localhost/admin"

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart
	@echo "✅ Services restarted!"

# View logs
logs:
	docker-compose logs -f

logs-web:
	docker-compose logs -f web

logs-bot:
	docker-compose logs -f bot

logs-db:
	docker-compose logs -f postgres

# Access application shell
shell:
	docker-compose exec web bash

# Access database shell
db-shell:
	docker-compose exec postgres psql -U student_services -d student_services

# Initialize database
db-init:
	docker-compose exec web python scripts/init_db.py

# Create database backup
db-backup:
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U student_services student_services > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created in backups/"

# Restore database from backup
db-restore:
	@echo "Available backups:"
	@ls -la backups/*.sql 2>/dev/null || echo "No backups found"
	@echo "Usage: make db-restore BACKUP=backups/backup_YYYYMMDD_HHMMSS.sql"
	@if [ -n "$(BACKUP)" ]; then \
		docker-compose exec -T postgres psql -U student_services -d student_services < $(BACKUP); \
		echo "✅ Database restored from $(BACKUP)"; \
	fi

# Show service status
status:
	docker-compose ps

# Clean up containers and volumes
clean:
	docker-compose down -v
	docker system prune -f

# Clean up everything including images
clean-all:
	docker-compose down -v --rmi all
	docker system prune -af

# Update and restart
update:
	docker-compose pull
	docker-compose up -d --build
	@echo "✅ Services updated and restarted!"

# SSL setup helper
ssl-setup:
	@echo "Setting up SSL with Let's Encrypt..."
	@echo "Make sure your domain points to this server first!"
	@read -p "Enter your domain name: " domain; \
	docker run --rm -it \
		-v $(PWD)/nginx/ssl:/etc/letsencrypt \
		-p 80:80 \
		certbot/certbot certonly --standalone -d $$domain
	@echo "✅ SSL certificates generated!"
	@echo "⚠️  Update nginx/nginx.conf to enable SSL and restart with 'make restart'"

# Development mode
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "✅ Development mode started!"
	@echo "🔧 Hot reload enabled"
