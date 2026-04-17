from csi_py import CSIHandler

model = CSIHandler(program="ETABS", backend="auto")
model.connect_open_instance()
print(model.grid_lines)