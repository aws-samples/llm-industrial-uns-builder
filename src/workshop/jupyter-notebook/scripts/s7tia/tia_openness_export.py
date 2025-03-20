import clr
from pathlib import Path
tia_portal_version = "V19"
tia_base_path = Path(r"C:\Program Files\Siemens\Automation", f"Portal {tia_portal_version}")
clr.AddReference(str(tia_base_path.joinpath("Bin\\PublicAPI\\Siemens.Engineering.Contract.dll")))
clr.AddReference(str(tia_base_path.joinpath(f"PublicAPI\\{tia_portal_version}\\Siemens.Engineering.dll")))

from System.IO import DirectoryInfo, FileInfo # type: ignore
import Siemens.Engineering as tia # type: ignore
import Siemens.Engineering.HW.Features as hwf # type: ignore
from Siemens.Engineering.Cax import CaxProvider # type: ignore
from Siemens.Engineering import EngineeringTargetInvocationException # type: ignore


def get_first_project_of_running_process():
    processes = tia.TiaPortal.GetProcesses()
    process = processes[0]
    mytia = process.Attach()
    return mytia.Projects[0]


def export_automationml(base_dir:Path, project):
    automationml_xml_file = base_dir.joinpath("project_automationml.aml")
    automationml_xml_file.parents[0].mkdir(parents=True, exist_ok=True)
    cax = project.GetService[CaxProvider]()
    cax.Export(project, FileInfo(str(automationml_xml_file)))


def export_block(base_dir:Path, block):
    print(f"try exporting block '{block.Name}'")
    file_path = base_dir.joinpath(f"{block.Name}.xml")
    file_path.parents[0].mkdir(parents=True, exist_ok=True)
    try:
        block.Export(FileInfo(str(file_path)), tia.ExportOptions.WithReadOnly)
    except EngineeringTargetInvocationException as ie:
        print(ie.Message)

    except Exception as e:
        print(type(e))
        print(e)


def export_blocks(base_dir:Path, block_group):
    for block in block_group.Blocks:
        export_block(base_dir, block)


def export_groups_and_blocks(base_dir:Path, parent):
    for group in parent.Groups:
        print(f"export group '{group.Name}'")
        group_path = base_dir.joinpath(group.Name)
        export_groups_and_blocks(group_path, group)
    try:
        export_blocks(base_dir, parent) #.BlockGroup)
    except AttributeError as e:
        print(parent)
        print(dir(parent))



def export_all_groups_and_blocks_from_all_plcs(export_dir, project):
    for plc in project.Devices:
        if plc.TypeIdentifier == 'System:Device.S71500':
            print(plc.Name)
            plc_device = plc.DeviceItems[1]
            software_container = tia.IEngineeringServiceProvider(plc_device).GetService[hwf.SoftwareContainer]()
            software_base = software_container.Software
            print(software_base.BlockGroup)
            plc_base_export_dir = export_dir.joinpath(plc.Name)
            export_groups_and_blocks(plc_base_export_dir, software_base.BlockGroup)