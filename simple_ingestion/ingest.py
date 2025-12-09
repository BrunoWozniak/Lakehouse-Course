import os
import pandas as pd
import logging
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_bucket_exists(s3_client, bucket_name):
    """Checks if a bucket exists, and if not, creates it."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logging.info(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        # If a 404 error is raised, the bucket does not exist.
        if '404' in e.response['Error']['Code'] or 'NoSuchBucket' in e.response['Error']['Code']:
            logging.info(f"Bucket '{bucket_name}' does not exist. Creating it now.")
            s3_client.create_bucket(Bucket=bucket_name)
            logging.info(f"Bucket '{bucket_name}' created successfully.")
        else:
            # Re-raise the exception if it's not a 404.
            logging.error("An unexpected error occurred checking for the bucket.")
            raise

def get_destination_parts(filename):
    """Determines the S3 schema and table from the filename for dbt source compatibility."""
    filename_lower = filename.lower()
    if 'chargenet' in filename_lower:
        schema = 'chargenet'
        table = filename_lower.replace('chargenet_', '').split('.')[0]
        return schema, table
    elif 'ecoride' in filename_lower:
        schema = 'ecoride'
        table = filename_lower.replace('ecoride_', '').split('.')[0]
        return schema, table
    elif 'vehicle_health' in filename_lower:
        schema = 'vehicle_health'
        table = 'logs'
        return schema, table
    else:
        return None, None

def ingest_data():
    """
    Reads data from local files, converts them to Parquet, and uploads them to an S3-compatible service
    in a structure that dbt and Dremio can automatically discover.
    """
    # --- Configuration ---
    data_folder = '/data'
    s3_endpoint_url = os.environ.get('AWS_S3_ENDPOINT')
    s3_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    s3_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket = 'lakehouse'
    bronze_path = 'bronze'

    if not all([s3_endpoint_url, s3_access_key, s3_secret_key]):
        logging.error("S3 environment variables are not fully configured. Please check your docker-compose.yml.")
        return

    logging.info(f"Starting ingestion process from '{data_folder}' to S3 bucket '{s3_bucket}/{bronze_path}'.")

    try:
        s3_client = boto3.client('s3', endpoint_url=s3_endpoint_url, aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key)
        ensure_bucket_exists(s3_client, s3_bucket)

        storage_options = {'key': s3_access_key, 'secret': s3_secret_key, 'client_kwargs': {'endpoint_url': s3_endpoint_url}}

        for filename in os.listdir(data_folder):
            local_file_path = os.path.join(data_folder, filename)
            
            if not os.path.isfile(local_file_path):
                logging.info(f"Skipping directory: {filename}")
                continue

            schema, table = get_destination_parts(filename)
            if not schema:
                logging.warning(f"Skipping file with no defined schema mapping: {filename}")
                continue
            
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(local_file_path)
                elif filename.endswith('.json'):
                    df = pd.read_json(local_file_path)
                else:
                    continue
                
                logging.info(f"Read {filename}...")
                
                # This creates the bronze/schema/table/ structure dbt expects
                # Using s3a:// scheme for Hadoop/Dremio compatibility
                s3_object_path = f"s3a://{s3_bucket}/{bronze_path}/{schema}/{table}/"
                
                logging.info(f"Writing to {s3_object_path}...")
                df.to_parquet(s3_object_path, engine='pyarrow', index=False, storage_options=storage_options)
                logging.info(f"Successfully wrote {filename} to S3.")

            except Exception as e:
                logging.error(f"Failed to process file {filename}. Error: {e}")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    logging.info("Ingestion process complete.")

if __name__ == "__main__":
    ingest_data()