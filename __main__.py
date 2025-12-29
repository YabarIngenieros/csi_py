from csi_py import CSIHandler

import time
etabs = CSIHandler() # inicializando el objeto
etabs.connect_open_instance()
to = time.time()

# etabs.add_tee_SD_sections('T1','4000Psi',0.85,0.85,0.4)
# etabs.add_tee_SD_sections('T2','4000Psi',0.95,0.85,0.4)
# etabs.add_tee_SD_sections('T3','4000Psi',0.95,0.95,0.4)
# etabs.add_tee_SD_sections('T4','4000Psi',1.05,0.85,0.4)
# etabs.apply_tee_sections()

etabs.add_tee_SD_sections(['T5','T2','T3','T4'],['4000Psi']*4,[0.85,0.95,0.95,1.05],
                          (0.85,0.85,0.95,0.85),[0.4]*4)

#etabs.set_grid_sitem([3,3.5,4,4.2],[4,4.2,3.8,2.4])

#etabs.set_grid_sitem([0,6,12,18],[0,6,12,18],spacing=False)


# etabs.add_line_bar_to_section('sec_Tee','A615Gr60',[-0.325,0.225],[0.325,0.225],18,0.150)
print(time.time()-to)
# to = time.time()
# print(etabs_model.area_properties)
# print(time.time()-to)