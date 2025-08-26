# src/ui_viewer.py

import matplotlib.pyplot as plt
import numpy as np
import os
import math

from data_manager import DataManager
from dicom_loader import apply_windowing

class ImageViewerUI:
    def __init__(self, data_manager: DataManager):
        print("Inicializando UI de Classificação Simplificada...")
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
        self.fig.canvas.mpl_connect('close_event', self.on_close)

        self.data_manager.start_buffer_thread()

        if self.data_manager.get_total_navigable_folders() > 0:
            self.display_current_exam()
        else:
            self.display_message("Nenhuma pasta encontrada para os critérios de filtro.")

    def display_current_exam(self):
        """Busca e exibe a primeira imagem do exame atual."""
        details = self.data_manager.get_current_folder_details()
        if not details:
            # Esta verificação agora é feita no on_key_press, mas mantemos por segurança
            self.display_message("Fim da lista de exames.")
            return

        accession_number = details["accession_number"]
        print(f"Exibindo exame: {accession_number}")

        # Esta chamada ainda pode bloquear, mas o usuário já viu o feedback "Carregando..."
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
        """Manipulador para eventos de pressionamento de tecla."""
        if event.key == 'up':
            if self.data_manager.move_to_previous_folder():
                self.display_message("Carregando...")
                self.fig.canvas.flush_events() # Força a UI a redesenhar AGORA
                self.display_current_exam()
        elif event.key == 'down':
            if self.data_manager.move_to_next_folder():
                self.display_message("Carregando...")
                self.fig.canvas.flush_events() # Força a UI a redesenhar AGORA
                self.display_current_exam()
        elif event.key in ['1', '2', '3', '4', '5']:
            details = self.data_manager.get_current_folder_details()
            if not details: return
            
            accession_number = details["accession_number"]
            classification = int(event.key)
            
            # 1. Salva (rápido)
            self.data_manager.save_classification(accession_number, classification)
            
            # 2. Tenta avançar para o próximo exame
            if not self.data_manager.move_to_next_folder():
                self.display_message("Fim da lista de exames!")
                return
            
            # 3. Exibe feedback IMEDIATO e força o redesenho da UI
            self.display_message("Carregando...")
            self.fig.canvas.flush_events() # <<< O PONTO CHAVE DA MUDANÇA
            
            # 4. Agora, chama a função que pode demorar um pouco
            self.display_current_exam()

    def on_close(self, event):
        """Garante que a thread do buffer seja parada ao fechar a janela."""
        print("Janela fechada. Encerrando a aplicação...")
        self.data_manager.stop_buffer_thread()

    def show(self):
        """Mostra a janela da aplicação."""
        plt.show()