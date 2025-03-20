import clr
clr.AddReference('C:\\Program Files\\Siemens\\Automation\\Portal V19\\Bin\\PublicAPI\\Siemens.Engineering.Contract.dll')
clr.AddReference(r"C:\Program Files\Siemens\Automation\Portal V19\PublicAPI\V19\Siemens.Engineering.dll")

from System.IO import DirectoryInfo, FileInfo
import Siemens.Engineering as tia
import Siemens.Engineering.HW.Features as hwf

processes = tia.TiaPortal.GetProcesses()
print (processes)
process = processes[0]
mytia = process.Attach()
myproject = mytia.Projects[0]

base_export_dir = "C:\\Users\\Administrator\\Documents\\TIA-Export\\StepTimeAnalysis\\"
db13_xml_file = f"{base_export_dir}DB13.xml"

PLC1 = myproject.Devices[0]

for plc in myproject.Devices:
    if plc.TypeIdentifier == 'System:Device.S71500':
        print(plc.Name)
        plc_device = plc.DeviceItems[1]
        software_container = tia.IEngineeringServiceProvider(plc_device).GetService[hwf.SoftwareContainer]()
        software_base = software_container.Software
        for block in software_base.BlockGroup.Blocks:
            print(f"try exporting block {block.Name}")
            try:
                block.Export(FileInfo(f"{base_export_dir}{plc_device.Name}_{block.Name}.xml"), tia.ExportOptions.WithReadOnly)
            except Exception as e:
                print(e)

        # plc_block = software_base.BlockGroup.Blocks.Find("DB13")
        # plc_block.Export(FileInfo(db13_xml_file), tia.ExportOptions.WithReadOnly)
        # for block in software_base.BlockGroup.Blocks:
        #     print(block.Name)
