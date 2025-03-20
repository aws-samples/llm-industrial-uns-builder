import plcsim_helper as plcsim
import window_automation
window_automation.start_plcsim_gui()
plcsim.load_plcsim_library()
plcsim.power_off_all_plcs()
plcsim.delete_all_plcs()
plcsim.set_up_all_plcs()