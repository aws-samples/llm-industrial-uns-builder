

import boto3
import time


from ec2_metadata import ec2_metadata
aws_region = ec2_metadata.region
sitewise = boto3.client('iotsitewise', region_name=aws_region)
s3 = boto3.client('s3')


# Load configuration
aws_account = boto3.client('sts').get_caller_identity()['Account']
aws_region = ec2_metadata.region
aws_stack_name = 'uns-scale-connectivity-workshop' # ToDo Remove in WS Studio
bucketname = f'reinvent-{aws_stack_name}-{aws_account}-{aws_region}'
roleArn = f'arn:aws:iam::{aws_account}:role/data_import_role_workshop-{aws_stack_name}'


def disassociate_all_assets(asset_id):
    describe_asset_res = sitewise.describe_asset(assetId=asset_id)
    asset_name = describe_asset_res["assetName"]
    print(f'\tAsset: {asset_name}')
    asset_hierarchies = describe_asset_res["assetHierarchies"]
    child_asset_ids = []
    for asset_hierarchy in asset_hierarchies:
        asset_hierarchy_id = asset_hierarchy["id"]
        asset_summaries = sitewise.list_associated_assets(assetId=asset_id, hierarchyId=asset_hierarchy_id)["assetSummaries"]
        for asset in asset_summaries:
            child_asset_ids.append(asset["id"])
            sitewise.disassociate_assets(assetId=asset_id, hierarchyId=asset_hierarchy_id, childAssetId=asset["id"]) 
            print(f'\t\tChild: {asset["name"]}')
    if len(child_asset_ids) == 0: print(f'\t\tNo child assets found, skip')
    for child_asset_id in child_asset_ids:
        disassociate_all_assets(child_asset_id)


def delete_all_objects(bucket_name):
    s3 = boto3.client('s3')
    objects = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' not in objects:
        print(f'\n{bucket_name} bucket is empty, skip')
        return
    print(f'\nDeleting objects from {bucket_name} bucket..')
    for obj in objects['Contents']:
        s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
        print(f"\tDeleted -> {obj['Key']}")

    print(f"\nAll objects deleted successfully from {bucket_name}")


def check_asset_exists(asset_eid):
    try:
        sitewise.describe_asset(
            assetId=asset_eid,
            excludeProperties=True)
        return True  
    except:
        return False


def check_asset_model_exists(asset_model_eid):
    try:
        sitewise.describe_asset_model(
            assetModelId=asset_model_eid,
            excludeProperties=True)
        return True  
    except:
        return False


def delete_all_sitewise_elements():
    asset_eids = ["eID_Body_Shop_Cell", "eID_Plastic_Molding_Cell", "eID_Tooling_and_Dye_Cell", "eID_Press_Shop_Cell","eID_Paint_Shop_Cell","eID_Component_Fabrication_Unit", "eID_Forming_Unit", "eID_Reinvent_Car_Factory", "eID_Las_Vegas_Facility"]
    asset_model_eids = [ "eID_Enterprise_Unit", "eID_Regional_Unit", "eID_Production_Unit", "eID_General_Cell"]
    
    if check_asset_exists('externalId:eID_Reinvent_Car_Factory'):
        disassociate_all_assets('externalId:eID_Reinvent_Car_Factory')
    else:
        print(f'\tNo asset hierarchies found')

    for asset_eid in asset_eids:
        if check_asset_exists(f'externalId:{asset_eid}'):
            sitewise.delete_asset(assetId=f'externalId:{asset_eid}')
            print(f'\tRemoved asset: {asset_eid}')
    time.sleep(3)    
    print(f'\tAll assets were removed')  
    
    for asset_model_eid in asset_model_eids: 
        if check_asset_model_exists(f'externalId:{asset_model_eid}'):
            asset_model_name=sitewise.describe_asset_model(assetModelId=f'externalId:{asset_model_eid}')['assetModelName']
            sitewise.update_asset_model(
            assetModelId=f'externalId:{asset_model_eid}',
            assetModelName=asset_model_name,
            assetModelProperties=[],
            assetModelHierarchies=[],
            assetModelCompositeModels=[])
            time.sleep(5)
            print(f'\tRemoved properties and hierarchy from asset model: {asset_model_eid}')
            sitewise.delete_asset_model(assetModelId=f'externalId:{asset_model_eid}')
            print(f'\tRemoved asset model: {asset_model_eid}')
       
    print(f'\tAll asset models were removed')

    print(f'\nYour factory was successfully deleted\n')


def check_if_portal_exists(portal_name):
    data = sitewise.list_portals() 
    portal_names = [portal['name'] for portal in data['portalSummaries']] 
    if portal_name in portal_names :
        return True  
    else: 
        return False


