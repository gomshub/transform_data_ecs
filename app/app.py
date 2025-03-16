from flask import Flask, jsonify
import boto3
import os
import pandas as pd

app = Flask(__name__)
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
s3_client = boto3.client("s3","goms-file-processing-bucket")
sqs_client = boto3.client("sqs")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
SQS_URL = os.getenv("SQS_QUEUE_URL" ,"https://sqs.eu-central-1.amazonaws.com/980921754227/file-processing-queue")


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200
@app.route("/process", methods=["POST"])
def process_data():
    messages = sqs_client.receive_message(QueueUrl=SQS_URL, MaxNumberOfMessages=1)
    
    if "Messages" not in messages:
        return jsonify({"message": "No messages in queue"}), 200
    for message in messages["Messages"]:
        s3_file_key = message["Body"]
        process_s3_file(s3_file_key)
        sqs_client.delete_message(QueueUrl=SQS_URL, ReceiptHandle=message["ReceiptHandle"])
    
    return jsonify({"message": "File processed successfully"}), 200
def process_s3_file(s3_key):
    local_file = "/tmp/" + s3_key.split("/")[-1]
    s3_client.download_file(S3_BUCKET, s3_key, local_file)
    
    output_file = local_file.replace(".csv", ".parquet")
    convert_to_parquet(local_file, output_file)
    
    s3_client.upload_file(output_file, S3_BUCKET, "output/" + os.path.basename(output_file))
    print(f"Processed and uploaded {output_file}")
def convert_to_parquet(input_csv, output_parquet):
    df = pd.read_csv(input_csv)
    df.to_parquet(output_parquet, engine="pyarrow")
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

