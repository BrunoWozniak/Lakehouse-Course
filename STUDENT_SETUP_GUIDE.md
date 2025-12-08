# Setup Guide: Lakehouse Project

Welcome! This guide will walk you through setting up the Lakehouse project on your local machine. The goal is to get all the data infrastructure running, ingest our raw data, and run the initial data transformations.

Please follow these steps carefully.

## Prerequisites

Before you begin, please ensure you have the following software installed on your machine:

1.  **Docker Desktop:** This is essential for running all the services for our data platform. [Download Docker Desktop](https://www.docker.com/products/docker-desktop/).
2.  **Git:** The version control system we use to download the project. [Download Git](https://git-scm.com/downloads).
3.  **A Text Editor:** We recommend [Visual Studio Code](https://code.visualstudio.com/download).

**For Windows Users:** Please ensure you have installed and are using the [Windows Subsystem for Linux 2 (WSL2)](https://learn.microsoft.com/en-us/windows/wsl/install) as it is required for Docker Desktop to run Linux containers.

## Step 1: Get the Project Code

First, we need to download the project repository from GitHub.

Open your terminal, navigate to the directory where you want to store the project (e.g., your Documents or a dedicated `Projects` folder), and run the following command:

```bash
git clone <URL_OF_YOUR_LAKEHOUSE_PROJECT_REPO>
cd Lakehouse
```

_(Note to instructor: Please replace `<URL_OF_YOUR_LAKEHOUSE_PROJECT_REPO>` with the actual URL of your repository before sharing with students.)_

## Step 2: Configure the Environment

The project uses a `.env` file to manage credentials and configuration for our local services. Create a new file named `.env` in the root of the `Lakehouse` project directory and paste the following content into it.

> **Note:** These are not real cloud credentials. They are default values used to allow the different services in our local Docker environment to communicate with each other.

```env
# Dremio Credentials
DREMIO_USER=dremio
DREMIO_PASSWORD=dremio123

# MinIO (S3) Credentials for local setup
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minioadmin
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# S3/MinIO Configuration
LAKEHOUSE_S3_PATH=s3a://lakehouse
AWS_S3_ENDPOINT=http://localhost:9000
```

## Step 3: Start the Data Infrastructure

The main `docker-compose.yml` file in the project contains all the core services we need: a data lake (MinIO), a query engine (Dremio), a data catalog (Nessie), and more.

In your terminal, from the root of the `Lakehouse` project directory, run the following command:

```bash
docker-compose up -d
```

This command will download the Docker images and start all the services in the background (`-d`). This may take a few minutes the first time.

## Step 4: Install and Run Airbyte

Next, we will set up Airbyte, our data ingestion tool. We will use its official command-line tool, `abctl`, to install and run it.

1.  **Install `abctl`:**
    Run the following command in your terminal. This downloads and installs the `abctl` tool.

    ```bash
    curl -LsfS https://get.airbyte.com | bash -
    ```

2.  **Install Airbyte:**
    Now, use `abctl` to install Airbyte. This will set up a local, containerized Airbyte platform.

    > **IMPORTANT:** This next command will take **10-20 minutes** to complete as it downloads all the necessary Docker images for Airbyte. Please be patient!

    ```bash
    abctl local install
    ```

3.  **Get Your Credentials:**
    Once the installation is complete, run the following command to get the username and password for the Airbyte web interface:
    ```bash
    abctl local credentials
    ```
    Save these credentials, as you will need them in the next step.

## Step 5: Configure the Airbyte Ingestion Pipeline

Now we will configure Airbyte to move our raw data into the data lake.

1.  **Access the Airbyte UI:**
    Open your web browser and navigate to [http://localhost:8000](http://localhost:8000). Log in using the credentials you retrieved in the previous step.

2.  **Copy Data Files for Airbyte:**
    The Airbyte File Source connector needs access to the data files. The easiest way to grant this is to copy our project's data files into a special directory that Airbyte can see.

    Open a **new terminal window** and run the following commands to create the directory and copy the files:

    ```bash
    mkdir -p /tmp/airbyte_local/
    cp -r data/* /tmp/airbyte_local/
    ```

3.  **Set up the Source:**

    - In the Airbyte UI, go to **Sources** and click **+ New source**.
    - Search for and select the **File** source type.
    - Configure the source:
      - **Source name:** `Local Project Files`
      - **URL:** `/tmp/airbyte_local/` (This is the path _inside_ the container that points to the files you just copied).
      - **Provider > Storage Provider:** `Local`
      - **Reader Options > File Format:** `csv` (You will create separate sources for different file types).
    - Click **Set up source**. Airbyte will discover the CSV files.

4.  **Set up the Destination:**

    - Go to **Destinations** and click **+ New destination**.
    - Search for and select the **S3** destination type.
    - Configure the destination to connect to our local MinIO service:
      - **Destination name:** `Local Data Lake`
      - **S3 Bucket Name:** `lakehouse` (This is the bucket our `docker-compose` service will create).
      - **S3 Bucket Path:** `bronze` (We will write data to the "bronze" layer).
      - **S3 Endpoint:** `http://minioserver:9000` (We use the Docker service name `minioserver` here, not `localhost`).
      - **AWS Access Key ID:** `minio` (This is for our local MinIO, not AWS).
      - **AWS Secret Access Key:** `minioadmin` (This is for our local MinIO, not AWS).
      - **Format > Output Format:** `Parquet`
    - Click **Set up destination**.

5.  **Create and Run the Connection:**
    - Go to **Connections** and click **+ New connection**.
    - Select your `Local Project Files` source and your `Local Data Lake` destination.
    - The connection will automatically detect the streams (your files). You can run a sync for one file or all of them.
    - Click **Set up connection** and run the first synchronization.

After the sync is complete, your raw data will be in the `bronze` layer of your MinIO S3 bucket!

## Step 6: Run Data Transformations (Silver & Gold)

Now that the raw data is in our lake, we will use `dbt` (Data Build Tool) to transform it. The dbt projects are already set up in the `transformation/` directory.

You will need to run these commands from within the `jupyterlab` container, as it has all the necessary Python and dbt tools installed.

1.  **Open a terminal in the JupyterLab container:**
    In your main terminal (not the Airbyte one), run:

    ```bash
    docker exec -it jupyterlab /bin/bash
    ```

    This will give you a shell inside the running container.

2.  **Navigate to the Silver project and run it:**

    ```bash
    cd work/transformation/silver
    dbt run
    ```

    This command will execute the dbt models in the `silver` directory, transforming the raw bronze data into cleaned-up silver tables.

3.  **Navigate to the Gold project and run it:**
    ```bash
    cd ../gold
    dbt run
    ```
    This command will run the final `gold` models, creating the aggregated views for our business intelligence tools.

## Conclusion

Congratulations! You have successfully set up the entire data platform, ingested data with Airbyte, and run the transformation pipelines with dbt. Your data is now ready for analysis and visualization.
