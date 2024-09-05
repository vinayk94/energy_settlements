import os
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser  # Use dateutil.parser to handle timezone

class ERCOTMatrixDownloaderParser:
    def __init__(self, downloads_dir="downloads"):
        self.base_url = "https://www.ercot.com"
        self.report_list_url = "https://www.ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId="
        self.report_download_url = "https://www.ercot.com/misdownload/servlets/mirDownload?doclookupId="
        self.downloads_dir = downloads_dir
        self.last_published_file = os.path.join(self.downloads_dir, "last_published_date.txt")

        # Create downloads directory if it doesn't exist
        os.makedirs(self.downloads_dir, exist_ok=True)

        self.report_type_id = self.get_report_type_id()  # Dynamically fetch the ReportTypeID

    def get_report_type_id(self):
        """
        Scrapes the ERCOT page to dynamically extract the ReportTypeID.
        """
        response = requests.get(f"{self.base_url}/mp/data-products/data-product-details?id=NP9-605-M")
        soup = BeautifulSoup(response.text, 'html.parser')

        label = soup.find(string=re.compile("Report Type ID"))
        if label:
            report_type_id = label.find_next('span').get_text(strip=True)
            print(f"Found Report Type ID: {report_type_id}")
            return report_type_id

        # Fallback method: Look for any text that resembles Report Type ID in a wider search
        id_search = re.search(r"Report Type ID\s*:\s*(\d+)", soup.get_text())
        if id_search:
            report_type_id = id_search.group(1)
            print(f"Fallback method found Report Type ID: {report_type_id}")
            return report_type_id

        raise ValueError("Report Type ID not found")

    def compare_publish_date(self, publish_date_str):
        """
        Compares the publish date with the last saved publish date.
        """
        # Parse the publish date using dateutil.parser to handle the timezone format
        new_publish_date = parser.parse(publish_date_str)

        if os.path.exists(self.last_published_file):
            with open(self.last_published_file, "r") as f:
                last_publish_date = parser.parse(f.read().strip())
            
            if new_publish_date > last_publish_date:
                print("New document is available.")
                return True
            else:
                print("No new document available.")
                return False
        else:
            # No previous record, consider it as a new document
            return True

    def update_last_published_date(self, publish_date_str):
        """
        Updates the last_published_date.txt with the latest publish date.
        """
        with open(self.last_published_file, "w") as f:
            f.write(publish_date_str)

    def download_matrix(self, doc_id, file_name):
        """
        Downloads the settlement matrix document.
        """
        download_url = f"{self.report_download_url}{doc_id}"
        response = requests.get(download_url)

        file_path = os.path.join(self.downloads_dir, file_name)

        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {file_name}")

    def run(self):
        """
        Main logic to check for updates and download the latest document if necessary.
        """
        print(f"Using Report Type ID: {self.report_type_id}")
        response = requests.get(f"{self.report_list_url}{self.report_type_id}")
        data = response.json()

        try:
            document = data['ListDocsByRptTypeRes']['DocumentList'][0]['Document']
            publish_date_str = document['PublishDate']
            file_name = document['ConstructedName']
            doc_id = document['DocID']

            if self.compare_publish_date(publish_date_str):
                self.download_matrix(doc_id, file_name)
                self.update_last_published_date(publish_date_str)
            else:
                print("No new document to download.")

        except (KeyError, IndexError):
            print("An error occurred while processing the document list.")

if __name__ == "__main__":
    downloader = ERCOTMatrixDownloaderParser()
    downloader.run()
