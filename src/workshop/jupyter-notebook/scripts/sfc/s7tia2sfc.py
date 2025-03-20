import base64
import json
import glob
import shutil
import zipfile
from pathlib import Path
import os
from s7tia import tia_block_helper
import boto3
import botocore

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

sfcArtifatctBaseURI = 'https://github.com/aws-samples/shopfloor-connectivity/releases/download'
sfcVersionInUse = '1.5.4'

def create_sfc_import_files(device_and_db_info, sfc_output, region, credProvider, gg, thingArn, ggcompversion, certParams):
    Sources = {}
    s7source = {}
    Channels = {}
    s7channel = {}
    with open(get_file_with_pathlib('templates/sfc-conf.json.template'), 'r') as sfc_template_file:
        sfc_template = json.load(sfc_template_file)
    
    # create list from tia export
    tia = list(device_and_db_info.values())

    ################################
    # LOOP through TIA export obj  #
    ################################
    for plc_info in tia:
        s7source['Name']=plc_info['asset_name']
        s7source['AdapterController']=plc_info['asset_name']+'_Controller'
        s7source['Description']=plc_info['TypeName']
        s7source['ProtocolAdapter']="S7FleetPLCSim"
        Sources[plc_info['asset_name']] = s7source
        s7source = {}

        # LOOP through all channel entries
        for entries in plc_info['entries'].values():
            for entry in entries:
                db_number=entry['db_number']
                s7channel['Name'] = db_number+'_'+entry['name']
                # Make S7 Channel Resource Format compliant
                dataType=str(entry['datatype']).upper()
                byteOffSet=entry['offset'] // 8
                bitOffSet=entry['offset'] % 8
                # now compliant
                s7channel['Address'] = "%DB{DB_NUMBER}:{BYTE_OFFSET}.{BIT_OFFSET}:{DATATYPE}"\
                .format(DB_NUMBER=entry['db_number'], BYTE_OFFSET=byteOffSet, BIT_OFFSET=bitOffSet, DATATYPE=dataType)
                Channels[db_number+'_'+entry['name']] = s7channel
                s7channel = {}
        # add Channels to Sources Obj
        Sources[plc_info['asset_name']]['Channels'] = Channels

        # add Controller entries to ProtocolAdapters
        sfc_template['ProtocolAdapters']['S7FleetPLCSim']['Controllers'][plc_info['asset_name']+'_Controller'] = "$(S7-Adapter-Controller-Block, ipAddress={IP}, controllerType={S7_TYPE})".format(IP=plc_info['ethernet'][0]['NetworkAddress'], S7_TYPE='S7-1500')

        # Reference Sources in the Main SFC Schedule
        sfc_template['Schedules'][0]['Sources'][plc_info['asset_name']] = ['*']

    ################################
    #           LOOP END           #
    ################################

    # write Sources object as file for later include
    write_json_file_to_path(Sources, sfc_output, 'include_generated_sources.json')

    # create include section for sources.json
    sfc_template['Sources'] = "@file:include_generated_sources.json"

    # set targets
    # create SW Target Mapping here...
    MappedAssets = { "Assets": []}
    for source in Sources.values():
        props = []
        for property in source['Channels'].values():
            props.append({"PropertyAlias":"/some/datastream/"+source['Name']+"/"+property['Name'],
                          "DataPath": "sources.\"{sourceName}\".values.\"{channelName}\"".format(sourceName=source['Name'], channelName=property['Name'])
                          })
        MappedAssets['Assets'].append({
            "Properties": props 
            }) 
    #print(MappedAssets)
    
    # write MappedAssets object as file for later include
    


    sfc_template['Targets']['DebugTarget'] = "$(DebugTarget-Block, logLevel=Info)"
    if credProvider=='AWS_IOT_CERT':
        SWTarget={ "Active": True, "TargetType": "AWS-SITEWISE","Region": region,"CredentialProviderClient": "AwsIotClient", "Assets": MappedAssets['Assets']}
        write_json_file_to_path(SWTarget, sfc_output, 'include_generated_swtarget.json')
        sfc_template['Targets']['SitewiseTarget'] = "@file:include_generated_swtarget.json"
        sfc_template['AwsIotCredentialProviderClients']['AwsIotClient'] = \
            "$(AwsIotClient-Block, endpoint={endpoint}, rolealias={rolealias}, thingname={thingname}, certificatefilepath={certificatefilepath}, keyfilepath={keyfilepath}, rootcafilepath={rootcafilepath}, greengrasspath={greengrasspath})" \
        .format(
                endpoint=certParams['endpoint'],\
                rolealias=certParams['rolealias'],\
                thingname=certParams['thingname'],\
                certificatefilepath=certParams['certificatefilepath'],\
                keyfilepath=certParams['keyfilepath'],\
                rootcafilepath=certParams['rootcafilepath'],\
                greengrasspath=certParams['greengrasspath']\
            )
    else:
        SWTarget={ "Active": True, "TargetType": "AWS-SITEWISE","Region": region, "Assets": MappedAssets['Assets']}
        write_json_file_to_path(SWTarget, sfc_output, 'include_generated_swtarget.json')
        sfc_template['Targets']['SitewiseTarget'] = "@file:include_generated_swtarget.json"

    # write main sfc-config as file
    write_json_file_to_path(sfc_template, sfc_output, 'sfc_config_generated.json')

    # also copy all required sfc-templates to out-dir
    file_pattern=str(get_file_with_pathlib('templates/*.json'))
    for file in glob.glob(file_pattern):
        #print(file)
        shutil.copy(file, sfc_output)

    # now zip all sfc-files inside the imports/sfc dir
    zip = zipfile.ZipFile(sfc_output / "sfc-conf.zip", "w", zipfile.ZIP_DEFLATED)
    file_pattern=str(sfc_output)+'/*.json'
    #print(file_pattern)
    for file in glob.glob(file_pattern):
        abspath=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', file))
        zip.write(abspath, arcname=os.path.basename(file))
    zip.close()


    # stdout final sfc-config
    print(bcolors.OKGREEN + '++++++++++++++')
    print('+ SFC CONFIG +')
    print('++++++++++++++')
    print('')
    print('...Packaging at @PATH: '+str(sfc_output)+bcolors.ENDC)
    print('')
    #print(json.dumps(sfc_template, sort_keys=True, indent=4))
    print('')
    print(bcolors.OKGREEN + '-> Successfully created SFC Config Zip Package @PATH: '+str(sfc_output)+"/sfc-conf.zip" + bcolors.ENDC)

    createSFCInstallScript(sfcVersionInUse, sfc_output)
    print(bcolors.OKGREEN + '-> Successfully created SFC Standalone Installer @PATH: '+str(sfc_output)+'/sfc-standalone-install.sh')
    print('')
    print('>> To install SFC standalone run:')
    print('')
    print('[LINUX] cd '+str(sfc_output)+' && ./sfc-standalone-install.sh && cd -')
    print('[WINDOWS] execute (double click) sfc-standalone-install.bat')
    print('')
    print('>> To execute SFC standalone on that box run:')
    print('')
    print('[LINUX] cd '+str(sfc_output)+' && export SFC_DEPLOYMENT_DIR=$(pwd) && ./sfc-main/bin/sfc-main -config sfc_config_generated.json')
    print('[WINDOWS] execute (double click) sfc-standalone-runner.bat'+bcolors.ENDC)
    print('')
    # check if Greengrass Comp & Installer needs to be created
    if gg == True:
        createSFCGreengrassCompRecipe(sfcVersionInUse, ggcompversion, sfc_output, region, thingArn)
        


