from pathlib import Path
from s7tia.tia_openness_export import *

if __name__ == '__main__':
    base_export_dir = Path(r"C://Users//Administrator//Documents//TIA-Export")

    project = get_first_project_of_running_process()
    export_automationml(base_export_dir, project)
    export_all_groups_and_blocks_from_all_plcs(base_export_dir, project)
