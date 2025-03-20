from pathlib import Path
from .tia_automationml_helper import automationml_export_to_entries
from .tia_block_helper import tia_db_export_to_entries


def get_devices_and_db_names(project_export_dir, automation_ml_file_name="project_automationml.aml"):
    devices = automationml_export_to_entries(
        str(Path(project_export_dir, automation_ml_file_name)))

    for device_name, device in devices.items():
        print(f"load DB for PLC {device_name}")
        plc_base_dir = Path(project_export_dir, device_name)
        db_export_files = [f for f in plc_base_dir.iterdir() if f.is_file()]
        device['db_files'] = db_export_files
        print(db_export_files)
    return devices


def get_device_and_db_info(project_export_dir, automation_ml_file_name="project_automationml.aml"):
    devices = automationml_export_to_entries(
        str(Path(project_export_dir, automation_ml_file_name)))

    for device_name, device in devices.items():
        print(f"load DB for PLC {device_name}")
        plc_base_dir = Path(project_export_dir, device_name)
        db_export_files = [f for f in plc_base_dir.iterdir() if f.is_file()]
        print(db_export_files)
        device["entries"] = {}
        for db_export_file in db_export_files:
            if str(db_export_file).endswith("DB_SW.xml"):
                print(f"Loading {db_export_file}")
                db_entries = tia_db_export_to_entries(str(db_export_file))
                # TODO have the DB number also separate of the entries
                if db_entries and len(db_entries) > 0:
                    db_number = db_entries[0]["db_number"]
                    device["entries"][db_number] = db_entries
    return devices