def createSFCInstallScript(sfcVersion, sfc_output):
    # WINDOWS
    #curl -LO https://github.com/aws-samples/shopfloor-connectivity/releases/download/v1.3.1/{sfc-main.tar.gz,debug-target.tar.gz,aws-sitewise-target.tar.gz,s7.tar.gz}
    #FOR %%i IN (*.tar.gz) DO tar -xf %%i

    # WINDOWS RUN
    #@ECHO OFF
    #SET SFC_DEPLOYMENT_DIR=%cd%
    #sfc-main\bin\sfc-main.bat -config %SFC_DEPLOYMENT_DIR%\sfc_config_generated.json

    # first, identify SFC modules in use for in-process runtime...
    module_list=[]
    module_list.append('sfc-main') # sfc-main (core) is always required
    with open(get_file_with_pathlib('templates/include_types.json'), 'r') as sfc_module_file:
        modules = json.load(sfc_module_file)
    for target in modules['Targets']:
        module = modules['Targets'][target]['JarFiles'][0].replace('${SFC_DEPLOYMENT_DIR}/', '').replace('/lib', '')
        module_list.append(module)
    for adapter in modules['Adapters']:
        module = modules['Adapters'][adapter]['JarFiles'][0].replace('${SFC_DEPLOYMENT_DIR}/', '').replace('/lib', '')
        module_list.append(module)
    module_list_str= str(module_list).replace('[','{').replace(']','}').replace(' ','').replace('\'','')

    # create an sfc installer shell script
    installer = \
