import pandas as pd
import json
from sklearn.impute import SimpleImputer
from sklearn.cluster import KMeans
import chardet
import chardet
import os
import time
from rich.progress import track
import sys
import requests
import seaborn as sns
import matplotlib.pyplot as plt

#os.environ['OMP_NUM_THREADS'] = '11'



# Run Rich for extra effects
for i in track(range(20), description="Fetching Results:"):
    if i < 19:
        time.sleep(0.05)
    else:
        time.sleep(3)


# Ensure the correct number of arguments are passed.
if len(sys.argv) < 2:
    print("Please provide the dataset file!")
    sys.exit(1)
csv_file = sys.argv[1]

#Just incase the Teaching assistant does not upload the file
try:
    with open(csv_file, 'rb') as f:
        encoded = chardet.detect(f.read())
    data = pd.read_csv(csv_file,encoding=encoded['encoding'])
except FileNotFoundError:
    print(f"Your file {csv_file} might be entered wrong or Your file {csv_file} is not in not found")
    sys.exit(1)

#-------------------------------
#Generic analysis
#-------------------------------

def analyze_data(data):
    analysis_results = {}

    # 1. Summary Statistics
    analysis_results['Summary Statistics'] = data.describe(include='all').to_dict()

    # 2. Missing Values
    missing_values = data.isnull().sum().to_dict()
    analysis_results['Missing Values'] = missing_values

    # 3. Correlation Matrix
    numerical_data = data.select_dtypes(include=['number'])
    correlation_matrix = numerical_data.corr().to_dict()
    analysis_results['Correlation Matrix'] = correlation_matrix

    # 4. Outliers
    numerical_data = data.select_dtypes(include=['number'])
    Q1 = numerical_data.quantile(0.25)
    Q3 = numerical_data.quantile(0.75)
    IQR = Q3 - Q1
    outliers = ((numerical_data < (Q1 - 1.5 * IQR)) | (numerical_data > (Q3 + 1.5 * IQR))).sum().to_dict()
    analysis_results['Outliers'] = outliers

    # 5. Clustering
    imputer = SimpleImputer(strategy='mean')
    numerical_data_imputed = imputer.fit_transform(numerical_data)

    kmeans = KMeans(n_clusters=3, random_state=42)
    data['Cluster'] = kmeans.fit_predict(numerical_data_imputed)
    cluster_counts = data['Cluster'].value_counts().to_dict()
    analysis_results['Clustering'] = cluster_counts

    return analysis_results
to_send = json.dumps(analyze_data(data))


#------------------------------------
#LLM summary on our generic statistics.
#------------------------------------

api_key = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIxZjMwMDIwODhAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.PEbfx_SD3tGSDZdoMCpQvm1s7xjH_OQ7_06EAVhc8LQ"
url = f"https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
output_md_file = "README.md"

request_text = """
This is the JSON file for the summary statistics. Do some generic analysis. Give output in markdown file format. 

Here are some ideas for analysis that may be insightful. Some of these are covered in this course, but don't limit yourself.

Outlier and Anomaly Detection: You might find errors, fraud, or high-impact opportunities.
Correlation Analysis, Regression Analysis, and Feature Importance Analysis: You might find what to improve to impact an outcome.
Time Series Analysis: You might find patterns that help predict the future.
Cluster Analysis: You might find natural groupings for targeted marketing or resource allocation.
Geographic Analysis: You might find where the biggest problems or opportunities are.
Network Analysis: You might find what to cross-sell or collaborate with.

Select whichever analysis is appropriate depending on the columns.
"""

try:
    # Read the JSON file
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an advanced data analyst."},
            {"role": "user", "content": f"{request_text}\n\n{to_send}"}
        ],
        "max_tokens": 750,
        "temperature": 0.3
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Send the POST request
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        # Save the response content as a Markdown file
        response_content = response.json()["choices"][0]["message"]["content"]
        with open(output_md_file, "w", encoding="utf-8") as md_file:
            md_file.write(response_content)
        print(f"Analysis saved to '{output_md_file}'.")
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")
except Exception as e:
    print(f"An error occurred: {e}")
