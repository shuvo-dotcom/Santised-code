# Production Best Practices for NFG Analytics on AWS

This document outlines best practices and recommendations for running your NFG Analytics application in a production environment on AWS alongside n8n.

## Server Configuration

### Instance Type

For a balanced application like NFG Analytics with an LLM component:

- **Recommended**: t3.large (2 vCPU, 8GB RAM) or t3.xlarge (4 vCPU, 16GB RAM)
- **Minimum**: t3.medium (2 vCPU, 4GB RAM)

### Storage

- **System Disk**: At least 30GB EBS volume (gp3 type recommended)
- **Data Storage**: Consider a separate EBS volume for persistent data
- **Backup**: Enable automatic EBS snapshots

### Network

- **Security Group**:
  - Allow inbound traffic on your application port (e.g., 8000)
  - Allow SSH access only from trusted IPs
  - Allow HTTP/HTTPS if using a web interface

## Docker Configuration

### Resource Limits

Add resource limits to your Docker Compose file to prevent container resource exhaustion:

```yaml
services:
  nfg-analyst:
    # ... existing configuration ...
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### Logging

Configure proper logging for containerized applications:

```yaml
services:
  nfg-analyst:
    # ... existing configuration ...
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
```

### Restart Policy

Ensure containers restart automatically after system reboots:

```yaml
services:
  nfg-analyst:
    # ... existing configuration ...
    restart: unless-stopped
```

## Security Measures

### API Keys and Secrets

1. **Never hardcode secrets** in your application or Dockerfile
2. Use environment variables for all secrets
3. Consider using AWS Secrets Manager or AWS Parameter Store for sensitive information

### Container Security

1. **Run containers as non-root** when possible
2. **Scan container images** for vulnerabilities
3. **Keep base images updated**

Add to your Dockerfile:

```dockerfile
# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

### Network Security

1. **Use internal Docker networks** for service-to-service communication
2. **Expose only necessary ports** to the host
3. **Implement HTTPS** for all external communications

## Monitoring and Alerting

### Health Checks

Add health check endpoints to your application and configure Docker health checks:

```yaml
services:
  nfg-analyst:
    # ... existing configuration ...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Metrics Collection

1. **Collect application metrics** using Prometheus
2. **Set up dashboards** with Grafana
3. **Monitor API latency, error rates, and resource usage**

### Alerting

1. **Set up alerts** for critical issues
2. **Monitor OpenAI API quota** to avoid unexpected cutoffs
3. **Alert on high error rates** or latency spikes

## Data Management

### Backup Strategy

1. **Regular data backups**:
   ```bash
   # Add to a cron job
   tar -czf /backups/nfg-data-$(date +%Y%m%d).tar.gz /path/to/data/folder
   ```

2. **Backup rotation** to maintain storage efficiency
3. **Test backup restoration** periodically

### Data Persistence

1. **Mount data directories** from the host filesystem
2. **Use a separate EBS volume** for persistent data
3. **Configure regular snapshots** for the data volume

## Scaling Considerations

### Horizontal Scaling

If your application needs to scale:

1. **Use a load balancer** in front of multiple application instances
2. **Ensure data consistency** across instances
3. **Implement session affinity** if needed

### Vertical Scaling

For simpler scaling:

1. **Monitor resource usage**
2. **Upgrade the instance size** when needed
3. **Schedule scaling events** during off-peak hours

## Cost Optimization

### Instance Selection

1. **Use reserved instances** for predictable workloads
2. **Consider Spot Instances** for batch processing tasks
3. **Right-size your instances** based on actual usage

### Resource Efficiency

1. **Implement auto-scaling** for variable workloads
2. **Schedule scaling** for known usage patterns
3. **Optimize container resource limits**

## Continuous Integration/Continuous Deployment

### CI/CD Pipeline

1. **Automate testing** before deployment
2. **Use blue/green deployment** to minimize downtime
3. **Implement automatic rollbacks** on failure

### Deployment Strategy

1. **Use tagged Docker images** for versioned deployments
2. **Keep version history** for quick rollback
3. **Document deployment procedures**

## Documentation

### System Documentation

1. **Document system architecture**
2. **Maintain runbooks** for common operations
3. **Keep configuration details** up to date

### Emergency Procedures

1. **Document emergency procedures** for outages
2. **Maintain contact information** for key personnel
3. **Create troubleshooting guides**

## Integration with n8n

### Resource Allocation

1. **Balance resources** between NFG Analytics and n8n
2. **Monitor resource contention**
3. **Set appropriate limits** for both applications

### Communication

1. **Use efficient API communication** between services
2. **Implement retries and circuit breakers**
3. **Monitor cross-service latency**

## Conclusion

Following these best practices will help ensure a robust, secure, and maintainable deployment of your NFG Analytics application on AWS alongside n8n. Regularly review and update your configuration to adapt to changing requirements and take advantage of new best practices and AWS features.
