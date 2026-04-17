from csi_py import CSIHandler

model = CSIHandler(program="ETABS", backend="auto")
model.connect_open_instance()
print(model.get_frames_at_intersection("1", "A"))