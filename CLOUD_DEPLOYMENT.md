# 🚀 Graphiti Cloud Deployment Guide

This guide covers the best practices for deploying your Graphiti server and Neo4j in production cloud environments.

## 🏗️ Deployment Options Overview

| Option | Cost | Complexity | Scalability | Best For |
|--------|------|------------|-------------|----------|
| **Docker + VPS** | 💰 Low | ⭐ Simple | ⭐⭐ Medium | Small-Medium projects |
| **Managed Cloud** | 💰💰 Medium | ⭐⭐ Easy | ⭐⭐⭐ High | Production apps |
| **Kubernetes** | 💰💰💰 High | ⭐⭐⭐ Complex | ⭐⭐⭐⭐ Very High | Enterprise |

---

## 🐳 Option 1: Docker + VPS (Recommended for Start)

### Cloud Providers:
- **DigitalOcean Droplet** (4GB RAM, 2vCPU): ~$24/month
- **AWS EC2 t3.medium** (4GB RAM, 2vCPU): ~$30/month  
- **Google Cloud Compute** (e2-medium): ~$25/month
- **Linode** (4GB): ~$24/month

### Quick Setup:

#### 1. Create Environment File
```bash
# .env
OPENAI_API_KEY=your_openai_key_here
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password_here
NEO4J_PORT=7687
```

#### 2. Deploy with Docker Compose
```bash
# On your server
git clone https://github.com/your-username/graphiti.git
cd graphiti
cp .env.example .env  # Edit with your values
docker-compose up -d
```

#### 3. Setup Nginx Reverse Proxy
```nginx
# /etc/nginx/sites-available/graphiti
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 4. Setup SSL with Certbot
```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## ☁️ Option 2: Managed Cloud Services (Recommended for Production)

### A. AWS Deployment

#### Neo4j Options:
1. **Neo4j Aura (Managed)**: $65/month for 2GB RAM
2. **EC2 + Neo4j**: $30-50/month for medium instances

#### Graphiti Server:
- **AWS App Runner**: ~$25/month (automatic scaling)
- **ECS Fargate**: ~$15-40/month  
- **EC2**: ~$30/month

#### Setup with AWS App Runner:
```yaml
# apprunner.yaml
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "Build started on `date`"
      - docker build -t graphiti-server .
run:
  runtime-version: latest
  command: uvicorn graph_service.main:app --host 0.0.0.0 --port 8000
  network:
    port: 8000
    env:
      - NEO4J_URI=bolt://your-neo4j-aura-url:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=your_password
      - OPENAI_API_KEY=your_key
```

### B. Google Cloud Deployment

#### Neo4j Options:
1. **Neo4j Aura**: $65/month
2. **GCE + Docker**: $30-50/month

#### Graphiti Server:
- **Cloud Run**: $0-30/month (pay per request)
- **GCE**: $25-50/month

#### Cloud Run Deployment:
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/graphiti-server
gcloud run deploy --image gcr.io/PROJECT_ID/graphiti-server \
  --platform managed \
  --set-env-vars NEO4J_URI=bolt://your-neo4j-url:7687 \
  --set-env-vars NEO4J_USER=neo4j \
  --set-env-vars NEO4J_PASSWORD=your_password \
  --set-env-vars OPENAI_API_KEY=your_key
```

### C. DigitalOcean App Platform

#### Deploy Button Setup:
```yaml
# .do/app.yaml
name: graphiti-server
services:
- name: api
  source_dir: /
  github:
    repo: your-username/graphiti
    branch: main
  run_command: uv run uvicorn graph_service.main:app --host 0.0.0.0 --port 8000
  environment_slug: docker
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: NEO4J_URI
    value: bolt://your-neo4j:7687
  - key: NEO4J_USER
    value: neo4j
  - key: NEO4J_PASSWORD
    value: ${PASSWORD}
  - key: OPENAI_API_KEY
    value: ${OPENAI_KEY}
