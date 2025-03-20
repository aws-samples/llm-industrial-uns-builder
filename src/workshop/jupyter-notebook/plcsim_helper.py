import winreg
from pathlib import Path
import clr
from ec2_metadata import ec2_metadata
import re
import time
from threading import Thread
import shutil

Version = "6.0"
InstalledSWKeyFolder = "SOFTWARE\\WOW6432Node\\Siemens\\Automation\\_InstalledSW\\PLCSIMADV\\Global"
InstalledSWPathKey = "Path"
LibraryKeyFolder = "SOFTWARE\\Wow6432Node\\Siemens\\Shared Tools\\PLCSIMADV_SimRT"
LibraryPathKey = "Path"
ApiFolder = "API"
LibraryName = "Siemens.Simatic.Simulation.Runtime.Api.x64"
LibraryFileName = "Siemens.Simatic.Simulation.Runtime.Api.x64.dll"


def load_plcsim_library() -> None:
    clr.AddReference(str(get_library_file_path()))


def IsInstalled() -> bool:
    return get_library_file_path().exists()


def get_library_file_path() -> Path:
    library_file_path = get_api_path().joinpath(Path(LibraryFileName))
    return library_file_path if library_file_path.is_file() else None


def get_api_path() -> Path:
    registryKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, LibraryKeyFolder)
    sharedPath = Path(winreg.QueryValueEx(registryKey, LibraryPathKey)[0])
    apiDirectory = sharedPath.joinpath(Path(ApiFolder), Path(Version))
    return apiDirectory if apiDirectory.is_dir() else None


def get_installation_path() -> Path:
    registryKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, InstalledSWKeyFolder)
    installationPath = Path(winreg.QueryValueEx(registryKey, InstalledSWPathKey)[0])
    return installationPath if installationPath.is_dir() else None


def open_port_for_remote_connections(port=4444) -> None:
    from Siemens.Simatic.Simulation.Runtime import SimulationRuntimeManager
    SimulationRuntimeManager.OpenPort(port)


def map_network_interfaces(plcsim_net_interfaces) -> dict:
    ec2_net_iface_to_plcsim_mapping = {}
    for mac, ec2_network_interface in ec2_metadata.network_interfaces.items():
        plcsim_mac = mac.replace(':', '-')
        ec2_net_iface_to_plcsim_mapping[plcsim_mac] = {
            "mac": plcsim_mac,
            "private_ipv4": ec2_network_interface.private_ipv4s,
            "interface_index": None
        }
    # map plcsim interface index
    for net_interface in plcsim_net_interfaces:
        mapping = ec2_net_iface_to_plcsim_mapping.get(net_interface.MACAddress.MACString, None)
        if mapping:
            mapping["interface_index"] = net_interface.interfaceIndex
    # map ip address, netmask and gateway with C# api
    from System.Net.NetworkInformation import NetworkInterface
    from System.Net.Sockets import AddressFamily
    for net_interface in NetworkInterface.GetAllNetworkInterfaces():
        mac_address = re.sub(r'(.{2})(?!$)', r'\1-', net_interface.GetPhysicalAddress().ToString())
        mapping = ec2_net_iface_to_plcsim_mapping.get(mac_address.lower(), None)
        if mapping:
            mapping["default_gw"] = net_interface.GetIPProperties().GatewayAddresses[0].Address.ToString()
            for address in net_interface.GetIPProperties().UnicastAddresses:
                if address.Address.AddressFamily == AddressFamily.InterNetwork:
                    mapping["netmask"] = address.IPv4Mask.ToString()
    return ec2_net_iface_to_plcsim_mapping


