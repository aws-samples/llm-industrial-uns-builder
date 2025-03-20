import clr
from pathlib import Path
import time
tia_portal_version = "V19"
tia_base_path = Path(r"C:\Program Files\Siemens\Automation", f"Portal {tia_portal_version}")
clr.AddReference(str(tia_base_path.joinpath("Bin\\PublicAPI\\Siemens.Engineering.Contract.dll")))
clr.AddReference(str(tia_base_path.joinpath(f"PublicAPI\\{tia_portal_version}\\Siemens.Engineering.dll")))
import Siemens.Engineering as tia # type: ignore
from Siemens.Engineering.HW import View # type: ignore
from System.IO import DirectoryInfo, FileInfo # type: ignore
from pywinauto import Application, Desktop
from pywinauto.findwindows import ElementNotFoundError
import window_automation

# TIA Portal project file location
project_path_string_wo_extension = \
    r"C:\Users\Administrator\Documents\Automation\reInventAutoWorkshop_V19\reInventAutoWorkshop_V19"
project_path_string_with_extension = project_path_string_wo_extension+".ap19"
project_path = FileInfo(project_path_string_with_extension)

# we need that python is allowed to call tia openness while opening tia
tia_python_accept_closer = window_automation.TiaOpenessPythonCallWindowCloser(0)
tia_python_accept_closer_event = tia_python_accept_closer._stop_event
tia_python_accept_closer.daemon = True
tia_python_accept_closer.start()
# for reference: this is what the thread is doing while tia is opening
# app = Application(backend="win32").connect(path="Siemens.Automation.Portal.exe")
# dlg = app.window(title_re=r"Openness access.*")
# dlg.child_window(auto_id="YestoallButton").click()

print("Starting TIA with UI")
try:
    # call openess to start the tia gui with a project
    mytia = tia.TiaPortal(tia.TiaPortalMode.WithUserInterface)
    myproject = mytia.Projects.Open(project_path)
    myproject.ShowHwEditor(View.Device)

    # as tia is open we can stop the window accepter
    tia_python_accept_closer_event.set()
    tia_python_accept_closer.stop()
    tia_python_accept_closer.join()

    # let's sleep for 30s to get everything loaded
    print("wait 30s for TIA to load")
    time.sleep(30)

    # connect to TIA via the win32 api to click through the rest
    #app = Application(backend="win32").connect(path="Siemens.Automation.Portal.exe")
    app = Application(backend="win32").connect(title=f"Siemens  -  {project_path_string_wo_extension}")

    # get project tree
    tree = app.top_window().child_window(auto_id="ProjectNavigationTree")
    # click the first item in the project tree (add device)
    tree.click_input(coords=(tree.rectangle().left + 30, tree.rectangle().top + 30), button="left", absolute=True,
                     double=True)
    # wait for catalog to open
    time.sleep(3)
    # get catalog tree
    catalog_tree = app.top_window().child_window(auto_id="m_CatalogTree")
    # from here on we need to click by pixel
    # click S7-1500
    catalog_tree.click_input(coords=(catalog_tree.rectangle().left + 40, catalog_tree.rectangle().top + 40),
                             button="left", absolute=True, double=True)
    # wait for catalog to unfold
    time.sleep(3)
    # click CPU
    catalog_tree.click_input(coords=(catalog_tree.rectangle().left + 60, catalog_tree.rectangle().top + 60),
                             button="left", absolute=True, double=True)
    # wait for catalog to unfold
    time.sleep(3)
    # click first CPU
    catalog_tree.click_input(coords=(catalog_tree.rectangle().left + 70, catalog_tree.rectangle().top + 70),
                             button="left", absolute=True, double=True)
    # wait for catalog to unfold
    time.sleep(3)

    # if there's no TIA license a license window pops up
    try:
        app.top_window().child_window(title="Automation License Management - S7PRO1-1500").exists()
        tia_license_window = Application(backend="win32").connect(title="Automation License Management - S7PRO1-1500")
        tia_license_window.Dialog.ListBox.select("STEP 7 Professional")
        tia_license_window.Dialog.Activate.click()
    except ElementNotFoundError as e:
        print("tia has already a license")

    # close catalog
    catalog_cancel = app.top_window().child_window(auto_id="m_ButtonCancel")
    catalog_cancel.type_keys("{HOME}{DOWN 2}{ENTER}")

except Exception as e:
    print (e)
