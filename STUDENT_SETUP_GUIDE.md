# Setup Guide: Building the Lakehouse Project

Welcome! This guide provides a complete walkthrough for setting up the project infrastructure, ingesting data with Airbyte, and transforming it with dbt.

Please follow these steps carefully.

## Prerequisites

Before you begin, please ensure you have the following software installed on your machine:

1.  **Docker Desktop:** This is essential for running all the services for our data platform. [Download Docker Desktop](https://www.docker.com/products/docker-desktop/).
2.  **Git:** The version control system we use to download the project. [Download Git](https://git-scm.com/downloads).
3.  **Python 3.8+ and pip:** Required for running dbt.
4.  **A Text Editor:** We recommend [Visual Studio Code](https://code.visualstudio.com/download).

**For Windows Users:** Please ensure you have installed and are using the [Windows Subsystem for Linux 2 (WSL2)](https://learn.microsoft.com/en-us/windows/wsl/install). **It is strongly recommended that you perform all steps, including cloning the project, from within your WSL2 terminal.**

---

## Part 1: Start the Core Infrastructure

This step will start all the necessary services for our data lakehouse, including MinIO (our data lake), Dremio (our query engine), and Nessie (our data catalog).

1.  **Get the Project Code:**
    Open your terminal, navigate to the directory where you want to store the project, and clone the repository:
    ```bash
    git clone https://github.com/BrunoWozniak/Lakehouse-Course.git
    cd Lakehouse-Course
    ```

2.  **Start the Services:**
    Run the following command from the root of the project directory. It will download the necessary Docker images and start all services.
    ```bash
    docker-compose up -d
    ```
    You can check that all services are running with `docker ps`. You should see containers for `dremio`, `minio`, `nessie`, `superset`, and `jupyterlab`.

### 3. Configure Dremio to connect to Nessie and MinIO

Once Dremio is up and running (you can access its UI at [http://localhost:9047](http://localhost:9047)), you need to configure a new source to connect to Nessie (our catalog) and MinIO (our data lake storage).

1.  **Log in to Dremio:**
    *   Navigate to [http://localhost:9047](http://localhost:9047).
    *   On your first visit, you will be prompted to create a user. We recommend `dremio` for the username and `dremio123` for the password. Log in with these credentials.
2.  **Add a New Source:**
    *   In the Dremio UI, click on the **+ Add Source** button (usually at the bottom of the left sidebar).
    *   Select **Nessie** from the list of data sources.
3.  **Configure the Nessie Source:**
    Fill in the following details for the Nessie source configuration:

| Field | Value |
| :--- | :--- |
| **Name** | `catalog` |
| **Nessie Endpoint** | `http://nessie:19120/api/v2` |
| **Authentication Type** | `No Authentication` |
| **Storage Provider** | `AWS S3` |
| **AWS Access Key** | `minio` |
| **AWS Secret Key** | `minioadmin` |
| **Connection Properties** | `fs.s3a.endpoint` = `http://minio:9000` |
| | `fs.s3a.path.style.access` = `true` |
| | `dremio.s3.compat` = `true` |

    Click **Save**. Dremio will now be connected to Nessie and MinIO, and you should be able to see the `lakehouse` bucket and any Iceberg tables created by Airbyte.

---

## Part 2: Data Ingestion with Airbyte

This new approach is more robust and simpler to configure. We will upload our source data to a "staging" bucket in MinIO and then use Airbyte's S3 source connector to ingest it into our lakehouse.

### Step 2.1: Upload Source Data to MinIO

First, we need to upload our raw data files into a staging area in MinIO.

1.  **Open the MinIO UI:** Navigate to [http://localhost:9001](http://localhost:9001) and log in (`minio`/`minioadmin`).
2.  **Create a `source` Bucket:** Click the "Create Bucket" button and create a new bucket named `source`.
3.  **Upload Files:** Go into the `source` bucket and click the **Upload** button. Upload all the individual `JSON` and `CSV` files from the `data/` directory in your project. Do not upload the `documents` folder itself, only the files inside the main `data` directory.

### Step 2.2: Install and Run Airbyte

1.  **Install `abctl` (Airbyte CLI):**
    If you haven't already, run the `abctl local install` command. The `--volume` flag is no longer needed with this new approach.
    ```bash
    # This command can take 10-20 minutes to complete.
    abctl local install --low-resource-mode
    ```

2.  **Retrieve Airbyte UI Credentials:**
    Run the following command to get the username and password for the Airbyte web interface.
    ```bash
    abctl local credentials
    ```

### Step 2.3: Configure Airbyte

1.  **First-Time Login:**
    The Airbyte UI should be available at [http://localhost:8000](http://localhost:8000). Use the credentials from the previous step to log in.

2.  **Configure the Iceberg Destination:**
    This is the same as before. Set up the **S3 Data Lake** destination to write Iceberg tables to the `lakehouse` bucket, cataloged in Nessie.

    *   **Destination Type:** S3 Data Lake
    *   **Destination name:** `Lakehouse`
    *   **Format:** `Apache Iceberg`
    *   **AWS Access Key ID:** `minio`
    *   **AWS Secret Access Key:** `minioadmin`
    *   **S3 Bucket Name:** `lakehouse`
    *   **S3 Endpoint:** `http://host.docker.internal:9000`
    *   **Warehouse URI:** `s3://lakehouse/bronze`
    *   **Catalog Type:** `Nessie`
    *   **Nessie URI:** `http://host.docker.internal:19120/api/v2`
    *   **Nessie Namespace:** `main`

3.  **Configure the S3 Sources (One Per File):**
    After extensive testing, we've found the most reliable method is to create **one Airbyte source for each data file**. This prevents resource issues and schema conflicts. You will repeat the following process for every CSV and JSON file you uploaded to the `source` bucket.

    **Example for `ecoride_customers.csv`:**
    1.  Go to **Sources** and click **+ New source**.
    2.  Select **S3** as the source type.
    3.  Configure it as follows:
        *   **Source name:** `S3 - ecoride_customers` (Give each source a unique name!)
        *   **S3 Bucket Name:** `source`
        *   **Globs:** `ecoride_customers.csv` (Use the exact filename)
        *   **Delivery Method:** **`Replicate Records`** (This is critical!)
        *   **File Format:** `CSV`
        *   Use the S3 credentials: `minio` / `minioadmin` and endpoint `http://host.docker.internal:9000`.
    4.  Click **Set up source**.

    **Example for a JSON file (`chargenet_stations.json`):**
    *   **Source name:** `S3 - chargenet_stations`
    *   **Globs:** `chargenet_stations.json`
    *   **Delivery Method:** `Replicate Records`
    *   **File Format:** `JSON`
    *   **Reader Options:** `{"multiLine": true}` (This is critical for our JSON files!)

4.  **Create and Configure Connections:**
    For each source you create, you must then create a connection to the `Lakehouse` destination.
    
    **Example for `S3 - ecoride_customers`:**
    1.  Go to **Connections** and click **+ New connection**.
    2.  Select `S3 - ecoride_customers` as the source and `Lakehouse` as the destination.
    3.  On the next screen, you will see a single stream. Configure it:
        *   **Primary Key:** `id`
        *   **Namespace:** `bronze.ecoride`
        *   **Table Name:** `customers`
    4.  Save the connection and run the first sync.

    **Repeat this entire process (create source, create connection, configure stream) for all your data files.** It's repetitive, but it is the guaranteed path to success.

### Step 2.4: Upload Unstructured Data (PDFs)

This step remains the same. The PDF documents for the RAG application should be uploaded manually to the `lakehouse/bronze/documents/` path in MinIO using the UI.

---

## Part 3: Data Transformation with dbt

With our data in the bronze layer, we'll now use dbt to transform it into `silver` (cleaned) and `gold` (business-ready) layers.

### Step 3.1: Install dbt and Dremio Adapter

In your terminal, run the following pip command to install dbt and the Dremio adapter:
```bash
pip install dbt-dremio
```

### Step 3.2: Configure Dremio Credentials

dbt needs to connect to Dremio. Our dbt profiles are configured to get credentials from environment variables.

1.  **Get Dremio Password:**
    *   Navigate to the Dremio UI at [http://localhost:9047](http://localhost:9047).
    *   On your first visit, you will be prompted to create a user. We recommend using `dremio` for the username and `dremio123` for the password.
2.  **Set Environment Variables:**
    In your terminal, set the following environment variables.

    **For macOS, Linux, or Windows (WSL2):**
    ```bash
    export DREMIO_USER=dremio
    export DREMIO_PASSWORD=dremio123
    ```
    You will need to do this for every new terminal session, or add it to your shell's startup file (e.g., `~/.zshrc`, `~/.bash_profile`).

    **For Windows (PowerShell):**
    ```powershell
    $env:DREMIO_USER="dremio"
    $env:DREMIO_PASSWORD="dremio123"
    ```
    **For Windows (Command Prompt):**
    ```cmd
    set DREMIO_USER=dremio
    set DREMIO_PASSWORD=dremio123
    ```

### Step 3.3: Run the dbt Models

The project contains two separate dbt projects: `silver` and `gold`. You must run them in order from their respective directories.

01.  **Run the Silver Layer:**
    ```bash
    cd transformation/silver
    dbt run
    cd ../..
    ```

2.  **Run the Gold Layer:**
    ```bash
    cd transformation/gold
    dbt run
    cd ../..
    ```

### Summary of Transformations

*   **Silver Layer (Physical Tables - Parquet):**
    *   **What it does:** Cleans the raw bronze data.
    *   **Tasks:** Casts data types (e.g., strings to dates/timestamps), trims whitespace, and selects relevant columns.
    *   **Outcome:** Creates physically cleaned Iceberg tables (as Parquet files) in the `silver` layer of the data lake, also cataloged in Nessie.

*   **Gold Layer (Logical Views):**
    *   **What it does:** Applies business logic to create analysis-ready datasets.
    *   **Tasks:** Joins silver-layer tables to calculate metrics like *Customer Lifetime Value*, *Charging Station Utilization*, and *Vehicle Usage*.
    *   **Outcome:** Creates logical **views** in Dremio's `gold` space. These views don't store data themselves but provide a clean, aggregated layer for analysis.

## Next Steps

Congratulations! You have successfully ingested and transformed your data. You can now:
*   **Explore the Data in Dremio:** Log in to the Dremio UI ([http://localhost:9047](http://localhost:9047)) and query the tables and views you created. You should see `bronze` and `silver` tables in the Nessie source, and `gold` views in the `lakehouse` space.
*   **Build Dashboards in Superset:** Connect Superset ([http://localhost:8088](http://localhost:8088)) to Dremio and start visualizing your gold-layer views.