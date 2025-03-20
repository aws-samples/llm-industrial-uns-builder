import os
import argparse
import urllib3
from urllib.parse import urljoin

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def download_file(url, file_path):
    http = urllib3.PoolManager()
    with http.request('GET', url, preload_content=False) as resp, open(file_path, 'wb') as out_file:
        while True:
            data = resp.read(1024)
            if not data:
                break
            out_file.write(data)
    print(f"Downloaded: {file_path}")


def main():
    parser = argparse.ArgumentParser(description="File downloader script")
    parser.add_argument("--force", action="store_true", help="Force download even if file exists")
    args = parser.parse_args()

    base_url = "https://ws-assets-prod-iad-r-pdx-f3b3f9f1a7d6a3d0.s3.us-west-2.amazonaws.com/7919c848-eb70-4278-96ba-06fd1e038fb6/"

    file_list = [
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\plcsim_helper.py",
            "download_path": "jupyter-notebook/plcsim_helper.py"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\close_window.py",
            "download_path": "jupyter-notebook/close_window.py"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\window_automation.py",
            "download_path": "jupyter-notebook/window_automation.py"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\start_plcs.py",
            "download_path": "jupyter-notebook/start_plcs.py"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\scripts.zip",
            "download_path": "jupyter-notebook/scripts.zip"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\IntegratedAutomation.ipynb",
            "download_path": "jupyter-notebook/IntegratedAutomation.ipynb"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\Playground.ipynb",
            "download_path": "jupyter-notebook/IntegratedAutomation_Sitewise.ipynb"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\01_Siemens_PLCSim_TIAPortal.ipynb",
            "download_path": "jupyter-notebook/Notebooks/01_Siemens_PLCSim_TIAPortal.ipynb"
        }, 
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\02_Sitewise_Config_Bedrock.ipynb",
            "download_path": "jupyter-notebook/Notebooks/02_Sitewise_Config_Bedrock.ipynb"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\03_BulkImport_UNS_Sitewise.ipynb",
            "download_path": "jupyter-notebook/Notebooks/03_BulkImport_UNS_Sitewise.ipynb"
        }, 
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\sitewise_helpers.py",
            "download_path": "jupyter-notebook/sitewise_helpers.py"
        },               
        {
            "filename": r"C:\Users\Administrator\Documents\Automation\reInventAutoWorkshop_V19.zip",
            "download_path": "tiaproject/reInventAutoWorkshop_V19.zip"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\PLC_Archive.zip",
            "download_path": "PLCSims/PLC_Archive.zip"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\include_generated_swtarget.json",
            "download_path": "sitewiseSFCConfig/include_generated_swtarget.json"
        },
                {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\complete_asset_models_definition.json",
            "download_path": "sitewiseSFCConfig/complete_asset_models_definition.json"
        },
        {
            "filename": r"C:\Users\Administrator\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\start_plcs.bat",
            "download_path": "jupyter-notebook/start_plcs.bat"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\start_tia.py",
            "download_path": "jupyter-notebook/start_tia.py"
        },
        {
            "filename": r"C:\Users\Administrator\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\start_tia.bat",
            "download_path": "jupyter-notebook/start_tia.bat"
        },
        {
            "filename": r"C:\Users\Administrator\Desktop\start_plcs.bat",
            "download_path": "jupyter-notebook/start_plcs_desktop.bat"
        },
        {
            "filename": r"C:\Users\Administrator\Desktop\start_tia.bat",
            "download_path": "jupyter-notebook/start_tia_desktop.bat"
        },
        {
            "filename": r"C:\Users\Administrator\Documents\jupyter-notebook\LICENSE",
            "download_path": "jupyter-notebook/LICENSE"
        }
    ]

    for file_obj in file_list:
        file_path = file_obj["filename"]
        download_path = file_obj["download_path"]

        # Construct the full URL
        full_url = urljoin(base_url, download_path)

        if args.force or not os.path.exists(file_path):
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Download the file
                download_file(full_url, file_path)
            except Exception as e:
                print(f"Error downloading {file_path}: {str(e)}")
        else:
            print(f"File already exists: {file_path}")


if __name__ == "__main__":
    main()