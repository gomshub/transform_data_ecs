import os
import git
import boto3
from flask import Flask, request, jsonify
# Flask App
app = Flask(__name__)
# AWS Configurations from environment variables
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET", "your-s3-bucket")
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456789012/your-queue-name")
GIT_REPO_URL = os.environ.get("GIT_REPO_URL", "https://github.com/your-org/your-repo.git")
LOCAL_REPO_PATH = "/app/code"
# Ensure the latest code is pulled from the Git repository
def update_repo():
    if os.path.exists(LOCAL_REPO_PATH):
        repo = git.Repo(LOCAL_REPO_PATH)
        repo.remotes.origin.pull()
    else:
        git.Repo.clone_from(GIT_REPO_URL, LOCAL_REPO_PATH)
# S3 Upload Function
def upload_to_s3(file_path, s3_key):
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    try:
        s3_client.upload_file(file_path, S3_BUCKET, s3_key)
        return f"File uploaded to S3: s3://{S3_BUCKET}/{s3_key}"
    except Exception as e:
        return str(e)
# SQS Send Message Function
def send_to_sqs(message):
    sqs_client = boto3.client("sqs", region_name=AWS_REGION)
    try:
        response = sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=message
        )
        return response["MessageId"]
    except Exception as e:
        return str(e)
# Flask Routes
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ECS Task Running"}), 200
@app.route("/process", methods=["POST"])
def process_data():
    update_repo()  # Ensure latest code is pulled
    
    # Example processing logic
    input_data = request.json.get("data", "Default data")
    processed_data = input_data.upper()  # Simulating transformation
# Save processed data to a file
    output_file = "/app/output.txt"
    with open(output_file, "w") as f:
        f.write(processed_data)
    
    # Upload the processed data to S3
    s3_response = upload_to_s3(output_file, "processed/output.txt")
# Send a message to SQS after processing
    sqs_message = f"Processed data: {processed_data}"
    sqs_response = send_to_sqs(sqs_message)
    return jsonify({
        "message": "Data processed and uploaded",
        "s3_response": s3_response,
        "sqs_message_id": sqs_response
    })
@app.route("/receive_from_sqs", methods=["GET"])
def receive_from_sqs():
    sqs_client = boto3.client("sqs", region_name=AWS_REGION)
    
    try:
        # Receive a message from the queue
        response = sqs_client.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20  # Long polling
        )
        
        if "Messages" in response:
            # Get the first message
            message = response["Messages"][0]
            message_body = message["Body"]
            print(f"Received message: {message_body}")
# Delete the message from the queue after processing
            sqs_client.delete_message(
                QueueUrl=SQS_QUEUE_URL,
                ReceiptHandle=message["ReceiptHandle"]
            )
            return jsonify({"status": "Message received", "message_body": message_body}), 200
        else:
            return jsonify({"status": "No messages in the queue"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == "__main__":
    update_repo()  # Ensure latest Git code before running
    app.run(host="0.0.0.0", port=5000)
