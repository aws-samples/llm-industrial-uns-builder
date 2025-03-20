import untangle


def automationml_export_to_entries(automationml_file):
    doc = untangle.parse(automationml_file)
    devices = {}
    hierarchies = [hierarchy for hierarchy in doc.CAEXFile.children if hierarchy._name == 'InstanceHierarchy']
    for hierarchy in hierarchies:
        for project in hierarchy.children:
            assets = [ele for ele in project.children if ele._name == 'InternalElement']
            for asset in assets:
                # print(f"Asset Name {asset['Name']}")
                asset_attributes = [attr for attr in asset.children if attr._name == 'Attribute' and
                                    attr.get_attribute('Name') and attr.get_attribute('Name') == 'TypeIdentifier']
                asset_type = asset_attributes[0].Value.cdata if len(asset_attributes) > 0 else None
                if asset_type and asset_type.startswith('System:Device'):
                    # print(f"Asset Type: {asset_type}")
                    # for attr in asset.InternalElement.Attribute:
                    #     print(f"Attribute {attr['Name']} {attr.Value.cdata.strip()}")
                    plc_name = asset.InternalElement.InternalElement["Name"]
                    print(f"Plc Name: {plc_name}")
                    device = {"asset_name": plc_name}
                    for attr in asset.InternalElement.InternalElement.Attribute:
                        if attr['Name'] != 'PositionNumber' and attr['Name'] != 'BuiltIn':
                            # print(f"Attribute {attr['Name']} {attr.Value.cdata.strip()}")
                            device[attr['Name']] = attr.Value.cdata.strip()
                    
                    # TODO: fix PNIO-Interface naming in TIA Project...
                    profinet_interfaces = [ele for ele in asset.InternalElement.InternalElement.InternalElement
                                           if ele["Name"].startswith('PROFINET interface_1') or ele["Name"].startswith('PROFINET_Interface_1')]
                    for profinet_interface in profinet_interfaces:
                        # print(f"Profinet Interface: {profinet_interface['Name']}")
                        # for attr in profinet_interface.Attribute:
                        #     if attr['Name'] != 'PositionNumber' and attr['Name'] != 'BuiltIn':
                        #         print(f"Profinet Interface Attribute {attr['Name']} {attr.Value.cdata.strip()}")
                        ethernet_configs = [ele for ele in profinet_interface.InternalElement
                                            if ele["Name"].startswith('E') and not ele["Name"].startswith('Port')]
                        ethernet_config_number = 1
                        device_ethernet_configs = []
                        for ethernet_config in ethernet_configs:
                            device_ethernet_config = {}
                            for attr in ethernet_config.Attribute:
                                if (attr['Name'] != 'PositionNumber' and attr['Name'] != 'BuiltIn' and
                                        attr['Name'] != 'IpProtocolSelection' and attr['Name'] != 'Type'):
                                    # print(
                                    #     f"Profinet Interface {ethernet_config_number} Attribute {attr['Name']} {attr.Value.cdata.strip()}")
                                    # device[f"Profinet Interface {ethernet_config_number} {attr['Name']}"] = attr.Value.cdata.strip()
                                    device_ethernet_config[attr['Name']] = attr.Value.cdata.strip()
                            device_ethernet_configs.append(device_ethernet_config)
                            ethernet_config_number += 1
                        device["ethernet"] = device_ethernet_configs
                    devices[plc_name] = device
    return devices
