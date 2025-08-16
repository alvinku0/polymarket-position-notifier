# Polymarket Position Notifier

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://www.docker.com/)

**Automated notification service for Polymarket trading activities**

Polymarket Position Notifier is a microservice that provides real-time monitoring and notification capabilities for Polymarket trading activities. The system automatically fetches trade notifications, persists them to a database, and delivers formatted alerts to Discord channels.

## Architecture

### System Design

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Polymarket    │    │   Notification   │    │    Discord      │
│      API        │◄───┤     Service      ├───►│    Webhook      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │    MongoDB      │
                       │   (Persistence) │
                       └─────────────────┘
```

### Component Architecture

#### Core Components

1. **PolymarketNotificationService** (`main.py`)
   - Handles scheduling and workflow orchestration

2. **PolymarketNotificationFetcher** (`src/polymarketConnector/`)
   - Interfaces with Polymarket CLOB API
   - Handles authentication and notification fetching

3. **NotificationOperation** (`src/db/`)
   - Database abstraction layer
   - Handles MongoDB connection management
   - Implements notification persistence with deduplication
   
4. **DiscordNotifier** (`src/discordService/`)
   - Discord webhook integration
   - Message formatting and delivery
   - Error handling for webhook failures

5. **ConfigManager** (`src/config/`)
   - Centralized configuration management

### Technology Stack

- **Runtime**: Python 3.11
- **Package Management**: UV
- **Database**: MongoDB
- **Containerization**: Docker & Docker Compose
- **External APIs**: Polymarket CLOB API, Discord Webhooks
- **Configuration**: YAML with environment variable interpolations

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/alvinku0/polymarket-position-notifier.git
cd polymarket-position-notifier

# 2. Configure environment variables
cp env.template .env
nano .env  # Add your credentials

# 3. Start services
sudo ./start.sh

# 4. Verify deployment
sudo docker-compose ps
sudo docker-compose logs -f notification-service
```

## Configuration

### Environment Variables

#### Required Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `PRIVATE_KEY` | Polymarket private key for API authentication | `0x1234...` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications | `https://discord.com/api/webhooks/...` |

#### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `POLYMARKET_PROXY_ADDRESS` | Polymarket proxy contract address | `""` |
| `SIGNATURE_TYPE` | Signature type for Polymarket API | `""` |
| `MONGO_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | MongoDB database name | `polymarket_notifications` |
| `ENVIRONMENT` | Deployment environment | `development` |

### Configuration Files

#### Base Configuration (`config/base.yaml`)

```yaml
polymarket:
  private_key: "${PRIVATE_KEY}"
  proxy_address: "${POLYMARKET_PROXY_ADDRESS:-}"
  signature_type: "${SIGNATURE_TYPE:-}"

discord:
  webhook_url: "${DISCORD_WEBHOOK_URL}"

application:
  fetch_frequency_seconds: 60
  send_to_discord: true

database:
  mongo_url: "${MONGO_URL:-mongodb://localhost:27017}"
  db_name: "${MONGO_DB_NAME:-polymarket_notifications}"

logging:
  level: "INFO"
  file_enabled: true
  console_enabled: false
```

## Monitoring & Operations

### Logging

#### Log Configuration

Logging is configured via `logging_config.py` and supports multiple outputs:

- **File logging**: Enabled by default, logs to `./log/` directory
- **Console logging**: Disabled by default in production
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

#### Health Checks

```bash
# Container health
sudo docker-compose ps

# Service logs
sudo docker-compose logs -f notification-service --tail=100

# Database connectivity
sudo docker-compose exec mongo mongosh --eval "db.runCommand('ping')"
```

### Monitoring Limitation

For high stake usage, consider implementing comprehensive monitoring capabilities.

## Code Organization

```
polymarket-position-notifier/
├── src/                          # Source code
│   ├── config/                   # Configuration management
│   ├── db/                       # Database operations
│   ├── discordService/           # Discord integration
│   └── polymarketConnector/      # Polymarket API client
├── tests/                        # Test suite
├── config/                       # Configuration files
├── log/                          # Log files (created at runtime)
├── main.py                       # Application entry point
├── logging_config.py             # Logging configuration
├── pyproject.toml               # Python project configuration
└── docker-compose.yml           # Container orchestration
```

## Testing

The project includes testing across multiple components:

### Running Tests

```bash
# Run complete test suite
uv run pytest
```

### Individual Test Files

```bash
# Database tests
uv run pytest tests/test_database.py -v

# Discord service tests
uv run pytest tests/test_discord.py -v

# Polymarket client tests
uv run pytest tests/test_polymarket.py -v
```

## Troubleshooting

### Common Issues

#### Service Won't Start

**Symptom**: Container exits immediately or fails to start

**Diagnosis**:
```bash
# Check container logs
sudo docker-compose logs notification-service

# Check configuration
sudo docker-compose config

# Verify environment variables
sudo docker-compose run --rm notification-service env | grep -E "(PRIVATE_KEY|DISCORD_WEBHOOK_URL)"
```

**Solutions**:
1. Verify all required environment variables are set
2. Check private key format and validity
3. Validate Discord webhook URL
4. Ensure MongoDB is accessible

#### Database Connection Issues

**Symptom**: "Failed to connect to MongoDB" errors

**Diagnosis**:
```bash
# Check MongoDB container
sudo docker-compose ps mongo

# Test database connectivity
sudo docker-compose exec mongo mongosh --eval "db.runCommand('ping')"

# Check network connectivity
sudo docker-compose exec notification-service ping mongo
```

**Solutions**:
1. Ensure MongoDB container is running
2. Verify network configuration
3. Check MongoDB authentication (if enabled)
4. Review connection string format

#### API Authentication Failures

**Symptom**: "Authentication failed" or "Invalid signature" errors

**Solutions**:
1. Verify private key format (should start with 0x)
2. Ensure private key has sufficient permissions
3. Check Polymarket API status
4. Verify signature type configuration

### Debug Mode

#### Enable Debug Logging

```yaml
# config/development.yaml
logging:
  level: "DEBUG"
  console_enabled: true
```

#### Recovery Procedures

```bash
# Graceful restart
sudo docker-compose restart notification-service

# Full reset
sudo docker-compose down
sudo docker-compose up -d
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

- ✅ **Commercial Use**: You can use this software commercially
- ✅ **Modification**: You can modify the source code
- ✅ **Distribution**: You can distribute the software
- ✅ **Private Use**: You can use this software privately
- ❗ **Liability**: No warranty or liability provided
- ❗ **Attribution**: Must include original license and copyright

### Third-Party Licenses

This project uses several third-party libraries. Key dependencies include:

- **py-clob-client**: MIT License
- **requests**: Apache 2.0 License
- **pymongo**: Apache 2.0 License
- **pyyaml**: MIT License
- **pytest**: MIT License

## Commands Reference

| Command | Description |
|---------|-------------|
| `sudo ./start.sh` | Build and start all services |
| `sudo docker-compose logs -f` | View all logs |
| `sudo docker-compose ps` | Check service status |
| `sudo docker-compose restart notification-service` | Restart notifier |
| `sudo docker-compose down` | Stop all services |