# AdTicks Spider - Deployment & Operations Guide

---

## Pre-Deployment Checklist

### Code Quality
- [ ] All 17 unit tests passing (`pytest tests/unit/test_web_spider.py -v`)
- [ ] Linting passes (`ruff check app/services/seo/web_spider.py`)
- [ ] Type checking passes (`mypy app/services/seo/web_spider.py`)
- [ ] No security issues (`bandit -r app/services/seo/`)
- [ ] Code coverage > 85% (`pytest --cov=app/services/seo --cov-report=html`)

### Infrastructure
- [ ] PostgreSQL database backed up
- [ ] Redis configured and tested
- [ ] Celery worker running
- [ ] All required environment variables set
- [ ] SSL certificates valid and renewed
- [ ] Firewall rules allow outbound HTTP/HTTPS

### Documentation
- [ ] README updated
- [ ] API documentation complete
- [ ] User guide published
- [ ] Runbooks created
- [ ] Troubleshooting guide available

### Performance
- [ ] Load test passed (10 concurrent crawls)
- [ ] Memory usage < 2GB
- [ ] CPU utilization < 80%
- [ ] Response time < 2 seconds

---

## Deployment Steps

### 1. Build & Push Docker Image

```bash
# Build image
docker build -t adticks-backend:1.0 .

# Tag for registry
docker tag adticks-backend:1.0 registry.example.com/adticks-backend:1.0

# Push to registry
docker push registry.example.com/adticks-backend:1.0

# Verify
docker pull registry.example.com/adticks-backend:1.0
docker inspect registry.example.com/adticks-backend:1.0 | jq '.[0].Created'
```

### 2. Deploy to Kubernetes

```bash
# Update image in deployment
kubectl set image deployment/adticks-backend \
  adticks-backend=registry.example.com/adticks-backend:1.0 \
  --namespace=production

# Monitor rollout
kubectl rollout status deployment/adticks-backend \
  --namespace=production \
  --timeout=5m

# Verify pods are ready
kubectl get pods -n production -l app=adticks-backend
```

### 3. Run Database Migrations

```bash
# Connect to pod
kubectl exec -it deployment/adticks-backend -n production -- /bin/bash

# Run migrations
cd /app && alembic upgrade head

# Verify migrations
alembic current
```

### 4. Pre-Flight Tests

```bash
# Get service endpoint
SERVICE_IP=$(kubectl get svc adticks-backend -n production -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health
curl http://$SERVICE_IP:8002/health

# Test API
TOKEN=$(curl -s http://$SERVICE_IP:8002/api/auth/login -d '{...}' | jq -r '.access_token')
curl -H "Authorization: Bearer $TOKEN" http://$SERVICE_IP:8002/api/auth/me
```

### 5. Blue-Green Deployment (Zero Downtime)

```bash
# 1. Deploy new version alongside old (blue-green)
kubectl apply -f deployment-v1.1-green.yaml -n production

# 2. Test green deployment
GREEN_IP=$(kubectl get svc adticks-backend-green -n production -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$GREEN_IP:8002/health

# 3. Switch traffic to green
kubectl patch service adticks-backend -p '{"spec":{"selector":{"version":"v1.1"}}}' -n production

# 4. Monitor for errors
kubectl logs -f deployment/adticks-backend-green -n production

# 5. Keep blue running for 24h rollback window
kubectl delete deployment adticks-backend-blue -n production --grace-period=86400
```

---

## Operations & Monitoring

### Daily Checks

```bash
#!/bin/bash
# daily_health_check.sh

NAMESPACE="production"
DATE=$(date)

echo "=== AdTicks Backend Daily Health Check - $DATE ===" >> /var/log/adticks/health.log

# 1. Pod health
echo "Checking pod status..."
POD_STATUS=$(kubectl get pods -n $NAMESPACE -l app=adticks-backend -o jsonpath='{.items[].status.phase}' | sort | uniq -c)
echo "Pod Status: $POD_STATUS" >> /var/log/adticks/health.log

# 2. API health
echo "Checking API health..."
HEALTH=$(curl -s http://localhost:8002/health | jq '.status')
echo "API Status: $HEALTH" >> /var/log/adticks/health.log

# 3. Database connection
echo "Checking database..."
kubectl exec -it deployment/adticks-backend -n $NAMESPACE -- \
  python -c "from app.core.database import engine; print(engine.url)" >> /var/log/adticks/health.log

# 4. Redis connection
echo "Checking Redis..."
REDIS_STATUS=$(redis-cli -h $REDIS_HOST PING)
echo "Redis Status: $REDIS_STATUS" >> /var/log/adticks/health.log

# 5. Resource usage
echo "Resource Usage:"
kubectl top nodes >> /var/log/adticks/health.log
kubectl top pods -n $NAMESPACE -l app=adticks-backend >> /var/log/adticks/health.log

echo "" >> /var/log/adticks/health.log
```

### Weekly Maintenance

```bash
#!/bin/bash
# weekly_maintenance.sh

echo "=== Weekly Maintenance: $(date) ===" >> /var/log/adticks/maintenance.log

# 1. Backup database
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > /backups/adticks-$(date +%Y%m%d).sql.gz

# 2. Clear old cache
redis-cli -h $REDIS_HOST EVAL "return redis.call('del', unpack(redis.call('keys', 'component:crawl_results:*')))" 0

# 3. Analyze database
kubectl exec -it deployment/adticks-backend -n production -- \
  psql -U $DB_USER -h $DB_HOST -c "ANALYZE;" $DB_NAME

# 4. Review error logs
journalctl -u adticks-api --since "7 days ago" | grep ERROR | tail -50

# 5. Update dependencies
# (In separate PR/deployment)
pip list --outdated
docker images | grep -i python | sort -k3

echo "Maintenance complete" >> /var/log/adticks/maintenance.log
```

