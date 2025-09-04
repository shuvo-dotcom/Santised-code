# NFG Analytics Integration with n8n

This guide provides instructions for integrating your NFG Analytics application with your existing n8n setup on your AWS Ubuntu server.

## Understanding the Integration

n8n (pronounced n-eight-n) is a workflow automation platform that can be used to connect different systems and automate workflows. By integrating your NFG Analytics application with n8n, you can:

1. Trigger workflows based on data from your NFG Analytics application
2. Process data from your NFG Analytics application using n8n's workflow capabilities
3. Send data from other systems to your NFG Analytics application

## Port Management

Since you already have n8n running on your server, it's important to ensure that your NFG Analytics application doesn't conflict with n8n's port usage:

1. n8n typically runs on port 5678 by default
2. Your NFG Analytics application is configured to run on port 8000

If there's a conflict, modify the `docker-compose.yml` file to use a different port for your NFG Analytics application.

## Integration Options

### Option 1: HTTP Request Node in n8n

The simplest way to integrate your NFG Analytics application with n8n is to use the HTTP Request node in n8n:

1. In your n8n workflow, add an "HTTP Request" node
2. Configure the node to call your NFG Analytics API:
   - Method: POST
   - URL: http://localhost:8000/query (or whatever port you've configured)
   - Body: JSON with your query parameters
   - Authentication: None (if both services are on the same server)

### Option 2: Custom n8n Node for NFG Analytics

For a more integrated experience, you can create a custom n8n node for your NFG Analytics application:

1. Set up a development environment for the custom node
2. Create the node that wraps your NFG Analytics API
3. Publish the node to npm or install it locally in your n8n setup

Detailed instructions for creating custom nodes can be found in the [n8n documentation](https://docs.n8n.io/integrations/creating-nodes/).

## Network Configuration

### Option 1: Same Network (Recommended)

If both n8n and your NFG Analytics application are running on the same server:

1. Use Docker's built-in networking
2. In your `docker-compose.yml` file, add:

```yaml
networks:
  default:
    name: shared-network
    external: true
```

Ensure your n8n container is also connected to the same network.

### Option 2: Internal Network Access

If n8n is running outside of Docker or in a different Docker network:

1. Configure your NFG Analytics API to be accessible on the host's network interface
2. Configure firewall rules to allow internal communication between the services

## Environment Variable Management

To share environment variables between your NFG Analytics application and n8n:

1. Create a shared `.env` file with variables needed by both services
2. For n8n-specific variables, maintain them in n8n's configuration
3. For NFG Analytics-specific variables, keep them in your application's `.env` file

## Example n8n Workflow for NFG Analytics

Here's an example of a simple n8n workflow that calls your NFG Analytics API:

1. **Trigger**: Schedule (e.g., every hour)
2. **HTTP Request**:
   - Method: POST
   - URL: http://localhost:8000/query
   - Body: 
     ```json
     {
       "query": "What is the current energy production forecast?",
       "parameters": {}
     }
     ```
3. **Function**: Process the response
4. **Send Email**: Send the results via email

## Monitoring Both Services

To monitor both services together:

1. Set up Prometheus to scrape metrics from both services
2. Configure a Grafana dashboard to visualize the metrics
3. Use a shared log aggregation solution like ELK Stack or Loki

## Load Balancing (Optional)

If you expect high traffic to both services:

1. Set up Nginx as a reverse proxy
2. Configure path-based routing:
   - `/n8n/` routes to your n8n instance
   - `/nfg-api/` routes to your NFG Analytics API

## Security Considerations

When integrating the two services:

1. Use internal networking when possible
2. If exposing APIs externally, implement proper authentication
3. Keep API keys and credentials secure
4. Regularly update both services to patch security vulnerabilities

## Backup Strategy

Implement a backup strategy that covers both services:

1. Back up n8n workflows and credentials
2. Back up NFG Analytics data folder
3. Store backups securely and test restoration processes

## Troubleshooting

If you encounter issues with the integration:

1. Check network connectivity between services
2. Verify port configurations
3. Check logs of both services
4. Test API endpoints individually before integration

Remember that both services should be able to run independently, so you can test each component separately before troubleshooting the integration.