def create_plcs() -> None:
    from Siemens.Simatic.Simulation.Runtime import SimulationRuntimeManager, ENetworkMode, ECPUType, SIPSuite4, SIP, \
        SimulationRuntimeException, EPLCInterface, ECommunicationInterface, EOperatingState
    # connect to the plcsim simulation manager
    sm = SimulationRuntimeManager
    # ensure we use the tcp multi adapater mode to map the plc interfaces to ec2 network interfaces
    sm.NetworkMode = ENetworkMode.TCPIPMultipleAdapter
    # check if we have a function to cose a popup window
    try:
        import window_automation
    except ImportError or ModuleNotFoundError:
        window_automation = None
    for interface_detail in map_network_interfaces(sm.NetInterfaces).values():
        # start a background thread that can close the trial license genertion window if it appears the first time.
        license_closer = None
        if window_automation:
            license_closer = window_automation.LicenseGeneratorWindowCloser(0.5)
            license_closer_event = license_closer._stop_event
            license_closer.daemon = True
            license_closer.start()
        # create only plcs where a second ip address is attached to the network interface
        if len(interface_detail["private_ipv4"]) > 1:
            second_ip_address = interface_detail["private_ipv4"][1]
            # for now lets create  ageneric S7 1500
            plcType = ECPUType.CPU1500_Unspecified
            # create plc instance
            i = sm.RegisterInstance(plcType, f"PLC_{second_ip_address}")
            # map the first network interface of the plc to the ec2 network interface
            i.SetNetInterfaceMapping(EPLCInterface.IE1, interface_detail["interface_index"])
            # tell the simulation manager to bind the network interface
            sm.SetNetInterfaceBindings()
            # power the plc on in oder to set the ip address
            # keep in mind if there's just a trial license this will trigger a popup with a warning
            # try closing the popup automatically in a background thread
            closer = None
            if window_automation:
                closer = window_automation.InstanceWindowCloser(0.5)
                closer.daemon = True
                closer.start()
            i.PowerOn()
            # poweron returned - so the popup is gone - remove closer thread
            if window_automation:
                if closer:
                    closer.stop()
                    closer.join()
                if license_closer:
                    license_closer_event.set()
                    license_closer.stop()
                    license_closer.join()
            # wait until the plc has reached the stop status
            while i.OperatingState != EOperatingState.Stop:
                time.sleep(0.1)
            # add the ip address to the first plc network interface
            plc_interface_id = 0
            # ip suite from ec2 network interface
            sip = SIPSuite4(second_ip_address, interface_detail["netmask"], interface_detail["default_gw"])
            # keep network settings even after reboot
            remanent_ip_mapping = True
            i.SetIPSuite(plc_interface_id, sip, remanent_ip_mapping)


def archive_all_plcs() -> None:
    from Siemens.Simatic.Simulation.Runtime import SimulationRuntimeManager, EOperatingState
    # connect to the plcsim simulation manager
    sm = SimulationRuntimeManager
    for plc_info in sm.RegisteredInstanceInfo:
        i = sm.CreateInterface(plc_info.Name)
        if i.OperatingState == EOperatingState.Off:
            print(f"archive {plc_info.Name}")
            i.ArchiveStorage(f"C:\\Users\\Administrator\\Documents\\PLC_Archive\\{plc_info.Name}.zip")
        else:
            print(f"cannot archive {plc_info.Name} as it is not stopped")

def retrieve_all_plcs() -> None:
    from Siemens.Simatic.Simulation.Runtime import SimulationRuntimeManager, EOperatingState
    # connect to the plcsim simulation manager
    sm = SimulationRuntimeManager
    for plc_info in sm.RegisteredInstanceInfo:
        i = sm.CreateInterface(plc_info.Name)
        if i.OperatingState == EOperatingState.Off:
            print(f"retrieving {plc_info.Name}")
            i.RetrieveStorage(f"C:\\Users\\Administrator\\Documents\\PLC_Archive\\{plc_info.Name}.zip")
        else:
            print(f"cannot retrieve {plc_info.Name} as it is not stopped")


def power_off_all_plcs() -> None:
    from Siemens.Simatic.Simulation.Runtime import SimulationRuntimeManager, EOperatingState
    # connect to the plcsim simulation manager
    sm = SimulationRuntimeManager
    for plc_info in sm.RegisteredInstanceInfo:
        print(f"power off {plc_info.Name}")
        i = sm.CreateInterface(plc_info.Name)
        if i.OperatingState != EOperatingState.Off:
            i.PowerOff()

def set_up_all_plcs() -> None:
    from Siemens.Simatic.Simulation.Runtime import SimulationRuntimeManager, EOperatingState
    print("01 Starting PLCs set-up process")
    create_plcs()
    time.sleep(2)
    print("02 Initializing PLCs....")
    # connect to the plcsim simulation manager
    sm = SimulationRuntimeManager
    for plc_info in sm.RegisteredInstanceInfo:
        i = sm.CreateInterface(plc_info.Name)
        if i.OperatingState != EOperatingState.Off:
            i.PowerOff()
    time.sleep(2)
    print("03 Loading PLCs with HW and SW Configuration")
    for plc_info in sm.RegisteredInstanceInfo:
        i = sm.CreateInterface(plc_info.Name)
        if i.OperatingState == EOperatingState.Off:
            i.RetrieveStorage(f"C:\\Users\\Administrator\\Documents\\PLC_Archive\\{plc_info.Name}.zip")
        else:
            print(f"cannot archive {plc_info.Name} as it is not stopped")
    time.sleep(2)
    print("04 Finishing PLCSims Configuration and set-up")
    for plc_info in sm.RegisteredInstanceInfo:
        i = sm.CreateInterface(plc_info.Name)
        i.UnregisterInstance()
    time.sleep(2)
    create_plcs()
    print("05 PLCSim set-up successfully completed")


