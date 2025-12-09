# Setup Guide: Lakehouse Project (Part 1 - Ingestion)

Welcome! This guide will walk you through setting up the Lakehouse infrastructure and ingesting our raw data into the "bronze" layer of our data lake.

Please follow these steps carefully.

## Prerequisites

Before you begin, please ensure you have the following software installed on your machine:

1.  **Docker Desktop:** This is essential for running all the services for our data platform. [Download Docker Desktop](https://www.docker.com/products/docker-desktop/).
2.  **Git:** The version control system we use to download the project. [Download Git](https://git-scm.com/downloads).
3.  **A Text Editor:** We recommend [Visual Studio Code](https://code.visualstudio.com/download).

**For Windows Users:** Please ensure you have installed and are using the [Windows Subsystem for Linux 2 (WSL2)](https://learn.microsoft.com/en-us/windows/wsl/install) as it is required for Docker Desktop to run Linux containers.

## Step 1: Get the Project Code

First, we need to download the project repository from GitHub.

Open your terminal, navigate to the directory where you want to store the project, and run the following commands:

```bash
git clone https://github.com/BrunoWozniak/Lakehouse-Course.git
cd Lakehouse-Course
```

## Step 2: Configure the Environment

The project uses a `.env` file to manage credentials for our local services. Create a new file named `.env` in the root of the project directory and paste the following content into it.

```env
# MinIO (S3) Credentials for local setup
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minioadmin
```

## Step 3: Start Platform and Ingest Data

The main `docker-compose.yml` file contains all the core services we need, including a custom service that will automatically handle our data ingestion.

In your terminal, from the root of the project directory, run the following command:

```bash
docker-compose up -d --build
```
This command will build the ingestion container, download all service images, start the platform, and run the ingestion script.

## Step 4: Verify Ingestion Success

After a few minutes, the script will finish. You can verify that the data has been successfully ingested by following these steps:

1.  **Open the MinIO UI:**
    Navigate to [http://localhost:9001](http://localhost:9001) in your web browser.

2.  **Log In:**
    Log in to the MinIO console using the credentials from your `.env` file:
    *   Access Key: `minio`
    *   Secret Key: `minioadmin`

3.  **Check for Data:**
    *   You should see a bucket named `lakehouse`.
    *   Inside the `lakehouse` bucket, you will find a `bronze` folder containing all the ingested data, saved in Parquet format.

## Next Steps

Congratulations! You have successfully set up the data platform and ingested the raw data into the bronze layer of the data lake.

The next stages of the project involve connecting our query engine and running data transformations to create the `silver` and `gold` layers. The setup for these tools has proven to be complex, and we will explore robust, alternative solutions for these steps in our next session.

---

## Appendix: Alternative Ingestion with Airbyte

This is an alternative, more advanced method for data ingestion using the Airbyte platform. This setup is more complex and may not work on all systems.

### Step A: Install and Run Airbyte

1.  **Install `abctl`:**
    Run the following command in your terminal. This downloads and installs the Airbyte command-line tool.
    ```bash
    curl -LsfS https://get.airbyte.com | bash -
    ```

2.  **Install Airbyte:**
    Now, use `abctl` to install Airbyte. The `--low-resource-mode` flag is recommended.

    > **IMPORTANT:** This command will take **10-20 minutes** (or more) to complete as it downloads all the necessary Docker images for Airbyte.

    ```bash
    abctl local install --low-resource-mode
    ```

3.  **Get Your Credentials:**
    Once the installation is complete, get the username and password for the Airbyte web interface:
    ```bash
    abctl local credentials
    ```

### Step B: Configure the Airbyte Pipeline

1.  **Access the Airbyte UI:**
    Open your web browser and navigate to [http://localhost:8000](http://localhost:8000). Log in using the credentials from the previous step.

2.  **Copy Data Files for Airbyte:**
    Airbyte needs access to the data files. Copy them into a special directory that Airbyte can see:
    ```bash
    mkdir -p /tmp/airbyte_local/
    cp -r data/* /tmp/airbyte_local/
    ```

3.  **Set up the File Source:**
    *   In Airbyte, go to **Sources** -> **+ New source** and select the **File** source.
    *   **Source name:** `Local Project Files`
    *   **URL:** `/tmp/airbyte_local/`
    *   **Provider:** `Local`
    *   **File Format:** `csv`
    *   Click **Set up source**.

4.  **Set up the S3 Destination:**
    *   Go to **Destinations** -> **+ New destination** and select **S3**.
    *   **Destination name:** `Local Data Lake`
    *   **S3 Bucket Name:** `lakehouse`
    *   **S3 Bucket Path:** `bronze-airbyte` (use a different path to avoid conflicts)
    *   **S3 Endpoint:** `http://host.docker.internal:9000` (for Airbyte in Docker to talk to MinIO on the host)
    *   **AWS Access Key ID:** `minio`
    *   **AWS Secret Access Key:** `minioadmin`
    *   **Format:** `Parquet`
    *   Click **Set up destination**.

5.  **Create and Run the Connection:**
    *   Go to **Connections** -> **+ New connection**.
    *   Connect your `Local Project Files` source to your `Local Data Lake` destination and run the synchronization.