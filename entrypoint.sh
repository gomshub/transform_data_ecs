#!/bin/bash
set -e
echo "Fetching SSH key from SSM..."
SSH_KEY=$(aws ssm get-parameter --name "$SSM_SSH_KEY_PARAM_NAME" --with-decryption --query "Parameter.Value" --output text)
echo "$SSH_KEY" > /root/.ssh/id_rsa
chmod 600 /root/.ssh/id_rsa
echo "Cloning repository..."
GIT_SSH_COMMAND="ssh -i /root/.ssh/id_rsa -o StrictHostKeyChecking=no" git clone "$GIT_REPO_URL" repo
cd repo
echo "Starting Flask app..."
python app.py
