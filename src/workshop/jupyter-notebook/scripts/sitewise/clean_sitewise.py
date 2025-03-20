import boto3
import time
import argparse
import uuid

sw_client = boto3.client('iotsitewise', region_name='ap-southeast-1')
SCRIPT_TIMEOUT_SECONDS = 60
MAX_RETRY = 3
SLEEP_BETWEEN_RETRY = 0.3


# Retrieve all associated assets for a given asset and hierarchy
def list_associated_assets(asset_id, hierarchy_id):
    all_associated_assets = []
    next_token = None
    # Paginate
    while True:
        if next_token:
            response = sw_client.list_associated_assets(assetId=asset_id, hierarchyId=hierarchy_id,
                                                        nextToken=next_token)
        else:
            response = sw_client.list_associated_assets(assetId=asset_id, hierarchyId=hierarchy_id)
        associated_assets = response['assetSummaries']
        all_associated_assets += associated_assets
        # Check if there are more pages of results
        if 'nextToken' in response:
            next_token = response['nextToken']
        else:
            break
        time.sleep(1)
    return all_associated_assets


# Retrieve all child assets for a given asset
def get_child_assets(asset_id):
    child_assets = []
    response = sw_client.describe_asset(assetId=asset_id, excludeProperties=True)
    asset_hierarchies = response['assetHierarchies']
    for hierarchy in asset_hierarchies:
        hierarchy_id = hierarchy['id']
        associated_assets = list_associated_assets(asset_id, hierarchy_id)
        child_assets += associated_assets
        time.sleep(0.1)
    return child_assets


def get_root_assets():
    assets_list = []
    next_token = None
    # Paginate
    while True:
        if next_token:
            response = sw_client.list_assets(nextToken=next_token, filter='TOP_LEVEL')
        else:
            response = sw_client.list_assets(filter='TOP_LEVEL')
        associated_assets = response['assetSummaries']
        assets_list += associated_assets
        # Check if there are more pages of results
        if 'nextToken' in response:
            next_token = response['nextToken']
        else:
            break

        time.sleep(SLEEP_BETWEEN_RETRY)

    return assets_list


# Recursive
##############################################################################

def print_hierarchy(child_assets, hierarchy_level):
    elapsed_time = time.time() - script_start_time
    for child_asset in child_assets:
        child_asset_name = child_asset['name']
        child_asset_id = child_asset['id']
        position = 3 * (hierarchy_level - 2)
        spaces = " " * position
        print(child_asset)
        print(f'{spaces}|__ Asset Name: {child_asset_name}, Asset Id: {child_asset_id}')
        if not include_all_levels: continue
        next_level_child_assets = get_child_assets(child_asset_id)
        if len(next_level_child_assets) > 0:
            print_hierarchy(next_level_child_assets, hierarchy_level + 1)


def delete_assets_hierarchy(father_asset_id=None, father_hierarchy_list=None):
    for father_hierarchy in father_hierarchy_list:
        father_hierarchy_id = father_hierarchy['id']
        associated_assets = list_associated_assets(father_asset_id, father_hierarchy_id)

        for child_asset in associated_assets:
            child_asset_name = child_asset['name']
            child_asset_id = child_asset['id']
            print(child_asset)
            # check status

            # check  hirarchies
            if len(child_asset['hierarchies']) > 0:
                print(child_asset['hierarchies'])
                print(child_asset_id)
                delete_assets_hierarchy(father_asset_id=child_asset_id,
                                        father_hierarchy_list=child_asset['hierarchies'])

            # Disassociate
            print(
                f'\nDisassociate Child Asset Name: {child_asset_name}, Asset Id: {child_asset_id}, Father Id: {father_asset_id}, Hierarchy Id: {father_hierarchy_id}')
            sw_client.disassociate_assets(assetId=father_asset_id,
                                          hierarchyId=father_hierarchy_id,
                                          childAssetId=child_asset_id)
            print("Succeed")
            # Delete
            retry = 0
            while retry <= MAX_RETRY and retry >= 0:
                # Disasosation Operation is Async
                time.sleep(SLEEP_BETWEEN_RETRY)
                try:
                    print(f'\nDelete Child Asset Name: {child_asset_name}, Asset Id: {child_asset_id}, try:{retry}')
                    sw_client.delete_asset(assetId=child_asset_id)
                    print("Succeed")
                except  Exception as e:
                    print(e)
                    retry += 1
                    continue

                retry = -1


