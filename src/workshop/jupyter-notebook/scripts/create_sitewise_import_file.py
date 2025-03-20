from pathlib import Path
from s7tia import automationml2sw
from sitewise import s7tia2sitewise

if __name__ == '__main__':
    project_name = "CarFactory"
    tia_export_dir = Path("C://Users//Administrator//Documents//TIA-Export")
    Path("../imports/sitewise").mkdir(parents=True, exist_ok=True)
    sw_output_bulk_file = Path("../imports/sitewise", f"{project_name}.sitewise.json")
    top_hierarchy_asset_name = "Plant_LAS"

    devices = automationml2sw.get_device_and_db_info(tia_export_dir)
    sw_bulk_import = s7tia2sitewise.add_or_create_to_sw_import(devices, project_name, top_hierarchy_asset_name)
    sw_bulk_import.write_to_file(sw_output_bulk_file)
