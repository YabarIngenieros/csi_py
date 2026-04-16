from csi_py import CSIHandler

model = CSIHandler(program="ETABS", backend="auto")
model.open_and_connect()