"""#!/bin/bash
set -e
wget {ARTIFACT_BASE_URL}/v{VERSION}/{MODULES}.tar.gz
for file in *.tar.gz; do
  tar -xf "$file"
  rm "$file"
done
"""\
    .format(ARTIFACT_BASE_URL=sfcArtifatctBaseURI, VERSION=sfcVersion, MODULES=module_list_str)
    write_file_to_path(installer, sfc_output, 'sfc-standalone-install.sh')
    os.chmod(str(sfc_output)+'/'+'sfc-standalone-install.sh', 0o755)

    # WINDOWS
    # create an sfc installer bat script
    installer_bat = \
"""curl -LO {ARTIFACT_BASE_URL}/v{VERSION}/{MODULES}
FOR %%i IN (*.tar.gz) DO tar -xf %%i
"""\
    .format(ARTIFACT_BASE_URL=sfcArtifatctBaseURI, VERSION=sfcVersion, MODULES="{sfc-main.tar.gz,debug-target.tar.gz,aws-sitewise-target.tar.gz,s7.tar.gz}")
    write_file_to_path(installer_bat, sfc_output, 'sfc-standalone-install.bat')
    # WINDOWS
    # create an sfc installer bat script
    run_win = \
"""@ECHO OFF
SET SFC_DEPLOYMENT_DIR=%cd%
sfc-main\\bin\\sfc-main.bat -config %SFC_DEPLOYMENT_DIR%\\sfc_config_generated.json
"""\
    .format(ARTIFACT_BASE_URL=sfcArtifatctBaseURI, VERSION=sfcVersion, MODULES="sfc-main.tar.gz,debug-target.tar.gz,aws-sitewise-target.tar.gz,s7.tar.gz")
    write_file_to_path(run_win, sfc_output, 'sfc-standalone-runner.bat')


    return installer

