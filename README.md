# Standing Up a Cloud-Native Market Data Architecture with BigQuery
## Table of contents
1. [Table of contents](#table-of-contents)
1. [Introduction](#introduction)
1. [Objectives](#objectives)
1. [Costs](#costs)
1. [Before you begin](#before-you-begin)
1. [Prepare your environment](#prepare-your-environment)
1. [Transcode and upload the sample data](#upload-the-sample-data)
1. [Explore the data in BigQuery](#explore-the-data-in-bigquery)
<!-- 1. [Run the Market Data pipeline](#run-the-market-data-pipeline)
1. [(Optional) Containerize the transformations](#-optional--containerize-the-transformations)
1. [Clean up](#clean-up)
1. [Delete the project](#delete-the-project)
1. [Delete the individual resources](#delete-the-individual-resources)
1. [What's next](#what-s-next) -->
## Introduction
This document shows you how to run a basic pipeline for ingesting and querying exchange native data formats into BigQuery.
It is intended for data engineers who want to familiarize themselves with a reference architecture for performing cloud-native analytics on high-performance, proprietary exchange data.
In this tutorial, you establish a working example of an exchange data architecture on Google Cloud. This example guides you through launching a data pipeline consisting of these steps:
* The ingestion of exchange binary ITCH messages into BigQuery
* The creation of BigQuery views that combine instrument reference and pricing data
* Authoring queries to extract data from those views
This document assumes that you’re familiar with high-performance exchange binary data feeds, Terraform, Cloud Storage, and BigQuery.
------
## Objectives
* Deploy prerequisite infrastructure to your GCP project using Terraform
* Illustrate the ingestion of binary market data into BigQuery using the transcoder
* Author views that simplify analytics against the dataset in BigQuery 
----
## Costs
This tutorial uses the following billable components of Google Cloud:
* BigQuery
* Cloud Storage
* Cloud Composer
Use the [Pricing Calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your 
projected usage.
-----
## Before you begin
For this reference guide, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). 
You can create a new one, or select a project you already created:
1. Select or create a Google Cloud project.
    [GO TO THE PROJECT SELECTOR PAGE](https://console.cloud.google.com/projectselector2/home/dashboard)
2. Enable billing for your project.
    [ENABLE BILLING](https://support.google.com/cloud/answer/6293499#enable-billing)
3. If you will be using a Cloud Shell instance as your development environment, then in the Cloud Console, activate Cloud Shell.
    [ACTIVATE CLOUD SHELL](https://console.cloud.google.com/?cloudshell=true&_ga=2.175791653.601714487.1648649282-1707141935.1648504534)
    At the bottom of the Cloud Console, a Cloud Shell session starts and displays a command-line prompt. Cloud Shell is a shell environment with the Google Cloud CLI already installed and with values already set for your current project. 
    
It can take a few seconds for the session to initialize.
When you finish this tutorial, you can avoid continued billing by deleting the resources you created. 
See [Clean up](#clean-up) for more detail.
---
## Prepare your environment
1. In Cloud Shell, specify the project that you want to use for this tutorial:
   ```
   gcloud config set project PROJECT_ID
   ```
   Replace PROJECT_ID with the ID of the project that you selected or created for this tutorial. 
   If a dialog displays, click *Authorize*.
2. Specify a default region to use for infrastructure creation:
   ```
   gcloud config set compute/region REGION
   ```
3. Clone the Partner-Code repository to your development environment
   ```
   git clone "git clone https://partner-code.googlesource.com/cloud-fsi-solutions/datacast" 
   ```
5. Install Terraform. To learn how to do this installation, see the [HashiCorp documentation](https://learn.hashicorp.com/tutorials/terraform/install-cli#install-terraform).
6. [Verify](https://learn.hashicorp.com/tutorials/terraform/install-cli#verify-the-installation) the installation
9. Initialize the environment variables: 
    ```
    cd datacast/pipelines && source environment-variables.sh
    ```
10. Run the setup script.
     ```
     cd common_components && ./setup_script.sh
     ```
    
    This will create a `backend.tf` and `terraform.tfvars` files based on the templates.
    If you wish to create a composer infrastructure, manually amand the`terraform.tfvars` so that it 
has `enable_composer=true`
11. Run terraform to create the required infrastructure
     ```
     cd orchestration/infrastructure/
     terraform init -upgrade
     terraform plan
     terraform apply
     ```
    If you enabled Composer at the step before, you will see a URL for the airflow ui. Click on the link to verify 
    the installation.
13. In the Google Cloud Console, go to the **Cloud Storage** page and check for a bucket with a name like 
`${project}-${region}-ingest-bucket` to verify that an ingest bucket has been created.
14. Go to the **BigQuery** page and verify that the following datasets have been created:
     * asx_dev
     * asx_sample_data
----
## Transcode and upload the sample data
In this section, you explore the sample input file, and run the Market Data Transcoder to load transcoded sample data 
to BigQuery. 
1. In the Cloud Shell Editor instance, inspect the input file by running the following commands:
<!-- WILL UPDATE WITH DATA SOURCE ONCE PCAPs ARE READY -->
    <!-- ```
    ing_bk=`gsutil ls | grep ingest-bucket`
    pub_bk="gs://reg-rpt-pattern-matait-dev-us-ingest-bucket/asx/"
    
    cd ../../../../pipelines/asx/ 
    gsutil cp ${pub_bk}NTP_220306_1646551229.log input_data/NTP_220306_1646551229.log
    head -c 1000 input_data/NTP_220306_1646551229.log
    ``` -->
    The commands print the input file's first 1000 bytes to Cloud Shell's standard output. Notice that some of the file's characters are non-ASCII
because the file is in binary rather than text format.
2. Open, and inspect, the /source folder. It contains an application which accepts command-line arguments. 
The class parses dynamic length binary messages in a binary format file and decodes them into input formats 
accepted by BigQuery and PubSub, according to a specified schema. More details are available in the Market 
Data Transcoders's [documentation](../README.md).
3. Run the Transcoder to load the file's decoded contents into Avro Files and then BigQuery:
    ```
    cd ../../
    
    python3 -m venv env && source env/bin/activate
    pip3 install -r requirements.txt
    python3 main.py -source_file cme/cme.incr.b64l -schema_file cme/schemas/templates_FixBinary_v12.xml --base64 -factory cme -source_file_format_type line_delimited -output_path=cme_avroOut 
    ```
    The data has now been decoded and persisted to Avro. 
----
## Create Streaming Pipeline via Dataflow
In this section we will create a streaming pipeline via Cloud Dataflow to load the data into the BigQuery sink.
1. In the Cloud Shell instance, use the following commands. Enable services:
    ```
    gcloud services enable dataflow.googleapis.com
 4   ```
2. Copy Avro Schema File into GCS Bucket
    ```
    gsutil cp cme_avroOut/cme.incr-MDIncrementalRefreshBook46.avsc gs://${PROJECT_ID}-eu-ingest-bucket
    ```
3. Create Topic
    ```
    gcloud pubsub topics create MDIncrementalRefreshBook46
    gcloud pubsub topics create dead-letter
    ```
4. Create Pub/Sub Subscriptions
    ```
    gcloud pubsub subscriptions create refreshbook-subscription \
    --topic=MDIncrementalRefreshBook46 \
    --topic-project=${PROJECT_ID}
    gcloud pubsub subscriptions create dead_letter \
    --topic=MDIncrementalRefreshBook46 \
    --topic-project=${PROJECT_ID}
    ```
<!-- TODO Add permissions to default compute service account for permissions to pubsub -->
5. Create Dataflow job to write data streamed from PubSub to Avro
    ```
    gcloud compute networks create default --subnet-mode=auto --bgp-routing-mode=global
    gcloud compute networks subnets update default --region=${REGION} --enable-private-ip-google-access
    <!-- gcloud beta dataflow flex-template run refreshbook-to-bq \
    --region=${REGION} \
    --disable-public-ips \
    --subnetwork=regions/${REGION}/subnetworks/default \
    --template-file-gcs-location=gs://dataflow-templates/latest/flex/PubSub_Avro_to_BigQuery \
    --additional-experiments=enable_secure_boot \
    --parameters \
schemaPath=gs://${PROJECT_ID}-eu-ingest-bucket/cme.incr-MDIncrementalRefreshBook46.avsc,\
inputSubscription=projects/${PROJECT_ID}/subscriptions/refreshbook-subscription,\
outputTableSpec=${PROJECT_ID}:cme_bq_dev.refresh_book_streamed ,\
outputTopic=projects/${PROJECT_ID}/topics/dead-letter -->
gcloud dataflow jobs run ps-to-avro-MDIncrementalRefreshBook46 --gcs-location gs://dataflow-templates-us-central1/latest/Cloud_PubSub_to_Avro --region us-central1 --staging-location gs://wfic-lab-harry-eu-dataflow-bucket/temp/ --parameters inputTopic=projects/wfic-lab-harry/topics/MDIncrementalRefreshBook46,outputDirectory=gs://wfic-lab-harry-eu-dataflow-bucket,avroTempDirectory=gs://wfic-lab-harry-eu-dataflow-bucket/temp/ --disable-public-ips --additional-experiments=enable_secure_boot 
    ```
6. Run the Transcoder to publish and stream the file's decoded contents into Pub/Sub:
    ```
    python3 main.py -source_file cme/cme.incr.b64l -schema_file cme/schemas/templates_FixBinary_v12.xml --base64 -factory cme -source_file_format_type line_delimited -output_type pubsub -output_encoding=binary -destination_project_id $PROJECT_ID 
    ``` 
    Navigate to [Pub/Sub](https://console.cloud.google.com/cloudpubsub) within the Cloud Console to view the topics created.
    Navigate to [Dataflow](https://console.cloud.google.com/dataflow) within the Cloud Console and select the refreshbook-to-bq	job to view the status of the job. The job may take 3 minutes to start.
7. Load the resultant data to BigQuery
    ```
    bq load \
    --source_format=AVRO \
    ${PROJECT_ID}:cme_bq_dev.refresh_book_streamed \
    "gs://wfic-lab-harry-eu-dataflow-bucket/*.avro"
    ```   
    The data is now published from real time streams on Cloud Pub/Sub and loaded into BigQuery. 
----
## Explore the data in BigQuery
<!-- In this section, you will use BigQuery to glean insights from the order data included in ASX's incremental feed.
1. In the Cloud Shell Editor instance, create a BigQuery view that aggregates granular ASX order data:
    ```
    cd pipelines/asx/sql
    ./mk_eod_stats_view.sh
    ```
    The view shows order execution volume aggregated by futures product families, arranged from most to least active family. -->
<!-- 3. Load the data into Cloud Storage:
    ```
    ./load_to_gcs.sh ../data/input
    ./load_to_gcs.sh ../data/expected
    ```
   
    The data is now available in your Cloud Storage ingest bucket. 
4. Load the data from the Cloud Storage ingest bucket to BigQuery:
    ```
    ./load_to_bq.sh
    ```
    To verify that the data has been loaded in BigQuery, in the console, go to the BigQuery page and select a table in 
both the `homeloan_data` and `homeloan_expectedresults` datasets.
    Select the Preview tab for each table, and confirm that each table has data.
5. To verify that the data has been loaded in BigQuery, in the console, go to the BigQuery page and select a table in 
both the `homeloan_data` and `homeloan_expectedresults` datasets. 
    Select the **Preview** tab of each table and check that data has been populated.
----
## Run the Market Data pipeline
1. In your development environment, initialize the dependencies of dbt:
    ```
    cd ../dbt/
    dbt deps
    ```
    This will install any needed dbt dependencies in your dbt project.
2. Test the connection between your local dbt installation and
   your BigQuery datasets by running the following command:
    ```
    dbt debug 
    ```
    At the end of the connectivity, configuration and dependency info returned by the command, you should see the 
following message: `All checks passed!`
   In the `models` folder, open a SQL file to inspect the logic of the sample reporting transformations implemented 
in DBT. 
3. Run the reporting transformations to create the Market Data metrics:
    ```
    dbt run
    ```
4. Run the transformations for a date of your choice:
    ```
    dbt run --vars '{"reporting_day": "2021-09-03"}'
    ```
   
    Notice the variables that control the execution of the transformations. The variable `reporting_day` indicates the 
date value that the portfolio should have. When you run the `dbt run` command, it's a best practice to provide this 
value.
5. In the console, go to the BigQuery page and inspect the `homeloan_dev` dataset. Notice how the data has been populated,
and how the `reporting_day` variable that you passed is used in the `control.reporting_day` field of the 
`wh_denormalised` view.
6. Inspect the models/schema.yml file:
    ```
    models:
     - <<: *src_current_accounts_attributes
       name: src_current_accounts_attributes
       columns:
         - name: ACCOUNT_KEY
           tests:
             - unique
                  - not_null
    ```
    Notice how the file defines the definitions of the columns and the associated data quality tests. 
For example, the `ACCOUNT_KEY` field in the src_current_accounts_attributes table must be unique and not null.
7. Run the data quality tests that are specified in the config files:
    ```
    dbt test -s test_type:generic 
    ```
   
8. Inspect the code in the ` use_cases/examples/home_loan_delinquency/dbt/tests `folder, which contains `singular`
tests.  Notice how the tests in this folder implement a table comparison between actual results as outputted by 
the `dbt run` command, and expected results as saved in the `homeloan_expectedresults` dataset.
9. Run the singular tests:
    ```
    dbt test -s test_type:singular
    ```
10. Generate the documentation for the project:
    ```
    dbt docs generate --profiles-dir profiles && dbt docs serve --profiles-dir profiles 
    ```
11. In the output that you see, search for, and then click, the following URL text: http://127.0.0.1:8080
    
    Your browser opens a new tab that shows the dbt documentation web interface.
12. Explore the lineage of the models, and their detailed documentation. You see that  the documentation includes all
the models’ documentation as specified in the  models/schema.yml files, and all the code of the models.
----
## (Optional) Containerize the transformations
1. Create a container for the BigQuery data load step, and push the container to Google Container Repository:
    ```
    cd ../../../../     # the gcloud command should be executed from the root 
    gcloud builds submit --config use_cases/examples/home_loan_delinquency/data_load/cloudbuild.yaml
    ```
    The Dockerfile in the data_load directory enables this containerization, which simplifies orchestration of the 
   workflow.
2. Containerize the DBT code for the data transformation step, and push the container to Google Container Repository. 
    ```
    gcloud builds submit --config use_cases/examples/home_loan_delinquency/dbt/cloudbuild.yaml
    ```
    Containerization helps you to create a package that can be easily versioned and deployed. 
3. Retrieve the path of the Airflow UI and the GCS bucket for dags, and store them in
   environment variables. 
   You will need to use the AIRFLOW_DAG_GCS to upload the Airflow DAG, and the AIRFLOW_UI 
   to log into Composer and see the progress of the orchestration.
    ```
    cd common_components/orchestration/infrastructure/ 
    AIRFLOW_DAG_GCS=$(terraform output --raw airflow_dag_gcs_prefix)
    AIRFLOW_UI=$(terraform output --raw airflow_uri)
    ```
4. Upload the home loan delinquency dag.
    ```
    cd ../../../use_cases/examples/home_loan_delinquency/deploy/
    gsutil cp run_homeloan_dag.py $AIRFLOW_DAG_GCS
    ```
   
5. Head to the Airflow UI and see the process executing. 
   Execute the command below to retrieve the UI, and click on the link:
   ```
   echo $AIRFLOW_UI
   ```
6. In the UI, after a few minutes you should see the home-loan-delinquency DAG.
   Click on the Last Run and you should see a diagram like the one below.
    ![image](images/airflow-ui.png)
    Note how the DAG consists of the following steps:
    * Load the data into BigQuery, using the data-load container
    * Execute the home loan delinquency transformations, using the dbt container
    * Execute the data quality tests and regression tests, using the dbt container
----
## Clean up
To avoid incurring charges to your Google Cloud account for the resources used in this tutorial:
### Delete the project
The easiest way to eliminate billing is to delete the project you created for the tutorial.
**Caution**: Deleting a project has the following effects:
* **Everything in the project is deleted.** If you used an existing project for this tutorial, when you delete it, you also delete any otherwork you've done in the project.
* **Custom project IDs are lost.** When you created this project, you might have created a custom project ID that you want to use in thefuture. To preserve the URLs that use the project ID, such as an **<code>appspot.com</code></strong> URL, delete selected resources inside theproject instead of deleting the whole project.
If you plan to explore multiple tutorials and quickstarts, reusing projects can help you avoid exceeding project quota limits.
1. In the Cloud Console, go to the **Manage resources** page. \
[Go to the Manage resources page](https://console.cloud.google.com/iam-admin/projects)
1. In the project list, select the project that you want to delete and then click **Delete **
1. In the dialog, type the project ID and then click **Shut down** to delete the project.
----
## Delete the individual resources
To avoid incurring further charges, destroy the resources.
```
cd ../../../../common_components/orchestration/infrastructure/
terraform destroy
```
----
## What's next
* Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
* Explore more [Google Cloud for financial service solutions.](https://cloud.google.com/solutions/financial-services#section-1)
* Read about HSBC Market Data use case
* Read about the ANZ use case -->
