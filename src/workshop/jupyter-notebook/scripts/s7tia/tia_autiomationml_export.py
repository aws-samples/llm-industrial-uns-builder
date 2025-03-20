import clr
clr.AddReference('C:\\Program Files\\Siemens\\Automation\\Portal V19\\Bin\\PublicAPI\\Siemens.Engineering.Contract.dll')
clr.AddReference(r"C:\Program Files\Siemens\Automation\Portal V19\PublicAPI\V19\Siemens.Engineering.dll")

from System.IO import DirectoryInfo, FileInfo
import Siemens.Engineering as tia
from Siemens.Engineering.Cax import CaxProvider

processes = tia.TiaPortal.GetProcesses() # Making a list of all running processes
print (processes)
process = processes[0]                   # Just taking the first process as an example
mytia = process.Attach()
myproject = mytia.Projects[0]

base_export_dir = "C:\\Users\\Administrator\\Documents\\"
automationml_xml_file = f"{base_export_dir}stepanalysis.aml"

cax = myproject.GetService[CaxProvider]()
cax.Export(myproject, FileInfo(automationml_xml_file))