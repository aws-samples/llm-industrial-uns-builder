# Build an AMI for TIA portal

## Prerequisites

You need an account for Siemens SiePortal https://sieportal.siemens.com/en-us/home in oder to download the required software.

## Step-by-Step Guide

1. Boot a Windows EC2 instance that has access to the internet
2. Download The TIA DVDs (we tested V19) inside the EC2 instance from here https://support.industry.siemens.com/cs/document/109820994/simatic-step-7-inkl-safety-s7-plcsim-and-wincc-v19-trial-download?dti=0&lc=en-US
3. Install TIA with mounting the DVDs
4. Install Python
5. Create an AMI from the EC2 instance

## Automated install

TODO