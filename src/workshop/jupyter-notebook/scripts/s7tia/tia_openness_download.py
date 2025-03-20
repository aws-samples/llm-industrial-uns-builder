def preconfigure_download(download_configuration):
   
    if (isinstance(download_configuration, dl.Configurations.StopModules)):
        download_configuration.CurrentSelection = dl.Configurations.StopModulesSelections.StopAll
    
    elif (isinstance(download_configuration, dl.Configurations.AlarmTextLibrariesDownload)):
        download_configuration.CurrentSelection = dl.Configurations.AlarmTextLibrariesDownloadSelections.ConsistentDownload

    elif (isinstance(download_configuration, dl.Configurations.BlockBindingPassword)):
        password = None #update if applicable
        download_configuration.SetPassword(password)                        

    elif (isinstance(download_configuration, dl.Configurations.CheckBeforeDownload)):
        download_configuration.Checked = true

    elif (isinstance(download_configuration, dl.Configurations.ConsistentBlocksDownload)):
        download_configuration.CurrentSelection = dl.Configurations.ConsistentBlocksDownloadSelections.ConsistentDownload

    elif (isinstance(download_configuration, dl.Configurations.ModuleWriteAccessPassword)):
        password = None;  #update if applicable
        download_configuration.SetPassword(password)
            
    elif (isinstance(download_configuration, dl.Configurations.OverwriteSystemData)):
        download_configuration.CurrentSelection = dl.Configurations.OverwriteSystemDataSelections.Overwrite;
        
    else:
        print (f"unknown download configuration: {type(download_configuration)}")


def postconfigure_download(download_configuration):
    
    if (isinstance(download_configuration, dl.Configurations.StartModules)):
        download_configuration.CurrentSelection = dl.Configurations.StartModulesSelections.StartModule
    
    else:
        print (f"unknown download configuration :{type(download_configuration)}")