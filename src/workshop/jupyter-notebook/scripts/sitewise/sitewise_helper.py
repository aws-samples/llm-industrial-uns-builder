import jsonpickle
from enum import Enum
from pathlib import Path


class AssetModel:
    def __init__(self, assetModelName: str, assetModelExternalId: str):
        self.assetModelName = assetModelName
        self.assetModelExternalId = assetModelExternalId
        self.assetModelProperties: [AssetModelProperty] = []
        self.assetModelHierarchies: [AssetModelHierarchy] = []


class DataType(Enum):
    STRING = 'STRING'
    INTEGER = 'INTEGER'
    DOUBLE = 'DOUBLE'
    BOOLEAN = 'BOOLEAN'
    STRUCT = 'STRUCT'


class AssetModelProperty:
    def __init__(self, name: str, externalId: str, dataType: DataType):
        self.name = name
        self.externalId = externalId
        self.dataType = dataType
        # for now just hardcode the type
        self.type = {
            "measurement": {
                "processingConfig": {
                    "forwardingConfig": {
                        "state": "DISABLED"
                    }
                }
            }
        }


class AssetModelHierarchy:
    def __init__(self, name: str, externalId: str, childAssetModelExternalId: str):
        self.name = name
        self.externalId = externalId
        self.childAssetModelExternalId = childAssetModelExternalId


class Asset:
    def __init__(self, assetName: str, assetExternalId: str, assetModelExternalId: str):
        self.assetName = assetName
        self.assetExternalId = assetExternalId
        self.assetModelExternalId = assetModelExternalId
        self.assetProperties: [AssetProperty] = []
        self.assetHierarchies: [AssetHierarchy] = []

    @classmethod
    def from_asset_model(cls, assetName: str, assetExternalId: str, assetModel:AssetModel):
        return cls(assetName, assetExternalId, assetModel.assetModelExternalId)




class AssetProperty:
    def __init__(self, externalId: str, alias: str):
        self.externalId = externalId
        self.alias = alias

    @classmethod
    def from_asset_model_property(cls, asset_model_property, alias: str):
        return cls(asset_model_property.externalId, alias)

class AssetHierarchy:
    def __init__(self, externalId: str, childAssetExternalId: str):
        self.externalId = externalId
        self.childAssetExternalId = childAssetExternalId


class SiteWiseBulk:
    def __init__(self, assetModels: [AssetModel] = [], assets: [Asset] = []):
        self.assetModels = assetModels
        self.assets = assets

    def write_to_file(self, file_name: Path):
        with open(file_name, "w") as json_file:
            json_file.write(jsonpickle.encode(self, unpicklable=False, indent=2))