def delete_all_plcs(delete_storate=True) -> None:
    from Siemens.Simatic.Simulation.Runtime import SimulationRuntimeManager, EOperatingState
    # connect to the plcsim simulation manager
    sm = SimulationRuntimeManager
    for plc_info in sm.RegisteredInstanceInfo:
        print(f"delete {plc_info.Name}")
        i = sm.CreateInterface(plc_info.Name)
        storage_path = i.StoragePath
        i.UnregisterInstance()
        if delete_storate:
            print(f"delete storage path for {plc_info.Name} '{storage_path}'")
            shutil.rmtree(storage_path, ignore_errors=True)

def check_all_plcs() -> None:
    from Siemens.Simatic.Simulation.Runtime import SimulationRuntimeManager, EOperatingState
    # connect to the plcsim simulation manager
    count = 0
    sm = SimulationRuntimeManager
    for plc_info in sm.RegisteredInstanceInfo:
        i = sm.CreateInterface(plc_info.Name)
        if i.OperatingState == EOperatingState.Run:
            print(f"\tSimulated PLC {plc_info.Name} detected")
            count += 1 
        else:
            print(f"\tSimulated PLC {plc_info.Name} available but inactive")
    print(f"\n{count} Simulated PLC instances available and active")

class PLCSIMManager:
    class SimulatedPLC:
        def __init__(self, simulation_instance):
            self.simulation_instance = simulation_instance
            self.name = self.simulation_instance.Name

        def get_ip_addresses(self) -> [str]:
            ip_addresses = []
            for net_interface in self.simulation_instance.ControllerIPSuite4:
                ip_addresses.append(net_interface.IPAddress.IPString)
            return ip_addresses

        def power_on(self, timeout=10000) -> None:
            self.simulation_instance.PowerOn(timeout)

        def delete(self) -> None:
            self.simulation_instance.UnregisterInstance()

    def __init__(self, remote_connection_string=None) -> None:
        load_plcsim_library()
        from Siemens.Simatic.Simulation.Runtime import SimulationRuntimeManager, ENetworkMode, ECPUType, SIPSuite4, SIP, \
            SimulationRuntimeException
        if remote_connection_string:
            self.simulation_manager = SimulationRuntimeManager.RemoteConnect(remote_connection_string)
        else:
            self.simulation_manager = SimulationRuntimeManager
        self.simulation_manager.NetworkMode = ENetworkMode.TCPIPMultipleAdapter
        self.plcs: dict[PLCSIMManager.SimulatedPLC] = {}
        self._load_plc_instances()

    def delete_all_instances(self) -> None:
        for plc_name, plc in self.plcs.items():
            plc.delete()
        self.plcs: dict[PLCSIMManager.SimulatedPLC] = {}

    def create_plc_instance(self, name: str, ip_address: str, netmask: str, default_gw: str) -> SimulatedPLC:
        from Siemens.Simatic.Simulation.Runtime import ECPUType, SIPSuite4
        plcType = ECPUType.CPU1500_Unspecified
        simulation_instance = self.simulation_manager.RegisterInstance(plcType, name)
        self.plcs[name] = PLCSIMManager.SimulatedPLC(simulation_instance)
        self.plcs[name].power_on()
        interface_id = 0
        sip = SIPSuite4(ip_address, netmask, default_gw)
        is_remanent = True
        self.plcs[name].simulation_instance.SetIPSuite(interface_id, sip, is_remanent)


    def get_ec2_net_to_plcsim_mapping(self) -> dict:
        ec2_net_iface_to_plcsim_mapping = {}
        for mac, ec2_network_interface in ec2_metadata.network_interfaces.items():
            plcsim_mac = mac.replace(':', '-')
            ec2_net_iface_to_plcsim_mapping[plcsim_mac] = {
                "mac": plcsim_mac,
                "private_ipv4": ec2_network_interface.private_ipv4s,
                "interface_index": None
            }
        for net_interface in self.simulation_manager.NetInterfaces:
            mapping = ec2_net_iface_to_plcsim_mapping.get(net_interface.MACAddress.MACString, None)
            if mapping:
                mapping["interface_index"] = net_interface.interfaceIndex

        return ec2_net_iface_to_plcsim_mapping

    def _load_plc_instances(self) -> None:
        self.plcs: dict[PLCSIMManager.SimulatedPLC] = {}
        for plc_info in self.simulation_manager.RegisteredInstanceInfo:
            simulation_instance = self.simulation_manager.CreateInterface(plc_info.Name)
            self.plcs[plc_info.Name] = PLCSIMManager.SimulatedPLC(simulation_instance)