def create_visualisation(portal_name,email_id):
    data = sitewise.list_portals() 
    portal_names = [portal['name'] for portal in data['portalSummaries']] 

    if aws_stack_name == "uns-scale-connectivity-workshop":    # To switch between Isengard and WS Studio
        my_role ="WSParticipantRole"
    else:
        my_role = "Admin"

    if portal_name not in portal_names :
   
        print(f'\tCreating Portal: {portal_name}')
        portal_response = sitewise.create_portal(
        portalName=portal_name,
        portalContactEmail=email_id,
        roleArn=roleArn,
        portalAuthMode='IAM',
        )
        portal_url = portal_response.get("portalStartUrl", "URL not found")
        portal_id = portal_response.get("portalId", "portalId not found")
        
        #time.sleep(55)
        while True:
            res = sitewise.describe_portal(portalId=portal_id)
            state = res["portalStatus"]["state"]
            if state in ('CREATING','UPDATING','DELETING'):
                try:
                    progress = res["progress"]
                    print(f'Status: {state} ')                
                except:
                    print(f'Status: {state}')
            elif state == 'FAILED':
                print(f'Status: {state}')
                break
            else:
                print(f'Status: {state}')
            if state == 'ACTIVE': break
            time.sleep(20) # Check status every 15 seconds

        print(f'\t01 Creating Access Policy for Portal {portal_name}')
        iam_response = sitewise.create_access_policy(
        accessPolicyIdentity={
            'iamRole': {'arn': f'arn:aws:iam::{aws_account}:role/{my_role}'}
        },
        accessPolicyResource={
            'portal': {'id': portal_id}
        },
        accessPolicyPermission='ADMINISTRATOR',
        )
        policy_id = iam_response.get("accessPolicyId", "policyId not found")
        time.sleep(10)

        print(f'\t02 Creating Project: Project {portal_name}')
        proj_response = sitewise.create_project(
        portalId=portal_id,
        projectName=f'Project {portal_name}',
        )
        project_id = proj_response.get("projectId", "projectId not found")
        time.sleep(20)

        print(f'\t03 Adding assets to Project {portal_name}')
        master_asset = sitewise.describe_asset(assetId='externalId:eID_Reinvent_Car_Factory',excludeProperties=True)['assetId']
        asset_project_resp = sitewise.batch_associate_project_assets(
        projectId=project_id,
        assetIds=[master_asset],
        )
        time.sleep(10)

        print(f'\t04 Setting up your Dashboard in Portal {portal_name}')
        dashboard_response = sitewise.create_dashboard(
        projectId=project_id,
        dashboardName=f'Dashboard {portal_name}',
        dashboardDefinition='{\"widgets\": [{\"type\": \"sc-status-grid\", \"title\": \"Vehicle\", \"x\": 0, \"y\": 0, \"height\": 3, \"width\": 3, \"annotations\": {\"y\": [{\"comparisonOperator\": \"LT\", \"value\": 20000, \"color\": \"#D13212\", \"showValue\": true}]}}, {\"type\": \"sc-bar-chart\", \"title\": \"Wind Speed\", \"x\": 3, \"y\": 3, \"height\": 3, \"width\": 3}]}',
        )
        dasboard_id = dashboard_response.get("dashboardId", "dashboardId not found")
        print(f'\t{portal_name} can be accessed at {portal_url}')
        time.sleep(5)
        portal_meta= [policy_id, dasboard_id, project_id, portal_id]
        print (f"PolicyId   :{portal_meta[0]}")
        print (f"DashboardId:{portal_meta[1]}")
        print( f"ProjectId  :{portal_meta[2]}")
        print( f"PortalId   :{portal_meta[3]}\n--------")
        return portal_meta
    
    else :
        print(f"A portal with the name '{portal_name}' already exists.")
         

def delete_visualisation(portal_ids):
    sitewise.delete_dashboard(dashboardId=portal_ids[1])
    time.sleep(4)
    sitewise.delete_project(projectId=portal_ids[2])
    time.sleep(4)
    sitewise.delete_access_policy(accessPolicyId=portal_ids[0])
    time.sleep(4)
    sitewise.delete_portal(portalId=portal_ids[3])
    time.sleep(4)
    print("Portal deleted")

import boto3
import time


from ec2_metadata import ec2_metadata
aws_region = ec2_metadata.region
sitewise = boto3.client('iotsitewise', region_name=aws_region)
s3 = boto3.client('s3')


# Load configuration
aws_account = boto3.client('sts').get_caller_identity()['Account']
aws_region = ec2_metadata.region
aws_stack_name = 'uns-scale-connectivity-workshop' # ToDo Remove in WS Studio
bucketname = f'reinvent-{aws_stack_name}-{aws_account}-{aws_region}'
roleArn = f'arn:aws:iam::{aws_account}:role/data_import_role_workshop-{aws_stack_name}'


