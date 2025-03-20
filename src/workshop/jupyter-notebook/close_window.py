import sys
import ctypes
import time
import threading

EnumWindows = ctypes.windll.user32.EnumWindows
EnumChildWindows = ctypes.windll.user32.EnumChildWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
GetClassName = ctypes.windll.user32.GetClassNameW
PostMessage = ctypes.windll.user32.PostMessageW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible
SendMessage = ctypes.windll.user32.SendMessageW


def getWindowText(hwnd):
    length = GetWindowTextLength(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    GetWindowText(hwnd, buffer, length + 1)
    return buffer.value


def getWindowClass(hwnd):
    buffer = ctypes.create_unicode_buffer(257)
    GetClassName(hwnd, buffer, 258)
    return buffer.value


def match(title, text, exactMatch):
    match = False
    if exactMatch:
        if text == title:
            match = True
    else:
        if 0 < title.find(text):
            match = True
    return match


def search(text, exactMatch, parentHwnd=None, matchOnClassName=False):
    resultHwnd = []

    def enumProc(hwnd, lParam, text=text, exactMatch=exactMatch, resultHwnd=resultHwnd):
        title = None
        if matchOnClassName:
            title = getWindowClass(hwnd)
            print(f"found class {title}")
        else:
            title = getWindowText(hwnd)

        if match(title, text, exactMatch):
            resultHwnd.append(hwnd)
            return False

        return True

    if None == parentHwnd:
        EnumWindows(EnumWindowsProc(enumProc), 0)
        return resultHwnd
    else:
        EnumChildWindows(parentHwnd, EnumWindowsProc(enumProc), 0)
        return resultHwnd


def clickButtonByHwnd(buttonHwnd):
    SendMessage(buttonHwnd, 0x00F5, 0, 0)  # 0x00F5 - BM_CLICK


def clickListByHwnd(buttonHwnd):
    SendMessage(buttonHwnd, 0x186, 0, 0)  # 0x00F5 - BM_CLICK


def clickList2ByHwnd(buttonHwnd):
    SendMessage(buttonHwnd, 0x185, 0, 0)  # 0x00F5 - BM_CLICK


def clickLis32ByHwnd(buttonHwnd):
    SendMessage(buttonHwnd, 0x014E, 0, 0)  # 0x00F5 - BM_CLICK


def updateWindowByHwnd(buttonHwnd):
    SendMessage(buttonHwnd, 0x0111, 0, 0)  # 0x0111 - WM_COMMAND


def dbClickByHwnd(buttonHwnd):
    SendMessage(buttonHwnd, 0x0203, 0, 0)  # 0x0203 - WM_LBUTTONDBLCLK


def searchButton(windowTitle, buttonText):
    exactMatch = True
    for hwnd in search(windowTitle, exactMatch):
        for buttonHwnd in search(buttonText, exactMatch, hwnd):
            return buttonHwnd
    return None


def searchListInWindowByClass(windowTitle, buttonClass):
    exactMatch = True
    for hwnd in search(windowTitle, exactMatch):
        print('found window title')
        for listHwnd in search(buttonClass, exactMatch, hwnd, True):
            return listHwnd
    return None


# interval - in terms of second
def timeIntervalCall(fn, interval):
    import time
    while True:
        fn()
        time.sleep(interval)


def clickButton(windowTitle, buttonText):
    print('attempt to find button...')
    buttonHwnd = searchButton(windowTitle, buttonText)
    if None != buttonHwnd:
        print('found')
        clickButtonByHwnd(buttonHwnd)
    else:
        print('not found')


def clickListEntry(windowTitle):
    print('attempt to find button...')
    listHwnd = searchListInWindowByClass(windowTitle, "ListBox")
    if None != listHwnd:
        print('list entry found')
        clickListByHwnd(listHwnd)
        clickList2ByHwnd(listHwnd)
        clickButtonByHwnd(listHwnd)
        clickLis32ByHwnd(listHwnd)
        updateWindowByHwnd(listHwnd)
        dbClickByHwnd(listHwnd)
        # send update window
        for parentHwnd in search(windowTitle, True):
            updateWindowByHwnd(parentHwnd)
    else:
        print('list entry not found')


def close_existing_plcsim_window():
    buttonHwnd = searchButton('PLCSIM Advanced', 'OK')
    if buttonHwnd:
        clickButtonByHwnd(buttonHwnd)


def close_existing_plcsim_activate_window():
    buttonHwnd = searchButton('Automation License Management - PLCSIM Advanced', 'Activate  ')
    if buttonHwnd:
        clickButtonByHwnd(buttonHwnd)


class WindowCloser(threading.Thread):

    def __init__(self, sleep_time = 0.1):
        self.keep_running = True
        self.sleep_time = sleep_time

    def stop(self):
        self.keep_running = False

    def run(self):
        while self.keep_running:
            close_existing_plcsim_window()
            time.sleep(self.sleep_time)


if __name__ == '__main__':
    windowTitle = 'Automation License Management - PLCSIM Advanced'
    buttonText = 'OK'
    interval = 1

    print('title : %s' % windowTitle)
    print('button text : %s' % buttonText)
    print('time interval : %s' % interval)

    #timeIntervalCall(lambda: clickButton(windowTitle, buttonText), interval)
    timeIntervalCall(lambda: clickListEntry(windowTitle), interval)
