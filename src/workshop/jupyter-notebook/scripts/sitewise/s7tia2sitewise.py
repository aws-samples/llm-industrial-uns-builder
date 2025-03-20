from sitewise.sitewise_helper import *
from pathlib import Path


def map_s7_datatype_to_sw(s7_data_type) -> str:
    lower_s7_data_type = s7_data_type.lower()
    if lower_s7_data_type == "uint" or lower_s7_data_type == "int":
        return DataType.INTEGER.name
    elif lower_s7_data_type == "bool":
        return DataType.BOOLEAN.name
    else:
        return DataType.STRING.name


def add_or_create_to_sw_import(device_and_db_info, project_name, top_hierarchy_asset_name=None,
                               existing_sw_import: SiteWiseBulk = SiteWiseBulk()) -> SiteWiseBulk:
    devices = device_and_db_info
    bulk_import = existing_sw_import
    if top_hierarchy_asset_name:
        base_asset_model = AssetModel(f"{top_hierarchy_asset_name}_model",
                                 f"{project_name}_{top_hierarchy_asset_name}_model")
        base_asset = Asset(f"{top_hierarchy_asset_name}",
                                      f"{project_name}_{top_hierarchy_asset_name}",
                           f"{project_name}_{top_hierarchy_asset_name}_model")
        bulk_import.assetModels.append(base_asset_model)
        bulk_import.assets.append(base_asset)
    for plc_name, plc_info in devices.items():
        asset_model = AssetModel(f"{plc_name}_model", f"{project_name}_{plc_name}_model")
        bulk_import.assetModels.append(asset_model)
        base_asset_model.assetModelHierarchies.append(AssetModelHierarchy(f"{plc_name}_model_to_plant",
                                                                          f"{plc_name}_model_to_plant_hierarchy",
                                                                          asset_model.assetModelExternalId))
        asset = Asset.from_asset_model(plc_name, f"{project_name}_{plc_name}", asset_model)
        bulk_import.assets.append(asset)
        base_asset.assetHierarchies.append(AssetHierarchy(f"{plc_name}_model_to_plant_hierarchy",
                                                               asset.assetExternalId))
        for db_number, db_entries in plc_info["entries"].items():
            for entry in db_entries:
                print(entry)
                entry_name = entry["name"]
                entry_sw_datatype = map_s7_datatype_to_sw(entry['datatype'])
                asset_model_property = AssetModelProperty(f"{db_number}_{entry_name}",
                                                                           f"{db_number}_{entry_name}",
                                                                           entry_sw_datatype)
                asset_model.assetModelProperties.append(asset_model_property)
                # {PLCNAME}DB{DBID}/{ENTRYNAME}
            asset.assetProperties.append(
                AssetProperty.from_asset_model_property(asset_model_property,
                                                        f"{plc_name}DB{db_number}/{entry_name}"))
    return bulk_import