def delete_models(father_model_id=None):
    if father_model_id is not None:
        sw_client.delete_asset_model(father_model_id)
        return 1

    total_model = 0
    all_models = []
    next_token = None
    # Paginate
    while True:
        if next_token:
            response = sw_client.list_asset_models(nextToken=next_token)
        else:
            response = sw_client.list_asset_models()
        associated_assets = response['assetModelSummaries']
        all_models += associated_assets
        # Check if there are more pages of results
        if 'nextToken' in response:
            next_token = response['nextToken']
        else:
            break

        time.sleep(SLEEP_BETWEEN_RETRY)

    while True:
        if next_token:
            response = sw_client.list_asset_models(nextToken=next_token,
                                                   assetModelTypes=['ASSET_MODEL', 'COMPONENT_MODEL'])
        else:
            response = sw_client.list_asset_models(assetModelTypes=['ASSET_MODEL', 'COMPONENT_MODEL'])

        associated_assets = response['assetModelSummaries']
        all_models += associated_assets
        # Check if there are more pages of results
        if 'nextToken' in response:
            next_token = response['nextToken']
        else:
            break

        time.sleep(SLEEP_BETWEEN_RETRY)

    print(all_models)
    for model in all_models:
        try:
            print(
                f"\nDelete Asset Model Name: {model['name']}, Asset Model Id: {model['id']}, Status : {model['status']['state']}")
            if model['status']['state'] == 'ACTIVE':
                sw_client.delete_asset_model(assetModelId=model['id'])
                print(":Success")
                time.sleep(SLEEP_BETWEEN_RETRY)
            else:
                print('Skipped')

        except  Exception as e:
            print(":Failed")
            print(e)

    return len(all_models)


# Main Operations
##############################################################################
def asset_tree(asset_id):
    asset = get_asset(asset_id)
    child_assets = get_child_assets(asset_id)
    print(f'\nAsset Name: {asset}, Asset Id: {asset_id}')
    print_hierarchy(child_assets, 2)


def asset_drop(asset_id):
    assets_list = []

    if asset_id == 'ALL':
        assets_list = get_root_assets()
    else:
        try:
            asset = get_asset(asset_id)
            print(asset)
            asset['hierarchies'] = asset['assetHierarchies']
            asset['id'] = asset['assetId']
            asset['name'] = asset['assetName']
            assets_list.append(asset)
        except sw_client.exceptions.ResourceNotFoundException as e:
            print(e)
            exit

    for asset in assets_list:
        child_assets = get_child_assets(asset['id'])

        # Delete childs
        delete_assets_hierarchy(asset['id'], asset['hierarchies'])

        # Delete Father
        print(f"\nDelete Root Node Name: {asset['name']}, Asset Id: {asset['id']}")
        sw_client.delete_asset(assetId=asset['id'])


def asset_model_drop(asset_model_id):
    print(f"\nDelete Asset Models")
    delete_models(father_model_id=None)


# Tools
##############################################################################
# Validation
def sitewise_uuid(value):
    try:
        uuid.UUID(str(value))
        return value
    except ValueError:
        return False

    raise Exception("\nInvalid  ID!")


# Get asset by id
def get_asset(asset_id):
    asset = sw_client.describe_asset(assetId=asset_id, excludeProperties=True)
    return asset


def get_asset_model(model_id):
    asset_model = sw_client.describe_asset_model(assetModelId=model_id, excludeProperties=True)

    return asset_model


# Main
##############################################################################
if __name__ == "__main__":
    script_start_time = time.time()
    # Create the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments
    parser.add_argument("--object", help="Object ['model','asset']")
    parser.add_argument("--operation", help="Operation ['tree','view','drop']")
    parser.add_argument("--asset-id", type=sitewise_uuid, default=None,
                        help="ID of the model to delete otherwise all models will be deleted ")
    parser.add_argument("--wipe", help="Drop all the model", action="store_true")
    parser.add_argument("--all-levels", help="Include all levels in the hierarchy", action="store_true")

    # Parse the arguments
    args = parser.parse_args()
    # Access the arguments
    operation = args.operation.strip()
    sitewise_entity = args.object.strip()
    asset_id = args.asset_id
    include_all_levels = args.all_levels

    print("%s,%s,%s" % (sitewise_entity, operation, asset_id))
    if (sitewise_entity == 'asset') and (operation == 'drop'):
        sitewise_id = args.asset_id
        if args.wipe:
            sitewise_id = 'ALL'

        asset_drop(sitewise_id)
        exit

    if (sitewise_entity == 'model') and (operation == 'drop'):
        sitewise_id = args.asset_id
        if args.wipe:
            sitewise_id = 'ALL'
        asset_model_drop(sitewise_id)
        exit

    if (sitewise_entity == 'asset') and (operation == 'tree'):
        asset_tree(sitewise_id)
        exit

    print("Invalid combination of flags")