def disassociate_all_assets(asset_id):
    describe_asset_res = sitewise.describe_asset(assetId=asset_id)
    asset_name = describe_asset_res["assetName"]
    print(f'\tAsset: {asset_name}')
    asset_hierarchies = describe_asset_res["assetHierarchies"]
    child_asset_ids = []
    for asset_hierarchy in asset_hierarchies:
        asset_hierarchy_id = asset_hierarchy["id"]
        asset_summaries = sitewise.list_associated_assets(assetId=asset_id, hierarchyId=asset_hierarchy_id)["assetSummaries"]
        for asset in asset_summaries:
            child_asset_ids.append(asset["id"])
            sitewise.disassociate_assets(assetId=asset_id, hierarchyId=asset_hierarchy_id, childAssetId=asset["id"]) 
            print(f'\t\tChild: {asset["name"]}')
    if len(child_asset_ids) == 0: print(f'\t\tNo child assets found, skip')
    for child_asset_id in child_asset_ids:
        disassociate_all_assets(child_asset_id)


def delete_all_objects(bucket_name):
    s3 = boto3.client('s3')
    objects = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' not in objects:
        print(f'\n{bucket_name} bucket is empty, skip')
        return
    print(f'\nDeleting objects from {bucket_name} bucket..')
    for obj in objects['Contents']:
        s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
        print(f"\tDeleted -> {obj['Key']}")

    print(f"\nAll objects deleted successfully from {bucket_name}")


def check_asset_exists(asset_eid):
    try:
        sitewise.describe_asset(
            assetId=asset_eid,
            excludeProperties=True)
        return True  
    except:
        return False


def check_asset_model_exists(asset_model_eid):
    try:
        sitewise.describe_asset_model(
            assetModelId=asset_model_eid,
            excludeProperties=True)
        return True  
    except:
        return False
    
def delete_child_assets(classic=True):
    genai_asset_eids =["eID_01_PRSH_X01", "eID_02_BSH_X01", "eID_03_PSH_X01", "eID_04_PLS_X02", "eID_05_TLD_X02"]
    classic_asset_eids = ["eID_Body_Shop_Cell", "eID_Plastic_Molding_Cell", "eID_Tooling_and_Dye_Cell", "eID_Press_Shop_Cell","eID_Paint_Shop_Cell"]
    try:
        disassociate_all_assets('externalId:eID_Component_Fabrication_Unit')
        disassociate_all_assets('externalId:eID_Forming_Unit')
    except:
        None

    if classic:
        asset_eids = classic_asset_eids
    else: 
        asset_eids = genai_asset_eids

    for asset_eid in asset_eids:
        if check_asset_exists(f'externalId:{asset_eid}'):
            sitewise.delete_asset(assetId=f'externalId:{asset_eid}')
    time.sleep(3)    
    print(f'\tChild assets were removed')


def delete_all_sitewise_elements():
    asset_eids = ["eID_Body_Shop_Cell", "eID_Plastic_Molding_Cell", "eID_Tooling_and_Dye_Cell", "eID_Press_Shop_Cell","eID_Paint_Shop_Cell","eID_Component_Fabrication_Unit", "eID_Forming_Unit", "eID_Reinvent_Car_Factory", "eID_Las_Vegas_Facility"]
    asset_model_eids = [ "eID_Enterprise_Unit", "eID_Regional_Unit", "eID_Production_Unit", "eID_General_Cell"]
    
    if check_asset_exists('externalId:eID_Reinvent_Car_Factory'):
        disassociate_all_assets('externalId:eID_Reinvent_Car_Factory')
    else:
        print(f'\tNo asset hierarchies found')

    for asset_eid in asset_eids:
        if check_asset_exists(f'externalId:{asset_eid}'):
            sitewise.delete_asset(assetId=f'externalId:{asset_eid}')
            print(f'\tRemoved asset: {asset_eid}')
    time.sleep(3)    
    print(f'\tAll assets were removed') 

    delete_child_assets(classic=False)
    
    for asset_model_eid in asset_model_eids: 
        if check_asset_model_exists(f'externalId:{asset_model_eid}'):
            asset_model_name=sitewise.describe_asset_model(assetModelId=f'externalId:{asset_model_eid}')['assetModelName']
            try:
                sitewise.update_asset_model(
                assetModelId=f'externalId:{asset_model_eid}',
                assetModelName=asset_model_name,
                assetModelProperties=[],
                assetModelHierarchies=[],
                assetModelCompositeModels=[])
                time.sleep(5)
                print(f'\tRemoved properties and hierarchy from asset model: {asset_model_eid}')
                sitewise.delete_asset_model(assetModelId=f'externalId:{asset_model_eid}')
                print(f'\tRemoved asset model: {asset_model_eid}')
            except:
                print('Deletion Incomplete. Please execute delete again')
       
    print(f'\tAll asset models were removed')

    print(f'\nYour factory was successfully deleted\n')