def createSFCGreengrassCompRecipe(sfcVersion, compVersion, sfc_output, region, thingArn):
    # check if we have session creds... we need them for checking gg deployment config
    print('')
    print(bcolors.OKGREEN+'...Packaging Greengrass Deployment JSON at @PATH: '+str(sfc_output))
    print('')
    print('...Checking AWS session credentials'+bcolors.ENDC)
    if check_aws_creds() is False:
        print('No AWS session credentials available - exiting now!')
        exit(1)
    else:
        print('OK')
        print('')

    installer = createSFCInstallScript(sfcVersion, sfc_output)
    installer_base64 = base64.b64encode(installer.encode('ascii')).decode('ascii')


    # TODO: Maximum size of component recipe is 16KB -> Consider packing base64 strings into deployment config...
    # 
    # get the created sfc-config zip and base64-encode it...
    with open(sfc_output / "sfc-conf.zip", 'rb') as zip:
        bytes = zip.read()
    sfc_config_zip_base64 = base64.b64encode(bytes).decode('ascii')
    
    # now get comp template and fill it - write as file to output-dir
    with open(get_file_with_pathlib('templates/gg_comp.json.template'), 'r') as gg_template:
        recipe = json.load(gg_template)
    recipe['ComponentVersion'] = compVersion
    compFileName='sfc-greengrass-component-recipe-{compVersion}.json'.format(compVersion=compVersion)
    write_json_file_to_path(recipe, sfc_output, compFileName)

    # create Greengrass deployment config
    client = boto3.client('greengrassv2', region_name=region)
    
    try:
        gg_list_deployments = client.list_deployments(targetArn=thingArn)
    except client.exceptions.AccessDeniedException:
        print('Access denied for '+thingArn+' Does that arn exist? Also check your Session Credentials & IAM Role. Exiting now!')
        exit(1)
    
    #print(gg_list_deployments)
    gg_deploymentId = gg_list_deployments['deployments'][0]['deploymentId']
    gg_deployment = client.get_deployment(deploymentId=gg_deploymentId)
    #print(gg_deployment)

    gg_deployment['components']['custom.aws.sfc.runtime.with.config'] = {
                                 'componentVersion': compVersion,
                                 'configurationUpdate': {
                                     'reset': [""],
                                     'merge': '{\"sfcInstallerBase64Encoded\":\"'+installer_base64+'\",\"sfcConfigZipBase64Encoded\":\"'+sfc_config_zip_base64+'\"}'
                                  }
    }
    ## delete invalid entries
    del gg_deployment['creationTimestamp']
    del gg_deployment['ResponseMetadata']
    del gg_deployment['deploymentId']
    del gg_deployment['deploymentStatus']
    del gg_deployment['isLatestForTarget']
    del gg_deployment['revisionId']
    del gg_deployment['tags']

    
    deplFileName='sfc-greengrass-component-deployment-{compVersion}.json'.format(compVersion=compVersion)
    write_json_file_to_path(gg_deployment, sfc_output, deplFileName)


    # now create small helper scripts to register & deploy component
    gg_register = "aws greengrassv2 create-component-version --inline-recipe fileb://{recipeFile} --region {region}"\
        .format(recipeFile=str(sfc_output)+'/'+compFileName, region=region)
    gg_deploy = "aws greengrassv2 create-deployment --cli-input-json file://{deplFile} --region {region}"\
        .format(deplFile=str(sfc_output)+'/'+deplFileName, region=region)
    print(bcolors.OKGREEN + '-> Successfully created SFC Greengrass Component Recipe & Deployment Doc @PATH: '+str(sfc_output)+'/'+compFileName)
    print('')
    print('>> To register SFC Greengrass component run:')
    print('')
    print(gg_register)
    print('')
    print('>> To deploy SFC Greengrass component run:')
    print('')
    print(gg_deploy)
    print('')
    print(bcolors.ENDC)
    


    
def write_json_file_to_path(data, path, file_name):
    with open(path / file_name, 'w') as file_out:
        file_out.write(json.dumps(data, sort_keys = True, indent = 4))

def write_file_to_path(data, path, file_name):
    with open(path / file_name, 'w') as file_out:
        file_out.write(data)


def get_file_with_pathlib(file_name):
   script_dir = Path(__file__).resolve().parent
   file_path = script_dir / file_name
   return file_path

def check_aws_creds():
    sts = boto3.client('sts')
    try:
        sts.get_caller_identity()
        return True
    except botocore.exceptions.UnauthorizedSSOTokenError:
        return False
    except botocore.exceptions.NoCredentialsError:
        return False