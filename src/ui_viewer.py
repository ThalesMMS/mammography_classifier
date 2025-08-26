# src/ui_viewer.py

import matplotlib.pyplot as plt
import numpy as np
import os
import math
import cProfile, pstats # temporário

from data_manager import DataManager
from dicom_loader import apply_windowing

class ImageViewerUI:
    def __init__(self, data_manager: DataManager):
        print("Inicializando UI de Classificação...")
        self.data_manager = data_manager

        self.classification_labels = {
            1: "1: Adiposa",
            2: "2: Predominantemente Adiposa",
            3: "3: Predominantemente Densa",
            4: "4: Densa",
            5: "5: Pular / Problema"
        }

        self.fig = plt.figure(figsize=(10, 8), facecolor='darkgray')
        self.ax = None
        self.fig.canvas.manager.set_window_title('Ferramenta de Classificação de Densidade Mamária')

        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        # O 'on_close' não é mais necessário para parar a thread/pool

        # A UI só é chamada depois que tudo está na RAM
        if self.data_manager.get_total_navigable_folders() > 0:
            self.display_current_exam()
        else:
            self.display_message("Nenhuma pasta encontrada para os critérios de filtro.")

    def display_current_exam(self):
        """Busca e exibe a imagem do exame atual (já na RAM)."""
        details = self.data_manager.get_current_folder_details()
        if not details:
            self.display_message("Fim da lista de exames.")
            return

        accession_number = details["accession_number"]
        image_data = self.data_manager.get_exam_data_from_buffer(accession_number)
        
        self.fig.clear()

        if not image_data:
            self.display_message(f"Nenhuma imagem pôde ser carregada para:\n{accession_number}")
            return

        self.ax = self.fig.add_subplot(1, 1, 1)
        
        pixel_data, view_params = image_data
        windowed_image = apply_windowing(
            pixel_data, view_params['wc'], view_params['ww'], view_params['photometric']
        )
        self.ax.imshow(windowed_image, cmap='gray')
        self.ax.axis('off')
        
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        self._display_exam_info(accession_number)
        self.fig.canvas.draw_idle()

    def _display_exam_info(self, accession_number):
        """Exibe o AccessionNumber e a classificação (se houver) na tela."""
        total_folders = self.data_manager.get_total_navigable_folders()
        current_index = self.data_manager.get_current_folder_index_display()
        info_text = f"Exame: {accession_number}  ({current_index}/{total_folders})"
        self.fig.text(0.02, 0.97, info_text, color='white', fontsize=12, weight='bold', ha='left', va='top',
                      bbox=dict(facecolor='black', alpha=0.5))
        
        classification = self.data_manager.get_classification(accession_number)
        if classification:
            label = self.classification_labels.get(classification, f"Classe: {classification}")
            status_text = f"Já Classificado: {label}"
            self.fig.text(0.02, 0.03, status_text, color='lime', fontsize=14, weight='bold', ha='left', va='bottom',
                          bbox=dict(facecolor='black', alpha=0.6))

    def display_message(self, message: str):
        """Exibe uma mensagem de status em tela cheia."""
        self.fig.clear()
        self.fig.text(0.5, 0.5, message, ha='center', va='center', color='white', fontsize=16)
        self.fig.canvas.draw_idle()

    def on_key_press(self, event):
        """Manipulador para eventos de pressionamento de tecla (agora sem 'Carregando...')."""
        
        # --- INÍCIO DO CÓDIGO DE PROFILING ---
        profiler = cProfile.Profile()
        profiler.enable()
        # ------------------------------------
        
        if event.key == 'up':
            if self.data_manager.move_to_previous_folder():
                self.display_current_exam()
        elif event.key == 'down':
            if self.data_manager.move_to_next_folder():
                self.display_current_exam()
        elif event.key in ['1', '2', '3', '4', '5']:
            details = self.data_manager.get_current_folder_details()
            if not details: return
            
            accession_number = details["accession_number"]
            classification = int(event.key)
            
            self.data_manager.save_classification(accession_number, classification)
            
            if not self.data_manager.move_to_next_folder():
                self.display_message("Fim da lista de exames!")
            else:
                self.display_current_exam()
        
        # --- FIM DO CÓDIGO DE PROFILING ---
        profiler.disable()
        print("\n--- ANÁLISE DE PERFORMANCE DO ÚLTIMO CLIQUE ---")
        stats = pstats.Stats(profiler).sort_stats('tottime') # Ordena pelo tempo gasto DENTRO de cada função
        stats.print_stats(15) # Mostra as 15 funções mais lentas
        # ----------------------------------

    def show(self):
        """Mostra a janela da aplicação."""
        plt.show()