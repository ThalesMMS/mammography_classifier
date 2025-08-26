import pydicom

# Carrega o arquivo DICOM
ds = pydicom.dcmread("src/img.dcm", force=True)

# Acessa as dimensões da imagem
rows = ds.Rows        # (0028,0010)
columns = ds.Columns  # (0028,0011)

print(f"Dimensão da imagem: {columns} x {rows} pixels")