# src/dicom_loader.py

import pydicom
import numpy as np
import os

def load_dicom_task(dicom_path, accession_number, shared_buffer):
    """
    Função 'trabalhadora' projetada para rodar em um processo separado.
    Carrega um arquivo DICOM e coloca o resultado em um dicionário compartilhado.
    """
    image_data = None
    try:
        ds = pydicom.dcmread(dicom_path, force=True)
        
        if hasattr(ds, 'PixelData'):
            pixel_array = ds.pixel_array.astype(np.float32)

            # Aplica Rescale Slope e Intercept se existirem
            if hasattr(ds, 'RescaleSlope') and hasattr(ds, 'RescaleIntercept'):
                slope = float(ds.RescaleSlope)
                intercept = float(ds.RescaleIntercept)
                if slope != 1.0 or intercept != 0.0:
                    pixel_array = pixel_array * slope + intercept

            # Determina os parâmetros de janelamento (Windowing)
            window_center, window_width = None, None
            if hasattr(ds, 'WindowCenter'):
                wc_val = ds.WindowCenter
                window_center = float(wc_val[0]) if isinstance(wc_val, pydicom.multival.MultiValue) else float(wc_val)
            if hasattr(ds, 'WindowWidth'):
                ww_val = ds.WindowWidth
                window_width = float(ww_val[0]) if isinstance(ww_val, pydicom.multival.MultiValue) else float(ww_val)

            # Se não houver parâmetros de janelamento, calcula a partir dos pixels
            if window_center is None or window_width is None:
                min_val, max_val = np.min(pixel_array), np.max(pixel_array)
                window_center = (max_val + min_val) / 2.0
                window_width = max_val - min_val
                if window_width <= 0: window_width = 1

            photometric = ds.PhotometricInterpretation if hasattr(ds, 'PhotometricInterpretation') else "MONOCHROME2"
            view_params = {"wc": window_center, "ww": window_width, "photometric": photometric}
            image_data = (pixel_array, view_params)

    except Exception as e:
        print(f"[Processo-{os.getpid()}] Erro ao carregar {os.path.basename(dicom_path)}: {e}")
        image_data = None # Falha no carregamento
    
    # Coloca o resultado (dados da imagem ou None) no dicionário compartilhado
    shared_buffer[accession_number] = image_data

def apply_windowing(image: np.ndarray, wc: float, ww: float, photometric: str) -> np.ndarray:
    """Aplica janelamento e retorna imagem uint8. (Função inalterada)"""
    img_min = wc - ww / 2.0
    img_max = wc + ww / 2.0
    
    windowed_image = np.clip(image, img_min, img_max)

    if img_max > img_min:
        windowed_image = (windowed_image - img_min) / (img_max - img_min)
    else:
        windowed_image = np.zeros_like(windowed_image)

    if photometric == "MONOCHROME1":
        windowed_image = 1.0 - windowed_image
        
    return (windowed_image * 255.0).astype(np.uint8)