### Monthly Review

- [ ] Review performance metrics
- [ ] Analyze error rates and patterns
- [ ] Capacity planning (growth rate)
- [ ] Security scan results
- [ ] Update documentation
- [ ] Plan feature releases
- [ ] Review customer feedback

---

## Scaling

### Horizontal Scaling (More Pods)

```yaml
# deployment.yaml
spec:
  replicas: 3  # Increase from 1 to 3
  template:
    spec:
      containers:
      - name: adticks-backend
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Vertical Scaling (Bigger Pods)

```yaml
# For high-memory operations (JS rendering future v1.1)
spec:
  template:
    spec:
      containers:
      - name: adticks-backend
        resources:
          requests:
            memory: "2Gi"
            cpu: "2000m"
          limits:
            memory: "4Gi"
            cpu: "4000m"
```

### Auto-Scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: adticks-backend-autoscaler
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: adticks-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max
```

---

## Troubleshooting

### Spider Crawls Return No Results

**Symptoms:** Empty `crawl-results` after crawl completes

**Diagnosis:**
```bash
# Check Celery task status
celery -A app.workers inspect active

# Check Redis cache
redis-cli GET "component:crawl_results:PROJECT_ID"

# Check logs for errors
kubectl logs deployment/adticks-backend | grep spider_crawl
```

**Solutions:**
1. Verify domain is accessible: `curl https://example.com`
2. Check robots.txt: `curl https://example.com/robots.txt`
3. Verify project ID is correct
4. Check firewall rules

### Memory Leak Issues

**Symptoms:** Memory usage grows over time, pod OOMKilled

**Diagnosis:**
```bash
# Monitor memory in real-time
kubectl top pods -n production -l app=adticks-backend --watch

# Check for event objects not being garbage collected
python3 -c "import gc; print([obj for obj in gc.get_objects() if hasattr(obj, '__sizeof__') and obj.__sizeof__() > 1000000])"
```

**Solutions:**
1. Increase memory limits
2. Restart pod gracefully
3. Profile memory usage: `python -m memory_profiler app/services/seo/web_spider.py`

### High Latency Crawls

**Symptoms:** Single crawl taking > 5 minutes

**Diagnosis:**
```bash
# Monitor network
kubectl exec -it deployment/adticks-backend -n production -- \
  tcpdump -i any -n 'host example.com' | head -50

# Check DNS resolution time
nslookup -type=A example.com
```

**Solutions:**
1. Reduce `max_urls` parameter
2. Reduce `max_depth` parameter
3. Check network connectivity
4. Verify target domain isn't rate-limiting bots

### Celery Tasks Stuck

**Symptoms:** Tasks never complete, appear to hang

**Diagnosis:**
```bash
# Check task queue
celery -A app.workers inspect active

# Check Redis connection
redis-cli --latency

# Check worker logs
kubectl logs deployment/celery-worker | tail -100
```

**Solutions:**
1. Restart Celery worker: `celery multi restart worker -A app.workers`
2. Clear stuck tasks: `celery -A app.workers purge`
3. Check Redis memory: `redis-cli INFO memory`

---

## Rollback Procedure

If deployment has critical issues:

```bash
# 1. Identify last known good version
PREVIOUS_IMAGE=$(kubectl get deployment adticks-backend -n production \
  -o jsonpath='{.spec.template.spec.containers[0].image}')

# 2. Rollback
kubectl rollout undo deployment/adticks-backend -n production

# 3. Verify rollback
kubectl rollout status deployment/adticks-backend -n production

# 4. Validate
curl -s http://localhost:8002/health | jq '.status'

# 5. Notify team
echo "Rolled back from $PREVIOUS_IMAGE" | slack-notify
```

---

## Incident Response

### High Error Rate (> 10%)

1. **Alert triggered** - Automated monitoring detects spike
2. **Investigate** - Check logs, error types, affected endpoints
3. **Triage** - Is it database, external API, or application?
4. **Mitigate** - Scale up, restart pods, or rollback
5. **Root cause** - Debug and fix underlying issue
6. **Post-mortem** - Document and prevent recurrence

### Service Unavailable (503)

1. Check pod status: `kubectl get pods -n production -l app=adticks-backend`
2. Check recent events: `kubectl describe pod POD_NAME -n production`
3. Check logs: `kubectl logs POD_NAME -n production`
4. Restart if needed: `kubectl delete pod POD_NAME -n production`

### Database Connection Loss

1. Check database status: `psql -h $DB_HOST -U $DB_USER -c "SELECT 1;"`
2. Check network connectivity
3. Check firewall rules
4. Restart database connection pool: Restart pods

---

## Security Hardening

```yaml
# deployment.yaml
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsReadOnlyRootFilesystem: true
      containers:
      - name: adticks-backend
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
              - ALL
        resources:
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
```

---

**Deployment Status:** Ready for Production ✅  
**Last Updated:** 2026-05-02  
**Next Review:** 2026-06-02