def check_if_portal_exists(portal_name):
    data = sitewise.list_portals() 
    portal_names = [portal['name'] for portal in data['portalSummaries']] 
    if portal_name in portal_names :
        return True  
    else: 
        return False


def create_visualisation(portal_name,email_id):
    data = sitewise.list_portals() 
    portal_names = [portal['name'] for portal in data['portalSummaries']] 

    if aws_stack_name == "uns-scale-connectivity-workshop":    # To switch between Isengard and WS Studio
        my_role ="WSParticipantRole"
    else:
        my_role = "Admin"

    if portal_name not in portal_names :
   
        print(f'\tCreating Portal: {portal_name}')
        portal_response = sitewise.create_portal(
        portalName=portal_name,
        portalContactEmail=email_id,
        roleArn=roleArn,
        portalAuthMode='IAM',
        )
        portal_url = portal_response.get("portalStartUrl", "URL not found")
        portal_id = portal_response.get("portalId", "portalId not found")
        
        #time.sleep(55)
        while True:
            res = sitewise.describe_portal(portalId=portal_id)
            state = res["portalStatus"]["state"]
            if state in ('CREATING','UPDATING','DELETING'):
                try:
                    progress = res["progress"]
                    print(f'Status: {state} ')                
                except:
                    print(f'Status: {state}')
            elif state == 'FAILED':
                print(f'Status: {state}')
                break
            else:
                print(f'Status: {state}')
            if state == 'ACTIVE': break
            time.sleep(20) # Check status every 15 seconds

        print(f'\t01 Creating Access Policy for Portal {portal_name}')
        iam_response = sitewise.create_access_policy(
        accessPolicyIdentity={
            'iamRole': {'arn': f'arn:aws:iam::{aws_account}:role/{my_role}'}
        },
        accessPolicyResource={
            'portal': {'id': portal_id}
        },
        accessPolicyPermission='ADMINISTRATOR',
        )
        policy_id = iam_response.get("accessPolicyId", "policyId not found")
        time.sleep(10)

        print(f'\t02 Creating Project: Project {portal_name}')
        proj_response = sitewise.create_project(
        portalId=portal_id,
        projectName=f'Project {portal_name}',
        )
        project_id = proj_response.get("projectId", "projectId not found")
        time.sleep(20)

        print(f'\t03 Adding assets to Project {portal_name}')
        master_asset = sitewise.describe_asset(assetId='externalId:eID_Reinvent_Car_Factory',excludeProperties=True)['assetId']
        asset_project_resp = sitewise.batch_associate_project_assets(
        projectId=project_id,
        assetIds=[master_asset],
        )
        time.sleep(10)

        print(f'\t04 Setting up your Dashboard in Portal {portal_name}')
        dashboard_response = sitewise.create_dashboard(
        projectId=project_id,
        dashboardName=f'Dashboard {portal_name}',
        dashboardDefinition='{\"widgets\": [{\"type\": \"sc-status-grid\", \"title\": \"Vehicle\", \"x\": 0, \"y\": 0, \"height\": 3, \"width\": 3, \"annotations\": {\"y\": [{\"comparisonOperator\": \"LT\", \"value\": 20000, \"color\": \"#D13212\", \"showValue\": true}]}}, {\"type\": \"sc-bar-chart\", \"title\": \"Wind Speed\", \"x\": 3, \"y\": 3, \"height\": 3, \"width\": 3}]}',
        )
        dasboard_id = dashboard_response.get("dashboardId", "dashboardId not found")
        print(f'\t{portal_name} can be accessed at {portal_url}')
        time.sleep(5)
        portal_meta= [policy_id, dasboard_id, project_id, portal_id]
        print (f"PolicyId   :{portal_meta[0]}")
        print (f"DashboardId:{portal_meta[1]}")
        print( f"ProjectId  :{portal_meta[2]}")
        print( f"PortalId   :{portal_meta[3]}\n--------")
        return portal_meta
    
    else :
        print(f"A portal with the name '{portal_name}' already exists.")
         

def delete_visualisation(portal_ids):
    try: 
        sitewise.delete_dashboard(dashboardId=portal_ids[1])
        time.sleep(4)
    except:
        print("Dashboard was deleted")
    try: 
        sitewise.delete_project(projectId=portal_ids[2])
        time.sleep(4)
    except:
        print("Project was deleted")
    try: 
        sitewise.delete_access_policy(accessPolicyId=portal_ids[0])
        time.sleep(4)
    except:
        print("Access Policy was deleted or incorrect")
    try: 
        sitewise.delete_portal(portalId=portal_ids[3])
        time.sleep(4)
    except:
        print("Portal was deleted")
    
    print("Success: Portal Deleted")