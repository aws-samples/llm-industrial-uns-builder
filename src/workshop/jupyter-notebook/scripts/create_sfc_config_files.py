import click
from pathlib import Path
from s7tia import automationml2sw
from sfc import s7tia2sfc

@click.command()
@click.option('--region', required=True, default='us-east-1', show_default=True, help='AWS Region Code, used for Regional Ingestion Targets')
@click.option('--credentialprovider', required=True, show_default=True, default='ENV_SESSION_CREDENTIALS', type=click.Choice(['AWS_IOT_CERT', 'ENV_SESSION_CREDENTIALS'], case_sensitive=False), help='Session credentials for targets accessing AWS Services - either aws-iot-cert based (Greengrass or thing cert.) or standard chain creds.')
# OPTIONAL
@click.option("--creategreengrassinstaller", is_flag=True, show_default=True, default=False, help="Packs the generated SFC-Config together with SFC-Runtime into an inline Greengrass v2 component (plus aws-cli script for component registration)")
@click.option("--thingarn", required=False, default='arn:aws:iot:us-east-1:123456789012:thing/MyThing', help='ARN of the (Greengrass Core) IoT thing')
@click.option('--greengrasscompversion', required=False, default='1.0.1', show_default=True, help='Semver Version of created Greengrass Component.')
@click.option('--iotcredentialendpoint', required=False, help='Use when credentialprovider is AWS_IOT_CERT! e.g. < ID >.credentials.iot.< YOUR REGION >.amazonaws.com')
@click.option('--rolealias', required=False, help='Use when credentialprovider is AWS_IOT_CERT! < ROLE EXCHANGE ALIAS, e.g.GreengrassV2TokenExchangeRoleAlias >')
@click.option('--thingname', required=False, help='Use when credentialprovider is AWS_IOT_CERT! < THING NAME > e.g. GreengrassCore-1')
@click.option('--certfilepath', required=False, help='Use when credentialprovider is AWS_IOT_CERT! < PATH TO DEVICE CERTIFICATE .crt FILE >')
@click.option('--privatekeyfilepath', required=False, help='Use when credentialprovider is AWS_IOT_CERT! < PATH TO PRIVATE KEY .key FILE >')
@click.option('--rootcafilepath', required=False, help='Use when credentialprovider is AWS_IOT_CERT! < PATH TO ROOT CERTIFICATE .pem FILE >')
@click.option('--greengrasspath', required=False, show_default=True, default='/greengrass/v2', help='Use when credentialprovider is AWS_IOT_CERT! e.g. /greengrass/v2')

def main(region, credentialprovider, creategreengrassinstaller, thingarn, greengrasscompversion, iotcredentialendpoint, rolealias, thingname, certfilepath, privatekeyfilepath, rootcafilepath, greengrasspath):
    project_name = "CarFactory"
    tia_export_dir = Path("C://Users//Administrator//Documents//TIA-Export")
    Path("../imports/sfc").mkdir(parents=True, exist_ok=True)
    sfc_output = Path("../imports/sfc", project_name)
    sfc_output.mkdir(parents=True, exist_ok=True)
    devices = automationml2sw.get_device_and_db_info(tia_export_dir)

    iot_cert_params={}
    iot_cert_params.update({'endpoint':iotcredentialendpoint})
    iot_cert_params.update({'rolealias':rolealias})
    iot_cert_params.update({'thingname':thingname})
    iot_cert_params.update({'iotcredentialendpoint':iotcredentialendpoint})
    iot_cert_params.update({'certificatefilepath':certfilepath})
    iot_cert_params.update({'keyfilepath':privatekeyfilepath})
    iot_cert_params.update({'rootcafilepath':rootcafilepath})
    iot_cert_params.update({'greengrasspath':greengrasspath})
    

    s7tia2sfc.create_sfc_import_files(devices, sfc_output, region, credentialprovider, creategreengrassinstaller, thingarn, greengrasscompversion, iot_cert_params)


if __name__ == '__main__':
    main()