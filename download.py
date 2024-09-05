import requests
import json
import re

class ERCOTMatrixDownloaderParser:
    def __init__(self):
        self.report_list_url = "https://www.ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId=12363"
        self.download_url_template = "https://www.ercot.com/misdownload/servlets/mirDownload?doclookupId="
        self.file_path = None

    def download_matrix(self):
        # Step 1: Fetch the report list
        response = requests.get(self.report_list_url)

        # Check if the response is JSON formatted
        try:
            report_list = response.json()
        except json.JSONDecodeError:
            raise Exception("Failed to decode JSON response")

        # Step 2: Access the document list
        document_list = report_list.get('ListDocsByRptTypeRes', {}).get('DocumentList', [])
        if not document_list:
            raise Exception("No documents found in the response")

        # Step 3: Find the most recent .docx file
        latest_report = None
        for report in document_list:
            document = report.get('Document', {})
            if document.get('Extension') == 'docx':
                latest_report = document
                break

        if not latest_report:
            raise Exception("Docx download link not found")

        # Step 4: Construct the download URL
        doclookup_id = latest_report['DocID']
        download_url = f"{self.download_url_template}{doclookup_id}"

        # Step 5: Download the file
        response = requests.get(download_url)
        self.file_path = latest_report['ConstructedName']
        with open(self.file_path, 'wb') as f:
            f.write(response.content)

        print(f"Downloaded: {self.file_path}")


# Usage
if __name__ == "__main__":
    parser = ERCOTMatrixDownloaderParser()

    try:
        parser.download_matrix()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
