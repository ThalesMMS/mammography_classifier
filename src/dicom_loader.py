# src/dicom_loader.py

import pydicom
import numpy as np
import os

class DicomImageLoader:
    def __init__(self):
        pass # Nenhuma inicialização complexa necessária por enquanto

    def load_dicom_data(self, dicom_path: str) -> tuple[np.ndarray | None, dict | None]:
        """
        Carrega um arquivo DICOM, aplica rescale slope/intercept e determina
        os parâmetros de janelamento.

        Args:
            dicom_path (str): O caminho para o arquivo .dcm.

        Returns:
            tuple[np.ndarray | None, dict | None]: 
             - O array de pixels após rescale (float32), ou None se erro.
             - Um dicionário com parâmetros de visualização {'wc', 'ww', 'photometric', 'source'}, 
               ou None se erro. 'source' indica se WC/WW vieram do 'DICOM' ou foram 'Calculated'.
        """
        try:
            ds = pydicom.dcmread(dicom_path, force=True) 
            
            if not hasattr(ds, 'PixelData'):
                 print(f"Erro: O arquivo DICOM '{os.path.basename(dicom_path)}' foi lido (force=True), mas não contém PixelData.")
                 return None, None
                 
            pixel_array = ds.pixel_array.astype(np.float32) 

            # 1. Aplicar Rescale Slope e Intercept
            rescale_slope = 1.0
            rescale_intercept = 0.0
            if hasattr(ds, 'RescaleSlope') and hasattr(ds, 'RescaleIntercept'):
                # Garantir que sejam tratados como float
                try:
                    rescale_slope = float(ds.RescaleSlope)
                    rescale_intercept = float(ds.RescaleIntercept)
                    pixel_array = pixel_array * rescale_slope + rescale_intercept
                except (ValueError, TypeError):
                     print(f"Aviso: Não foi possível converter RescaleSlope/Intercept para float em '{os.path.basename(dicom_path)}'. Usando valores padrão 1.0/0.0.")
                     # Mantém pixel_array como estava se a conversão falhar

            # 2. Determinar Parâmetros de Janelamento e Photometric Interpretation
            window_center = None
            window_width = None
            source = "Calculated" # Assume calculado por padrão

            if hasattr(ds, 'WindowCenter'):
                wc_val = ds.WindowCenter
                try:
                    # Usa o primeiro valor se for multivalorado
                    window_center = float(wc_val[0]) if isinstance(wc_val, pydicom.multival.MultiValue) else float(wc_val)
                except (ValueError, TypeError):
                     print(f"Aviso: Não foi possível converter WindowCenter ('{wc_val}') para float em '{os.path.basename(dicom_path)}'.")
            
            if hasattr(ds, 'WindowWidth'):
                ww_val = ds.WindowWidth
                try:
                    # Usa o primeiro valor se for multivalorado
                    window_width = float(ww_val[0]) if isinstance(ww_val, pydicom.multival.MultiValue) else float(ww_val)
                except (ValueError, TypeError):
                     print(f"Aviso: Não foi possível converter WindowWidth ('{ww_val}') para float em '{os.path.basename(dicom_path)}'.")

            photometric_interpretation = "MONOCHROME2" # Padrão
            if hasattr(ds, 'PhotometricInterpretation'):
                photometric_interpretation = ds.PhotometricInterpretation

            # Se WC/WW foram obtidos com sucesso do DICOM, marcar a fonte
            if window_center is not None and window_width is not None:
                source = "DICOM"
            else:
                # Calcular se não foram encontrados ou foram inválidos
                print(f"Info: Calculando WindowCenter/WindowWidth a partir de min/max para '{os.path.basename(dicom_path)}'.")
                min_val = np.min(pixel_array)
                max_val = np.max(pixel_array)
                window_center = (max_val + min_val) / 2.0
                window_width = max_val - min_val
                if window_width <= 0:
                    window_width = 1 # Evitar divisão por zero ou WW negativo

            view_params = {
                "wc": window_center,
                "ww": window_width,
                "photometric": photometric_interpretation,
                "source": source 
            }
            
            return pixel_array, view_params # Retorna array float e parâmetros

        except FileNotFoundError:
            print(f"Erro: Arquivo DICOM não encontrado em '{dicom_path}'")
            return None, None
        except Exception as e:
            print(f"Erro ao carregar ou processar o arquivo DICOM '{os.path.basename(dicom_path)}': {e}")
            # import traceback
            # traceback.print_exc() 
            return None, None

