from csi_py import CSIHandler

import time
etabs = CSIHandler() # inicializando el objeto
etabs.connect_open_instance()
to = time.time()
# etabs.add_tee_SD_section('T1','4000Psi',0.85,0.85,0.4)
# etabs.add_tee_SD_section('T2','4000Psi',0.95,0.85,0.4)
# etabs.add_tee_SD_section('T3','4000Psi',0.95,0.95,0.4)
# etabs.add_tee_SD_section('T4','4000Psi',1.05,0.85,0.4)
etabs.add_line_bar_to_section('T1','A615Gr60',(0.05,0.375),(0.80,0.037),'8',0.15)
etabs.apply_edited_table()


# etabs.add_line_bar_to_section('sec_Tee','A615Gr60',[-0.325,0.225],[0.325,0.225],18,0.150)
print(time.time()-to)
# to = time.time()
# print(etabs_model.area_properties)
# print(time.time()-to)