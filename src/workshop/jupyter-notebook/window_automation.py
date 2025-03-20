from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
import time
import threading

def start_plcsim_gui():
    plcsim_base_dir = r"C:\Program Files (x86)\Siemens\Automation\PLCSIMADV\bin"
    Application().start(cmd_line=f"{plcsim_base_dir}/Siemens.Simatic.PlcSim.Advanced.UserInterface.exe",
                        work_dir=plcsim_base_dir)

def accept_generating_trial_license():
    try:
        app = Application(backend="uia").connect(title="Automation License Management - PLCSIM Advanced")
        app.Dialog.ListBox.type_keys("{HOME}{DOWN 2}{ENTER}")
    except ElementNotFoundError as e:
        print("trial license no window")

def accept_trial_license_for_instance():
    try:
        app = Application(backend="uia").connect(title="PLCSIM Advanced")
        app.Dialog.Button.click()
    except ElementNotFoundError as e:
        print("no trial window")

def accept_all_python_openess_calls():
    try:
        app = Application(backend="win32").connect(path="Siemens.Automation.Portal.exe")
        dlg = app.window(title_re=r"Openness access.*")
        dlg.child_window(auto_id="YestoallButton").click()
    except ElementNotFoundError as e:
        print("no tia openess window to accept call from python")

class WindowCloser(threading.Thread):

    def __init__(self, closing_function, sleep_time = 0.1):
        super(WindowCloser, self).__init__()
        self.closing_function = closing_function
        self._stop_event = threading.Event()
        self.sleep_time = sleep_time

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while True:
            self.closing_function()
            time.sleep(self.sleep_time)
            if self.stopped():
                break


class InstanceWindowCloser(WindowCloser):
    def __init__(self, sleep_time = 0.1):
        super(InstanceWindowCloser, self).__init__(accept_trial_license_for_instance, sleep_time)


class LicenseGeneratorWindowCloser(WindowCloser):
    def __init__(self, sleep_time = 0.1):
        super(LicenseGeneratorWindowCloser, self).__init__(accept_generating_trial_license, sleep_time)


class TiaOpenessPythonCallWindowCloser(WindowCloser):
    def __init__(self, sleep_time = 0.1):
        super(TiaOpenessPythonCallWindowCloser, self).__init__(accept_all_python_openess_calls, sleep_time)