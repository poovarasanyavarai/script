# Dashboard Metrics Processing System

A clean, efficient Python application for processing and storing dashboard analytics metrics from chatbot conversations. Built following KISS (Keep It Simple, Stupid) and DRY (Don't Repeat Yourself) principles.

## 🚀 Features

- **Automated Metrics Processing**: Processes chatbot conversation data and calculates key metrics
- **Multi-Channel Analytics**: Tracks feedback across different communication channels (WhatsApp, Facebook, etc.)
- **Language Distribution Analysis**: Monitors conversation languages and distribution
- **Comprehensive Logging**: Detailed success/failure tracking with performance summaries
- **Database Integration**: PostgreSQL backend with robust connection management
- **Docker Support**: Ready for containerized deployment
- **Clean Architecture**: Well-structured codebase with meaningful file names

## 📊 What It Does

The system processes chatbot metrics including:
- Total conversations per chatbot
- Customer satisfaction scores (CSAT)
- Feedback statistics (positive, negative, average)
- Language distribution analysis
- Channel-specific feedback breakdown
- **Geographic feedback distribution** (STATIC_FB_GEO)
- **Geographic performance data** with interaction dots and country performance (STATIC_PERFORM_BY_GEO)
- **System alerts and notifications** with severity levels (STATIC_ALERTS)
- **Trending metrics and insights** (STATIC_TRENDS)
- **Net impact calculation** (positive - negative feedback ratio)
- **Automation rate percentage**
- Real-time processing with success/failure tracking

## 🏗️ Architecture

```
📁 scripts/
├── 📄 dashboard_metrics_processor.py    # Main entry point
├── 📄 Dockerfile                        # Docker configuration
├── 📄 requirements.txt                 # Python dependencies
├── 📄 .env                             # Environment configuration
├── 📄 README.md                        # This file
└── 📁 dashboard_analytics/             # Core application modules
    ├── 📄 metrics_service.py           # Business logic layer
    ├── 📄 analytics_repository.py      # Data access layer
    ├── 📄 database_connection.py       # Database connection management
    └── 📄 config_query.py             # Configuration queries
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- PostgreSQL database
- pip (Python package manager)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd scripts
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database connection:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

## 🚀 Running the Application

### Method 1: Direct Python Execution
```bash
python3 dashboard_metrics_processor.py
```

### Method 2: Docker Deployment
```bash
# Build the Docker image
docker build -t dashboard-metrics .

# Run the container
docker run dashboard-metrics
```

### Method 3: Azure Container Registry
```bash
# Login to Azure Container Registry
az acr login --name zinfradevv1

# Build and push with correct image name
docker build -t zinfradevv1.azurecr.io/dashboard-metrics:latest .
docker push zinfradevv1.azurecr.io/dashboard-metrics:latest
```

## ☸️ Kubernetes Deployment

The Dashboard Metrics system is designed to run as a Kubernetes CronJob that executes every 15 minutes.

### Prerequisites
- Kubernetes cluster with `kubectl` configured
- Azure Container Registry access
- PostgreSQL database accessible from the cluster

### Build and Push Image

```bash
# Navigate to project directory
cd "/home/poovarasan/Downloads/scripts 4/scripts"

# Login to Azure Container Registry
az acr login --name zinfradevv1

# Build the Docker image with correct tag
docker build -t zinfradevv1.azurecr.io/dashboard-metrics:latest .

# Push to Azure Container Registry
docker push zinfradevv1.azurecr.io/dashboard-metrics:latest
```

### Deploy to Kubernetes

#### Option 1: Automated Deployment (Recommended)
```bash
# Make deployment script executable
chmod +x deploy-k8s.sh

# Run complete deployment
./deploy-k8s.sh
```

#### Option 2: Manual Deployment
```bash
# Apply configuration
kubectl apply -f k8s-configmap.yaml
kubectl apply -f k8s-secret.yaml
kubectl apply -f k8s-cronjob-dashboard-metrics.yaml

# Create ACR secret (if needed)
kubectl create secret docker-registry acr-secret \
    --docker-server=zinfradevv1.azurecr.io \
    --docker-username=<ACR_USERNAME> \
    --docker-password=<ACR_PASSWORD> \
    --docker-email=<ACR_EMAIL>
```

### Kubernetes Configuration

#### CronJob Details
- **Name**: `dashboard-metrics`
- **Schedule**: `*/15 * * * *` (every 15 minutes)
- **Image**: `zinfradevv1.azurecr.io/dashboard-metrics:latest`
- **Namespace**: `default`
- **Resources**: 256Mi/200m requests, 512Mi/500m limits
- **Timeout**: 10 minutes max runtime

#### Environment Variables
| Variable | Value | Source |
|----------|-------|--------|
| `CONFIG_STORE_BASE_URL` | `https://z-config-store.48.216.130.212.nip.io` | ConfigMap |
| `CONFIG_STORE_API_KEY` | `891f41ee454479c49e458c4a7c50dd1e` | Secret |
| `DATABASE_URL` | `postgresql://z_agent_user:z_agent_password@postgresql-shared:5432/z_agent` | CronJob spec |
| `LOG_LEVEL` | `INFO` | ConfigMap |
| `PYTHONPATH` | `/app` | ConfigMap |

### Testing the Kubernetes Deployment

#### Manual Test Execution
```bash
# Create manual test job with new naming convention
kubectl create job --from=cronjob/dashboard-metrics dashboard-metrics-manual-$(date +%s)

# Monitor job progress
kubectl get jobs -l app=dashboard-metrics
kubectl get pods -l app=dashboard-metrics

# View logs
kubectl logs -l app=dashboard-metrics -f
```

#### Expected Test Output
```
✅ Successfully processed: Chatbot Name
✅ Success rate: 100.0% (X/X chatbots)
✅ Metrics insertion completed
Successfully processed X out of X chatbots.
```

### Monitoring and Maintenance

#### Check CronJob Status
```bash
# Verify cronjob configuration
kubectl get cronjob dashboard-metrics

# Check recent executions
kubectl get jobs -l app=dashboard-metrics --sort-by=.metadata.creationTimestamp

# Monitor resource usage
kubectl top pods -l app=dashboard-metrics
```

#### Log Analysis
```bash
# View recent logs
kubectl logs -l app=dashboard-metrics --tail=50

# Follow logs in real-time
kubectl logs -l app=dashboard-metrics -f

# Check specific job logs
kubectl logs job/dashboard-metrics-manual-<timestamp>
```

#### Troubleshooting
```bash
# Describe failed job
kubectl describe job <job-name>

# Check pod events
kubectl describe pod <pod-name>

# View previous pod logs (if container restarted)
kubectl logs <pod-name> --previous
```

### Updating the Deployment

#### Update Docker Image
```bash
# Build new version
docker build -t zinfradevv1.azurecr.io/dashboard-metrics:v2.0 .
docker push zinfradevv1.azurecr.io/dashboard-metrics:v2.0

# Update cronjob with new image
kubectl patch cronjob dashboard-metrics -p '{"spec":{"jobTemplate":{"spec":{"template":{"spec":{"containers":[{"name":"dashboard-metrics","image":"zinfradevv1.azurecr.io/dashboard-metrics:v2.0"}]}}}}}}'
```

#### Update Configuration
```bash
# Update ConfigMap
kubectl apply -f k8s-configmap.yaml

# Update Secret
kubectl apply -f k8s-secret.yaml

# Restart jobs to pick up new config
kubectl delete jobs -l app=dashboard-metrics
```

### Cleanup
```bash
# Delete old completed jobs (keep last 3)
kubectl delete jobs -l app=dashboard-metrics --field-selector=status.successful=1 --ignore-not-found=true

# Clean up test jobs
kubectl delete job dashboard-metrics-manual-<timestamp>
```

## 📝 Configuration

### Environment Variables (.env)
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Application Settings
LOG_LEVEL=INFO
SNAPSHOT_TIME=2025-11-26 12:00:00
```

### Database Schema
The application expects the following database tables:
- `chatbots` - Chatbot configuration
- `conversations` - Conversation records
- `conversation_overall_feedback` - Feedback data
- `chatbot_metrics` - Processed metrics (output)

## 📊 Output Format

The application generates comprehensive metrics in the following format:

```json
{
  "snapshot_time": "2025-11-26 12:00:00",
  "chatbot_id": "chatbot-001",
  "name": "Customer Support Bot",
  "total_conversations": 150,
  "feedback_total": 50,
  "feedback_pos": 40,
  "feedback_neg": 10,
  "feedback_avg": 4.2,
  "languages": "[{\"language\": \"english\", \"count\": 100}]",
  "fb_channel": "[{\"channel\": \"whatsapp\", \"count\": 30}]",
  "ai_csat": 80.0,
  "fb_geo": "[{\"country\": \"India\", \"percentage\": \"85\", \"country_code\": \"IN\"}]",
  "perform_by_geo": "{\"dots\": [{\"lat\": 13.0843, \"lng\": 80.2705, \"country\": \"Tamilnadu\", \"code\": \"IN\", \"interactions\": 80000}], \"countryPerformance\": [{\"country\": \"USA\", \"interactions\": 120000, \"code\": \"US\"}]}",
  "alerts": "[{\"time\": \"1 hr ago\", \"message\": \"ABC Bot fallback rate hit 22%\", \"severity\": \"high\"}]",
  "trends": "[{\"time\": \"1 hr ago\", \"message\": \"Fallback rate in ABC Bot stable at 22%\", \"severity\": \"medium\"}]",
  "net_impact": 60.0,
  "automation_rate": 75.0
}
```

### Static Data Fields Explained

#### **STATIC_FB_GEO** - Geographic Feedback Distribution
```json
[
  {"country": "India", "percentage": "85", "country_code": "IN"},
  {"country": "USA", "percentage": "90", "country_code": "US"}
]
```

#### **STATIC_PERFORM_BY_GEO** - Geographic Performance Data
- **dots**: Geographic coordinates with interaction counts
- **countryPerformance**: Country-wise performance statistics
```json
{
  "dots": [
    {"lat": 13.0843, "lng": 80.2705, "country": "Tamilnadu", "code": "IN", "interactions": 80000}
  ],
  "countryPerformance": [
    {"country": "USA", "interactions": 120000, "code": "US"}
  ]
}
```

#### **STATIC_ALERTS** - System Alerts
Real-time alerts with severity levels (low, medium, high, critical):
```json
[
  {"time": "1 hr ago", "message": "ABC Bot fallback rate hit 22%", "severity": "high"}
]
```

#### **STATIC_TRENDS** - Trending Metrics
Latest trends and insights:
```json
[
  {"time": "1 hr ago", "message": "Positive sentiment steady at 90%", "severity": "low"}
]
```

#### **Calculated Metrics**
- **net_impact**: ((positive_feedback - negative_feedback) / total_feedback) * 100
- **automation_rate**: Percentage of automated vs human-handled conversations

## 📋 Key Functions

### Core Processing Functions
- `get_feedback_by_channel()` - Retrieves feedback counts by communication channel
- `get_language_distribution()` - Analyzes conversation language distribution
- `get_feedback_stats_by_chatbot()` - Calculates feedback statistics per chatbot
- `get_conversations()` - Retrieves conversation data

### Processing Pipeline
1. **Data Collection**: Gathers conversation and feedback data
2. **Metrics Calculation**: Processes raw data into meaningful metrics
3. **Channel Analysis**: Breaks down feedback by communication channels
4. **Language Processing**: Analyzes language distribution
5. **CSAT Calculation**: Computes customer satisfaction scores
6. **Database Storage**: Persists processed metrics with comprehensive logging

## 🐳 Docker Support

### Dockerfile Features
- **Multi-stage build**: Optimized for size and security
- **Python 3.11-slim**: Lightweight base image
- **PostgreSQL dependencies**: Includes required build libraries
- **Log directory**: Creates `/app/logs` for application logs
- **Non-root user**: Security-focused execution

### Docker Commands
```bash
# Build image
docker build -t dashboard-metrics .

# Run with environment file
docker run --env-file .env dashboard-metrics

# Run with volume mounting
docker run -v $(pwd)/logs:/app/logs dashboard-metrics
```

## 📝 Logging

The application provides comprehensive logging:

```
2025-11-26 12:00:00,000 - INFO - 🚀 Starting dashboard metrics processing
2025-11-26 12:00:01,000 - INFO - Processing chatbot: Customer Support Bot
2025-11-26 12:00:01,500 - INFO - ✅ Successfully processed: Customer Support Bot
2025-11-26 12:00:05,000 - INFO - ==================================================
2025-11-26 12:00:05,000 - INFO - METRICS PROCESSING SUMMARY
2025-11-26 12:00:05,000 - INFO - ==================================================
2025-11-26 12:00:05,000 - INFO - Total chatbots: 3
2025-11-26 12:00:05,000 - INFO - Successful: 3
2025-11-26 12:00:05,000 - INFO - Failed: 0
2025-11-26 12:00:05,000 - INFO - Success rate: 100.0%
2025-11-26 12:00:05,000 - INFO - ✅ Dashboard metrics processing completed successfully!
```

## 🔧 Development

### Code Principles
- **KISS (Keep It Simple, Stupid)**: Simple, readable code
- **DRY (Don't Repeat Yourself)**: No code duplication
- **Single Responsibility**: Each function has one clear purpose
- **Error Handling**: Comprehensive error management and logging

### Testing
```bash
# Run structure tests (no dependencies required)
python3 -c "
import ast
for file in ['dashboard_metrics_processor.py', 'dashboard_analytics/metrics_service.py']:
    with open(file, 'r') as f: ast.parse(f.read())
print('✅ All syntax checks passed')
"
```

### Adding New Features
1. Add new functions to `analytics_repository.py` for data access
2. Implement business logic in `metrics_service.py`
3. Update database schema if needed
4. Add appropriate logging and error handling

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Connection**: Check your `.env` configuration
   ```env
   DATABASE_URL=postgresql://user:pass@host:port/db
   ```

3. **Permission Errors**: Ensure proper database permissions
   ```sql
   GRANT SELECT, INSERT ON chatbot_metrics TO your_user;
   ```

4. **Docker Issues**: Check Docker logs
   ```bash
   docker logs <container-id>
   ```

### Performance Optimization
- Use database indexes for frequently queried columns
- Implement connection pooling for high-volume processing
- Consider batch processing for large datasets
- Monitor memory usage for large-scale deployments

## 📈 Monitoring

### Key Metrics to Monitor
- **Processing Time**: Time taken to process each chatbot
- **Success Rate**: Percentage of successfully processed chatbots
- **Database Performance**: Query execution times
- **Error Rates**: Frequency and types of errors

### Log Analysis
Monitor logs for patterns:
```bash
# Filter for errors
grep "ERROR" logs/app.log

# Track success rates
grep "Success rate" logs/app.log

# Monitor processing time
grep "processing completed" logs/app.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style Guidelines
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for complex functions
- Maintain the existing code structure

## 📄 License

[Add your license information here]

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Review the logs for detailed error information

---

**Built with ❤️ following clean code principles**