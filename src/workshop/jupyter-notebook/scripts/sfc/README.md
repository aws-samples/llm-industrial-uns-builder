SFC config & Runtime Creation
=============================

The scripts [`src/create_sfc_config_files.py`](../create_sfc_config_files.py) and [`src/sfc/s7tia2sfc.py`](s7tia2sfc.py) invoke the *get_device_and_db_info()* methods from src/s7tia (to get a json dict representation of the TIA exports) and create a valid SFC config package stored in `imports/sfc`.

## Features 

The script provides automations to get up a SFC runtime quickly. Available automations are:
- `Config Package` - a collection of sfc json config files (files also as zipped archive)
- Standalone `runtime script` - to install all SFC binaries & execute SFC runtime
- Optional `Greengrass Component Recipe & Deployment file` as JSON - a ready to use Component recipe for registering/deploying to Greengrass Cloud 
- Choice of `Credential Handling` strategy - either via IoT Certificate (mTLS/X.509) or via environment session credentials




## Quickstart

Starting the script without `--parameters` will use all defaults...

```sh
(.venv) ~/workspace/SFC/integrated-automation/src: python3 create_sfc_config_files.py
...
...
++++++++++++++
+ SFC CONFIG +
++++++++++++++

...Packaging at @PATH: ../imports/sfc/CarFactory

-> Successfully created SFC Config Zip Package @PATH: ../imports/sfc/CarFactory/sfc-conf.zip
-> Successfully created SFC Standalone Installer @PATH: ../imports/sfc/CarFactory/sfc-standalone-install.sh

>> To install SFC standalone run:
cd ../imports/sfc/CarFactory && ./sfc-standalone-install.sh

>> To execute SFC standalone run:
cd ../imports/sfc/CarFactory && export SFC_DEPLOYMENT_DIR=$(pwd) &&./sfc-main/bin/sfc-main -config sfc_config_generated.json

```

## Usage

### I want to create...
  - **`Standalone SFC Runtime with Config` for a host with AWS credentials available & set?**

    ```sh
    python3 create_sfc_config_files.py --region us-east-1
    # that one will create a standalone config & runtime for ingestion at selected region
    # OUTPUTS: sfc-config package, sfc-install script & standalone run commands
    ```

  - **`Greengrass Component with Config & Deploy/Run` it to a Core device?**

    ```sh
      python3 create_sfc_config_files.py \
      --region us-east-1 \
      --creategreengrassinstaller \
      --greengrasscompversion 1.0.0 \
      --thingarn arn:aws:iot:us-east-1:729641235348:thing/GatewayGreengrassCoreDevice-IAD1
      # that one will create a greengrass recipe & a deployment file
      # OUTPUTS: sfc-config package, gg recipe, gg-deployment & aws cli commands
      #
      # register component...
      aws greengrassv2 create-component-version \
      --inline-recipe fileb://../imports/sfc/CarFactory/sfc-greengrass-component-recipe-1.0.0.json \
      --region us-east-1
      # deploy to gg a core device...
      aws greengrassv2 create-deployment \
      --cli-input-json file://../imports/sfc/CarFactory/sfc-greengrass-component-deployment-1.0.0.json
    ```

  - **Standalone SFC Runtime using an `AWS IoT certificate as Credential Provider`?**
    ```sh
      python3 create_sfc_config_files.py \
      --region us-east-1 \
      --credentialprovider AWS_IOT_CERT \
      --iotcredentialendpoint https://your_aws_account_specific_prefix.credentials.iot.your-region.amazonaws.com \
      --thingname myThing01 \
      --certfilepath /path/to/x509.crt \
      --privatekeyfilepath /path/to/key.key \
      --rootcafilepath /path/to/root-ca.pem
      # that one will create a standalone SFC config & runtime with a AwsIotCredentialProviderClients section
      # plus SFC AWS-Targets (Sitewise) using that credential provider
      # OUTPUTS: sfc-config package, sfc-install script & standalone run commands
    ```
  


## All script options


```txt
python3 create_sfc_config_files.py --help
Usage: create_sfc_config_files.py [OPTIONS]

Options:
  --region TEXT                   AWS Region Code, used for Regional Ingestion
                                  Targets  [default: us-east-1; required]
  --credentialprovider [AWS_IOT_CERT|ENV_SESSION_CREDENTIALS]
                                  Session credentials for targets accessing
                                  AWS Services - either aws-iot-cert based
                                  (Greengrass or thing cert.) or standard
                                  chain creds.  [default:
                                  ENV_SESSION_CREDENTIALS; required]
  --creategreengrassinstaller     Packs the generated SFC-Config together with
                                  SFC-Runtime into an inline Greengrass v2
                                  component (plus aws-cli script for component
                                  registration)
  --thingarn TEXT                 ARN of the (Greengrass Core) IoT thing
  --greengrasscompversion TEXT    Semver Version of created Greengrass
                                  Component.  [default: 1.0.1]
  --iotcredentialendpoint TEXT    Use when credentialprovider is AWS_IOT_CERT!
                                  e.g. < ID >.credentials.iot.< YOUR REGION
                                  >.amazonaws.com
  --rolealias TEXT                Use when credentialprovider is AWS_IOT_CERT!
                                  < ROLE EXCHANGE ALIAS,
                                  e.g.GreengrassV2TokenExchangeRoleAlias >
  --thingname TEXT                Use when credentialprovider is AWS_IOT_CERT!
                                  < THING NAME > e.g. GreengrassCore-1
  --certfilepath TEXT             Use when credentialprovider is AWS_IOT_CERT!
                                  < PATH TO DEVICE CERTIFICATE .crt FILE >
  --privatekeyfilepath TEXT       Use when credentialprovider is AWS_IOT_CERT!
                                  < PATH TO PRIVATE KEY .key FILE >
  --rootcafilepath TEXT           Use when credentialprovider is AWS_IOT_CERT!
                                  < PATH TO ROOT CERTIFICATE .pem FILE >
  --greengrasspath TEXT           Use when credentialprovider is AWS_IOT_CERT!
                                  e.g. /greengrass/v2  [default:
                                  /greengrass/v2]
  --help                          Show this message and exit.
```