# Função auxiliar para aplicar janelamento (pode ser movida para utils.py ou ui_viewer.py depois)
def apply_windowing(image: np.ndarray, wc: float, ww: float, photometric: str) -> np.ndarray:
    """Aplica janelamento e retorna imagem uint8."""
    img_min = wc - ww / 2.0
    img_max = wc + ww / 2.0
    
    windowed_image = np.clip(image, img_min, img_max)

    if img_max > img_min:
        windowed_image = (windowed_image - img_min) / (img_max - img_min)
    else:
        windowed_image = np.zeros_like(windowed_image)

    if photometric == "MONOCHROME1":
        windowed_image = 1.0 - windowed_image
        
    windowed_image_uint8 = (windowed_image * 255.0).astype(np.uint8)
    return windowed_image_uint8


# Exemplo de como usar (apenas para teste):
# if __name__ == '__main__':
#     project_root = os.path.dirname(os.getcwd()) 
#     archive_folder_path = os.path.join(project_root, "archive")
    
#     test_dicom_path = None
#     # Bloco para encontrar arquivo de teste (igual ao anterior)
#     try:
#         from data_manager import DataManager 
#         dm = DataManager(archive_folder_path)
#         valid_folders = dm._all_valid_patient_folders 
#         if valid_folders:
#             first_folder = valid_folders[0]
#             dicoms_in_first_folder = dm.get_dicom_files(first_folder)
#             if dicoms_in_first_folder:
#                 test_dicom_path = os.path.join(archive_folder_path, first_folder, dicoms_in_first_folder[0])
#                 print(f"Usando arquivo DICOM para teste: {test_dicom_path}")
#             else: print(f"Nenhum arquivo DICOM encontrado na pasta de teste: {first_folder}")
#         else: print("Nenhuma pasta válida encontrada pelo DataManager para obter um arquivo DICOM de teste.")
#     except Exception as e:
#         print(f"Não foi possível usar o DataManager para encontrar um arquivo DICOM de teste: {e}")

#     if test_dicom_path and os.path.exists(test_dicom_path):
#         loader = DicomImageLoader()
#         # Agora recebe a tupla: (array_float, view_params)
#         pixel_data_float, view_params = loader.load_dicom_data(test_dicom_path)

#         if pixel_data_float is not None and view_params is not None:
#             print(f"Dados DICOM carregados. Dimensões: {pixel_data_float.shape}, Tipo: {pixel_data_float.dtype}")
#             print(f"Valores min/max dos dados brutos (após rescale): {np.min(pixel_data_float):.2f}, {np.max(pixel_data_float):.2f}")
#             print(f"Parâmetros de visualização determinados:")
#             print(f"  Window Center (WC): {view_params['wc']:.2f}")
#             print(f"  Window Width (WW): {view_params['ww']:.2f}")
#             print(f"  Photometric Int.: {view_params['photometric']}")
#             print(f"  Fonte WC/WW: {view_params['source']}") # <<< Indica se veio do DICOM ou calculado

#             # Aplicar janelamento aqui, APENAS para o teste de visualização
#             image_to_display = apply_windowing(pixel_data_float, view_params['wc'], view_params['ww'], view_params['photometric'])
#             print(f"Valores min/max da imagem processada (uint8): {np.min(image_to_display)}, {np.max(image_to_display)}")

#             try:
#                 import matplotlib.pyplot as plt
#                 plt.imshow(image_to_display, cmap='gray') # Exibe a imagem uint8 processada
#                 plt.title(f"DICOM: {os.path.basename(test_dicom_path)} (WC/WW: {view_params['source']})")
#                 plt.colorbar()
#                 plt.show()
#             except ImportError:
#                 print("Matplotlib não está instalado. Não é possível exibir a imagem de teste.")
#             except Exception as e:
#                 print(f"Erro ao tentar exibir imagem com Matplotlib: {e}")
#         else:
#             print("Falha ao carregar os dados DICOM.")
#     # Restante do bloco de erro (igual ao anterior)
#     elif test_dicom_path:
#         print(f"Caminho de teste especificado, mas arquivo DICOM não encontrado: {test_dicom_path}")
#     else:
#         print("Caminho do arquivo DICOM de teste não definido ou DataManager não pôde fornecer um.")

