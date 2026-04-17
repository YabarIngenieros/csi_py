from csi_py import CSIHandler

model = CSIHandler(program="ETABS", backend="auto")
model.connect_open_instance()
print(model.get_section_by_label('B37',story='Story1'))