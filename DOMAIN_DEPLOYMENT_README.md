# 🚀 Sophia AI Intel - Domain Deployment Guide

**Domain**: www.sophia-intel.ai
**Infrastructure**: Lambda Labs GH200 GPU (192.222.51.223)
**Status**: Ready for Production Deployment

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Manual Deployment](#manual-deployment)
5. [GitHub Actions Deployment](#github-actions-deployment)
6. [DNS Configuration](#dns-configuration)
7. [SSL Certificate Setup](#ssl-certificate-setup)
8. [Testing & Verification](#testing--verification)
9. [Management & Monitoring](#management--monitoring)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This guide provides comprehensive instructions for deploying Sophia AI Intel to the production domain `www.sophia-intel.ai` using your existing Lambda Labs infrastructure.

### **Current Architecture**
- **Infrastructure**: Lambda Labs GH200 GPU instances
- **Orchestration**: Docker Compose + Pulumi
- **Domain**: DNSimple API integration
- **SSL**: Let's Encrypt certificates
- **Services**: 8 microservices + dashboard

### **Production URLs** (After Deployment)
- **Main Site**: https://www.sophia-intel.ai
- **Dashboard**: https://www.sophia-intel.ai/
- **API Gateway**: https://www.sophia-intel.ai/api/
- **Research API**: https://www.sophia-intel.ai/research/
- **Context API**: https://www.sophia-intel.ai/context/
- **GitHub API**: https://www.sophia-intel.ai/github/
- **Business API**: https://www.sophia-intel.ai/business/
- **Lambda API**: https://www.sophia-intel.ai/lambda/
- **HubSpot API**: https://www.sophia-intel.ai/hubspot/
- **Agent Swarm**: https://www.sophia-intel.ai/agents/

---

## 🔧 Prerequisites

### **Required GitHub Secrets**
Add these to your repository secrets at: https://github.com/ai-cherry/sophia-ai-intel/settings/secrets/actions

```bash
# Core Infrastructure
PULUMI_ACCESS_TOKEN=<your-pulumi-cloud-token>
LAMBDA_API_KEY=<lambda-labs-api-key>
LAMBDA_PRIVATE_SSH_KEY=<base64-encoded-private-key>

# Database & Cache
NEON_DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://user:pass@host:port

# LLM Providers
OPENAI_API_KEY=sk-...

# DNSimple API
DNSIMPLE_API_TOKEN=<dnsimple-api-token>
DNSIMPLE_ACCOUNT_ID=<dnsimple-account-id>

# Optional APIs
TAVILY_API_KEY=<tavily-api-key>
PERPLEXITY_API_KEY=<perplexity-api-key>
ANTHROPIC_API_KEY=<anthropic-api-key>
HUBSPOT_API_TOKEN=<hubspot-api-token>
```

### **SSH Access**
Ensure your SSH key is added to the Lambda Labs instance:
1. Go to https://cloud.lambdalabs.com/ssh-keys
2. Upload your public SSH key
3. Note the private key path for deployment scripts

### **DNSimple Account**
1. Sign up at https://dnsimple.com
2. Add your domain `sophia-intel.ai`
3. Get your API token and account ID

---

## 🚀 Quick Start

### **Option 1: Automated GitHub Actions (Recommended)**

1. **Add GitHub Secrets** (see Prerequisites section)
2. **Trigger Deployment**:
   ```bash
   # Go to: https://github.com/ai-cherry/sophia-ai-intel/actions
   # Select "Deploy to www.sophia-intel.ai"
   # Click "Run workflow"
   ```
3. **Monitor Progress**: Watch the GitHub Actions logs
4. **Test**: Visit https://www.sophia-intel.ai

### **Option 2: Manual Deployment**

1. **Configure SSH Access**:
   ```bash
   export LAMBDA_SSH_KEY_PATH="$HOME/.ssh/lambda-labs-key"
   chmod 600 "$LAMBDA_SSH_KEY_PATH"
   ```

2. **Run Deployment Script**:
   ```bash
   ./scripts/deploy-domain.sh
   ```

3. **Update DNS** (see DNS Configuration section)

4. **Test**: Visit https://www.sophia-intel.ai

---

## 🔄 Manual Deployment

### **Step 1: SSH to Lambda Labs Instance**
```bash
ssh -i ~/.ssh/lambda-labs-key ubuntu@192.222.51.223
```

### **Step 2: Update System**
```bash
sudo apt-get update
sudo apt-get install -y curl wget git htop nginx certbot python3-certbot-nginx
```

### **Step 3: Deploy Services**
```bash
cd /home/ubuntu
git clone https://github.com/ai-cherry/sophia-ai-intel.git
cd sophia-ai-intel
git pull origin main

# Start services
docker-compose down || true
docker-compose pull
docker-compose up -d --build
```

### **Step 4: Configure nginx**
```bash
sudo cp nginx.sophia-intel.ai.conf /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl reload nginx
```

### **Step 5: Setup SSL**
```bash
sudo certbot --nginx \
  -d www.sophia-intel.ai \
  --non-interactive \
  --agree-tos \
  --email admin@sophia-intel.ai \
  --redirect \
  --hsts \
  --staple-ocsp
```

### **Step 6: Update DNS**
See DNS Configuration section below.

---

## 🤖 GitHub Actions Deployment

### **Workflow Files Created**
- `.github/workflows/deploy-sophia-intel.ai-fixed.yml` - Main deployment workflow
- `nginx.sophia-intel.ai.conf` - Production nginx configuration
- `scripts/deploy-domain.sh` - Manual deployment script

### **Workflow Features**
- ✅ Automated Pulumi deployment to Lambda Labs
- ✅ DNSimple API integration for DNS updates
- ✅ SSL certificate generation and renewal
- ✅ nginx configuration deployment
- ✅ Health checks and endpoint testing
- ✅ Comprehensive logging and artifact collection

### **Triggering the Workflow**
```bash
# Automatic: Push to main branch
git push origin main

# Manual: Via GitHub Actions UI
# Go to Actions → Deploy to www.sophia-intel.ai → Run workflow
```

---

## 🌐 DNS Configuration

### **DNSimple Setup**
1. **Log into DNSimple**: https://dnsimple.com
2. **Select Domain**: sophia-intel.ai
3. **Add A Record**:
   - **Name**: www
   - **Type**: A
   - **Content**: 192.222.51.223
   - **TTL**: 300 (5 minutes for quick updates)

### **DNS Propagation**
- **Time**: 5-30 minutes typically
- **Check Status**: https://dnsimple.com/check
- **Test**: `dig www.sophia-intel.ai`

### **DNS Records Required**
```bash
# A record for the domain
www.sophia-intel.ai. 300 IN A 192.222.51.223

# Optional: Root domain redirect
sophia-intel.ai. 300 IN A 192.222.51.223
```

---

## 🔐 SSL Certificate Setup

### **Automatic (Recommended)**
The deployment script automatically configures SSL:
```bash
sudo certbot --nginx \
  -d www.sophia-intel.ai \
  --non-interactive \
  --agree-tos \
  --email admin@sophia-intel.ai
```

### **Manual SSL Setup**
```bash
# Install certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d www.sophia-intel.ai

# Test renewal
sudo certbot renew --dry-run
```

### **SSL Features**
- ✅ **Free**: Let's Encrypt certificates
- ✅ **Auto-renewal**: Built-in cron job
- ✅ **Security**: HSTS, OCSP stapling
- ✅ **Redirect**: HTTP → HTTPS automatic

---

## 🧪 Testing & Verification

### **Health Checks**
```bash
# Test all endpoints
curl -f https://www.sophia-intel.ai/health
curl -f https://www.sophia-intel.ai/api/health
curl -f https://www.sophia-intel.ai/research/healthz
curl -f https://www.sophia-intel.ai/context/healthz

# Test HTTP redirect
curl -I http://www.sophia-intel.ai
```

### **SSL Verification**
```bash
# Check certificate
echo | openssl s_client -connect www.sophia-intel.ai:443

# SSL Labs test
curl -I https://www.sophia-intel.ai
```

### **Service Verification**
```bash
# SSH to instance
ssh ubuntu@192.222.51.223

# Check containers
docker-compose ps

# View logs
docker-compose logs -f sophia-dashboard
docker-compose logs -f nginx-proxy
```

---

## 📊 Management & Monitoring

### **Daily Operations**
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Update services
docker-compose pull && docker-compose up -d

# Check SSL status
sudo certbot certificates
```

### **SSL Management**
```bash
# Renew certificates
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run

# View certificates
sudo certbot certificates
```

### **DNS Management**
```bash
# Check DNS propagation
dig www.sophia-intel.ai

# Update DNS via DNSimple dashboard
# https://dnsimple.com/domains/sophia-intel.ai
```

### **Backup & Recovery**
```bash
# Backup nginx config
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# Backup SSL certificates
sudo tar -czf /home/ubuntu/ssl-backup.tar.gz /etc/letsencrypt

# Emergency restart
docker-compose restart
```

---

## 🛠️ Troubleshooting

### **Common Issues**

#### **1. DNS Not Propagating**
```bash
# Check DNS
dig www.sophia-intel.ai

# Clear DNS cache (macOS)
sudo killall -HUP mDNSResponder

# Check DNSimple dashboard
# https://dnsimple.com/domains/sophia-intel.ai
```

#### **2. SSL Certificate Issues**
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Delete and reissue
sudo certbot delete --cert-name www.sophia-intel.ai
sudo certbot --nginx -d www.sophia-intel.ai
```

#### **3. nginx Configuration Errors**
```bash
# Test configuration
sudo nginx -t

# View error logs
sudo tail -f /var/log/nginx/error.log

# Restore backup
sudo cp /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf
sudo systemctl reload nginx
```

#### **4. Service Health Issues**
```bash
# Check service logs
docker-compose logs sophia-dashboard
docker-compose logs nginx-proxy

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build
```

#### **5. SSH Connection Issues**
```bash
# Test SSH connection
ssh -i ~/.ssh/lambda-labs-key ubuntu@192.222.51.223

# Check SSH key permissions
chmod 600 ~/.ssh/lambda-labs-key

# Verify Lambda Labs instance status
# https://cloud.lambdalabs.com/instances
```

### **Emergency Procedures**
```bash
# Complete system restart
docker-compose down
docker-compose up -d --build

# nginx emergency restart
sudo systemctl restart nginx

# Full SSL reissue
sudo certbot --nginx -d www.sophia-intel.ai --force-renewal
```

---

## 📞 Support & Resources

### **Documentation**
- **DNSimple**: https://dnsimple.com/docs
- **Let's Encrypt**: https://certbot.eff.org/docs
- **nginx**: https://nginx.org/en/docs
- **Docker Compose**: https://docs.docker.com/compose

### **Management URLs**
- **GitHub Repository**: https://github.com/ai-cherry/sophia-ai-intel
- **GitHub Actions**: https://github.com/ai-cherry/sophia-ai-intel/actions
- **DNSimple Dashboard**: https://dnsimple.com/domains/sophia-intel.ai
- **Lambda Labs**: https://cloud.lambdalabs.com

### **Contact**
- **Email**: admin@sophia-intel.ai
- **SSH**: ubuntu@192.222.51.223
- **Logs**: docker-compose logs -f

---

## 🎉 Success Checklist

- [ ] GitHub secrets configured
- [ ] SSH key uploaded to Lambda Labs
- [ ] DNS A record pointing to 192.222.51.223
- [ ] SSL certificate generated
- [ ] nginx configured and running
- [ ] All services healthy
- [ ] https://www.sophia-intel.ai accessible
- [ ] HTTP redirects to HTTPS
- [ ] All API endpoints responding

**🎊 Your Sophia AI Intel platform is now production-ready at www.sophia-intel.ai!**

---

*Last Updated: August 25, 2025*
*Infrastructure: Lambda Labs GH200 GPU*
*Domain: www.sophia-intel.ai*