# Exemplo de como usar (apenas para teste):
if __name__ == '__main__':
    project_root = os.path.dirname(os.getcwd()) 
    archive_folder_path = os.path.join(project_root, "archive")
    
    test_dicom_path = None
    # Bloco para encontrar arquivo de teste (igual ao anterior)
    try:
        from data_manager import DataManager 
        dm = DataManager(archive_folder_path)
        valid_folders = dm._all_valid_patient_folders 
        if valid_folders:
            first_folder = valid_folders[0]
            dicoms_in_first_folder = dm.get_dicom_files(first_folder)
            if dicoms_in_first_folder:
                test_dicom_path = os.path.join(archive_folder_path, first_folder, dicoms_in_first_folder[0])
                print(f"Usando arquivo DICOM para teste: {test_dicom_path}")
            else: print(f"Nenhum arquivo DICOM encontrado na pasta de teste: {first_folder}")
        else: print("Nenhuma pasta válida encontrada pelo DataManager para obter um arquivo DICOM de teste.")
    except Exception as e:
        print(f"Não foi possível usar o DataManager para encontrar um arquivo DICOM de teste: {e}")

    if test_dicom_path and os.path.exists(test_dicom_path):
        loader = DicomImageLoader()
        pixel_data_float, view_params = loader.load_dicom_data(test_dicom_path)

        if pixel_data_float is not None and view_params is not None:
            print(f"Dados DICOM carregados. Dimensões: {pixel_data_float.shape}, Tipo: {pixel_data_float.dtype}")
            print(f"Valores min/max dos dados brutos (após rescale): {np.min(pixel_data_float):.2f}, {np.max(pixel_data_float):.2f}")
            print(f"Parâmetros de visualização determinados:")
            print(f"  Window Center (WC): {view_params['wc']:.2f}")
            print(f"  Window Width (WW): {view_params['ww']:.2f}")
            print(f"  Photometric Int.: {view_params['photometric']}")
            print(f"  Fonte WC/WW: {view_params['source']}") 

            # --- MODIFICAÇÃO PARA EXIBIR FLOAT DIRETAMENTE ---
            print("\nExibindo imagem float diretamente com matplotlib (usando vmin/vmax)...")

            # Calcular vmin e vmax a partir de WC/WW
            wc = view_params['wc']
            ww = view_params['ww']
            vmin = wc - ww / 2.0
            vmax = wc + ww / 2.0

            # Escolher o colormap adequado (invertido para MONOCHROME1)
            cmap_to_use = 'gray'
            if view_params['photometric'] == 'MONOCHROME1':
                cmap_to_use = 'gray_r' # '_r' indica reverso

            try:
                import matplotlib.pyplot as plt
                # Passar o array float diretamente, junto com vmin, vmax e cmap
                plt.imshow(pixel_data_float, cmap=cmap_to_use, vmin=vmin, vmax=vmax) 
                plt.title(f"DICOM Float: {os.path.basename(test_dicom_path)} (WC/WW: {view_params['source']})")
                plt.colorbar() # A colorbar agora mostrará os valores float originais (pós-rescale)
                plt.show()
            except ImportError:
                print("Matplotlib não está instalado. Não é possível exibir a imagem de teste.")
            except Exception as e:
                print(f"Erro ao tentar exibir imagem com Matplotlib: {e}")
            # --- FIM DA MODIFICAÇÃO ---

        else:
            print("Falha ao carregar os dados DICOM.")
    # Restante do bloco de erro (igual ao anterior)
    elif test_dicom_path:
        print(f"Caminho de teste especificado, mas arquivo DICOM não encontrado: {test_dicom_path}")
    else:
        print("Caminho do arquivo DICOM de teste não definido ou DataManager não pôde fornecer um.")