databases:
- name: neo4j-db
  engine: PG  # DigitalOcean doesn't have Neo4j, use external
```

---

## 🗄️ Neo4j Hosting Options

### 1. Neo4j Aura (Managed) - **Recommended**
- **Pros**: Fully managed, automatic backups, security
- **Cons**: More expensive
- **Cost**: $65/month (2GB), $165/month (8GB)
- **Setup**: https://neo4j.com/aura/

### 2. Self-Hosted Neo4j
```bash
# Docker Neo4j with persistent data
docker run \
  -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -v neo4j_data:/data \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:5.26.2
```

### 3. Cloud Provider Neo4j
- **AWS**: EC2 + Neo4j AMI
- **GCP**: Compute Engine + Neo4j
- **Azure**: VM + Neo4j

---

## 🛡️ Production Security Checklist

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-...
NEO4J_URI=bolt://your-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secure_password_here

# Optional
MODEL_NAME=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
USE_PARALLEL_RUNTIME=false
```

### Security Best Practices:
- ✅ Use strong Neo4j passwords
- ✅ Enable Neo4j authentication
- ✅ Use HTTPS/SSL certificates
- ✅ Restrict Neo4j network access
- ✅ Set up firewall rules
- ✅ Use environment variables for secrets
- ✅ Enable monitoring and logging

---

## 📊 Performance & Scaling

### Resource Requirements:

#### Minimum (Development):
- **RAM**: 2GB
- **CPU**: 1 vCPU
- **Storage**: 20GB

#### Recommended (Production):
- **RAM**: 4-8GB
- **CPU**: 2-4 vCPU
- **Storage**: 50-100GB SSD

#### Large Scale:
- **RAM**: 16GB+
- **CPU**: 8+ vCPU  
- **Storage**: 500GB+ NVMe

### Neo4j Sizing:
- **Small**: 2GB RAM, 1M nodes
- **Medium**: 8GB RAM, 10M nodes
- **Large**: 32GB RAM, 100M+ nodes

---

## 🎯 Quick Start Commands

### 1. Local Docker Test:
```bash
cp .env.example .env
docker-compose up -d
curl http://localhost:8000/healthcheck
```

### 2. Deploy to DigitalOcean:
```bash
# Create droplet, then:
git clone your-repo
cd graphiti
docker-compose up -d
```

### 3. Deploy to AWS App Runner:
```bash
aws apprunner create-service \
  --service-name graphiti-api \
  --source-configuration file://apprunner.yaml
```

---

## 🔧 Monitoring & Maintenance

### Health Checks:
```bash
# API Health
curl https://your-domain.com/healthcheck

# Neo4j Health  
curl http://your-neo4j:7474/db/neo4j/tx/commit \
  -H "Authorization: Basic $(echo -n 'neo4j:password' | base64)"
```

### Backup Strategy:
```bash
# Neo4j backup
docker exec neo4j neo4j-admin database backup --to-path=/backups neo4j

# Automated daily backups
0 2 * * * docker exec neo4j neo4j-admin database backup --to-path=/backups neo4j
```

---

## 💰 Cost Estimates (Monthly)

### Small Setup (~$90/month):
- DigitalOcean Droplet (4GB): $24
- Neo4j Aura (2GB): $65
- Domain + SSL: $1

### Medium Setup (~$200/month):
- AWS App Runner: $50
- Neo4j Aura (8GB): $165  
- CloudWatch: $10

### Large Setup (~$500/month):
- EKS/ECS: $200
- Neo4j Aura (32GB): $300
- Load balancer, monitoring: $50

---

## 🚀 Getting Started Recommendation

**For your video memory system, start with:**

1. **DigitalOcean Droplet** (4GB) + **Neo4j Aura** (2GB)
2. **Total cost**: ~$90/month
3. **Can handle**: 10k+ videos, real-time queries
4. **Easy upgrade path** to larger instances

This gives you production reliability without complexity!