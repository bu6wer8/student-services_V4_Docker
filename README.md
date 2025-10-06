# Student Services Platform (Docker Edition)

A comprehensive academic writing services platform with Telegram bot integration, admin panel, and payment processing, now containerized with Docker for easy and reliable deployment.

## 🚀 Features

This version retains all the original features of the platform, but with a more robust and maintainable deployment process.

- **Core Services:** Assignment writing, project development, presentations, and more.
- **Telegram Bot:** Interactive order placement, real-time updates, and customer support.
- **Payment Processing:** Stripe and bank transfer integration.
- **Admin Panel:** Dashboard for managing orders, customers, and payments.
- **Technology Stack:** FastAPI, PostgreSQL, Redis, Nginx, and Docker.

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your server:

- **Docker:** [Install Docker](https://docs.docker.com/engine/install/)
- **Docker Compose:** [Install Docker Compose](https://docs.docker.com/compose/install/)

## 🚀 Quick Start Guide

Deploying the Student Services Platform is now a simple, step-by-step process.

### Step 1: Clone the Repository

First, clone this repository to your server:

```bash
git clone https://github.com/your-username/student-services-platform.git
cd student-services-platform
```

### Step 2: Configure Your Environment

The application is configured using an `.env` file. A template is provided, which you can copy and edit:

```bash
cp .env.example .env
nano .env
```

Update the `.env` file with your specific settings. **It is crucial to set strong, unique passwords and your actual API keys.**

| Variable | Description |
| :--- | :--- |
| `APP_URL` | Your domain name (e.g., `https://yourdomain.com`). |
| `DB_PASSWORD` | A secure password for the PostgreSQL database. |
| `SECRET_KEY` | A long, random string for application security. |
| `ADMIN_PASSWORD` | A secure password for the admin user. |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from @BotFather. |
| `TELEGRAM_ADMIN_ID` | Your Telegram user ID. |
| `STRIPE_PUBLIC_KEY` | Your Stripe public API key. |
| `STRIPE_SECRET_KEY` | Your Stripe secret API key. |
| `STRIPE_WEBHOOK_SECRET` | Your Stripe webhook secret. |

### Step 3: Build and Start the Application

With your configuration in place, you can build and start all the services using the provided `Makefile`:

```bash
make up
```

This command will:

1.  Build the Docker image for the application.
2.  Start the web, bot, database, Redis, and Nginx containers in the background.

### Step 4: Initialize the Database

After the services have started, you need to initialize the database, which will create all the necessary tables and your admin user:

```bash
make db-init
```

### Step 5: Set Up SSL (Recommended)

For a production environment, you must secure your application with an SSL certificate. The `Makefile` includes a helper for this using Let's Encrypt.

1.  **Point your domain's DNS A record to your server's IP address.**

2.  Run the SSL setup command:

    ```bash
    make ssl-setup
    ```

    You will be prompted to enter your domain name.

3.  After the certificates are generated, you need to enable SSL in the Nginx configuration. Open `nginx/nginx.conf` and uncomment the SSL-related lines:

    ```nginx
    # nano nginx/nginx.conf

    # ... (inside the server block for port 443)
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    # ...
    ```

4.  Restart the services to apply the changes:

    ```bash
    make restart
    ```

**Your Student Services Platform is now deployed and ready to use!**

- **Web Interface:** `https://yourdomain.com`
- **Admin Panel:** `https://yourdomain.com/admin`

## ⚙️ Managing Your Application

A `Makefile` is included to simplify the management of your Docker environment. Here are some of the most common commands:

| Command | Description |
| :--- | :--- |
| `make up` | Start all services. |
| `make down` | Stop all services. |
| `make restart` | Restart all services. |
| `make logs` | View real-time logs from all services. |
| `make logs-web` | View logs from only the web application. |
| `make shell` | Access a shell inside the web application container. |
| `make db-shell` | Connect to the PostgreSQL database shell. |
| `make db-backup` | Create a backup of the database. |
| `make status` | Show the status of all running services. |
| `make clean` | Stop and remove all containers and volumes. |

For a full list of commands, run `make help`.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request.

## 📄 License

This project is licensed under the MIT License.

