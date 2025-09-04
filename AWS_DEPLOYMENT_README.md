# NFG Analytics - AWS Deployment Package

This package contains all the necessary files and instructions to deploy the NFG Analytics application to an AWS Ubuntu server that already has n8n running.

## Files Included

- `aws_deployment_guide.md`: Detailed step-by-step deployment guide
- `deploy_to_aws.sh`: Automated deployment script
- `check_n8n_compatibility.sh`: Script to check compatibility with existing n8n setup
- `n8n_integration_guide.md`: Guide for integrating with existing n8n setup
- `aws_production_best_practices.md`: Best practices for production deployment

## Quick Start

1. **Check Compatibility**
   
   Run the compatibility check script to identify any potential issues:
   
   ```bash
   ./check_n8n_compatibility.sh
   ```
   
   Address any issues identified in the report.

2. **Customize Deployment**
   
   Edit `deploy_to_aws.sh` to set your AWS server details:
   
   ```bash
   # Set your AWS server details
   AWS_USER="ubuntu"
   AWS_HOST="your-aws-server-ip"
   DEPLOY_DIR="/home/ubuntu/nfg-analytics"
   SSH_KEY_PATH="~/.ssh/your_aws_key.pem"
   ```

3. **Deploy the Application**
   
   Run the deployment script:
   
   ```bash
   ./deploy_to_aws.sh
   ```
   
   Follow the prompts and provide any required information.

4. **Integrate with n8n (Optional)**
   
   Follow the instructions in `n8n_integration_guide.md` to integrate your NFG Analytics application with your existing n8n setup.

5. **Apply Best Practices**
   
   Review the recommendations in `aws_production_best_practices.md` and apply them to your deployment as needed.

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [n8n Documentation](https://docs.n8n.io/)

## Troubleshooting

If you encounter issues during deployment:

1. Check the deployment log output for error messages
2. Verify that all prerequisites are met
3. Check that your AWS server has the necessary permissions
4. Ensure your SSH key has the correct permissions (chmod 600)
5. Verify network connectivity to your AWS server

For more detailed troubleshooting, refer to the respective guide files.

## Support

For additional support or questions:
- Review the documentation in the provided guide files
- Check the original NFG Analytics documentation

## Security Notes

- Always keep your OpenAI API key secure
- Use strong passwords for all services
- Keep your AWS server updated with security patches
- Follow the security best practices outlined in `aws_production_best_practices.md`
