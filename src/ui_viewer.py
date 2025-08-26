# src/ui_viewer.py

import matplotlib.pyplot as plt
import numpy as np
import os
import math

from data_manager import DataManager
from dicom_loader import apply_windowing

class ImageViewerUI:
    def __init__(self, data_manager: DataManager):
        print("Inicializando a nova UI de Classificação...")
        self.data_manager = data_manager

        # Dicionário para mapear a classificação numérica para um texto descritivo
        self.classification_labels = {
            1: "1: Adiposa",
            2: "2: Predominantemente Adiposa",
            3: "3: Predominantemente Densa",
            4: "4: Densa"
        }

        # Configuração da figura principal do Matplotlib
        self.fig = plt.figure(figsize=(12, 8), facecolor='darkgray')
        self.fig.canvas.manager.set_window_title('Ferramenta de Classificação de Densidade Mamária')

        # Conectar os eventos de teclado e fechamento da janela
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('close_event', self.on_close)

        # Inicia a thread de pré-carregamento de imagens
        self.data_manager.start_buffer_thread()

        # Verifica se há pastas para exibir e carrega o primeiro exame
        if self.data_manager.get_total_navigable_folders() > 0:
            self.display_current_exam()
        else:
            self.display_message("Nenhuma pasta encontrada para os critérios de filtro.")

    def display_current_exam(self):
        """
        Busca os dados do exame atual no buffer, calcula o layout do grid
        e exibe todas as imagens na tela.
        """
        details = self.data_manager.get_current_folder_details()
        if not details:
            self.display_message("Fim da lista de exames.")
            return

        accession_number = details["accession_number"]
        print(f"Exibindo exame: {accession_number}")

        # Busca os dados das imagens do buffer (pode esperar um pouco se não estiver pronto)
        image_data_list = self.data_manager.get_exam_data_from_buffer(accession_number)

        if not image_data_list:
            self.display_message(f"Erro ao carregar imagens para o exame:\n{accession_number}")
            return

        # Limpa a figura para redesenhar
        self.fig.clear()

        num_images = len(image_data_list)
        
        # --- Lógica para calcular o layout do grid ---
        if num_images <= 0:
            self.display_message(f"Nenhuma imagem encontrada para:\n{accession_number}")
            return
        elif num_images <= 4:
            rows, cols = (1, 3) if num_images == 3 else (math.ceil(num_images / 2), 2)
        else:
            cols = math.ceil(math.sqrt(num_images))
            rows = math.ceil(num_images / cols)
        
        # Cria os subplots (eixos) no grid calculado
        axes = self.fig.subplots(rows, cols).flatten()

        # Exibe cada imagem em seu respectivo subplot
        for i, (pixel_data, view_params) in enumerate(image_data_list):
            ax = axes[i]
            windowed_image = apply_windowing(
                pixel_data,
                view_params['wc'],
                view_params['ww'],
                view_params['photometric']
            )
            ax.imshow(windowed_image, cmap='gray')
            ax.axis('off')

        # Esconde os eixos que não foram utilizados
        for i in range(num_images, len(axes)):
            axes[i].axis('off')
        
        self.fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.95, wspace=0.05, hspace=0.05)

        # Adiciona informações de texto na tela
        self._display_exam_info(accession_number)

        # Atualiza o canvas da figura
        self.fig.canvas.draw_idle()

    def _display_exam_info(self, accession_number):
        """Exibe o AccessionNumber e a classificação (se houver) na tela."""
        # Informações do exame no canto superior esquerdo
        total_folders = self.data_manager.get_total_navigable_folders()
        current_index = self.data_manager.get_current_folder_index_display()
        info_text = f"Exame: {accession_number}  ({current_index}/{total_folders})"
        self.fig.text(0.02, 0.97, info_text, color='white', fontsize=12, weight='bold', ha='left', va='top')
        
        # Verifica e exibe a classificação existente no canto inferior esquerdo
        classification = self.data_manager.get_classification(accession_number)
        if classification:
            label = self.classification_labels.get(classification, f"Classe: {classification}")
            status_text = f"Já Classificado: {label}"
            self.fig.text(0.02, 0.03, status_text, color='lime', fontsize=14, weight='bold', ha='left', va='bottom',
                          bbox=dict(facecolor='black', alpha=0.6, pad=5))

    def display_message(self, message: str):
        """Exibe uma mensagem de status em tela cheia."""
        self.fig.clear()
        self.fig.text(0.5, 0.5, message, ha='center', va='center', color='white', fontsize=16)
        self.fig.canvas.draw_idle()

    def on_key_press(self, event):
        """Manipulador para eventos de pressionamento de tecla."""
        print(f"Tecla pressionada: {event.key}")
        
        # Navegação manual
        if event.key == 'up':
            if self.data_manager.move_to_previous_folder():
                self.display_current_exam()
        elif event.key == 'down':
            if self.data_manager.move_to_next_folder():
                self.display_current_exam()
        
        # Teclas de classificação
        elif event.key in ['1', '2', '3', '4']:
            details = self.data_manager.get_current_folder_details()
            if not details: return
            
            accession_number = details["accession_number"]
            classification = int(event.key)
            
            # 1. Salva a classificação
            self.data_manager.save_classification(accession_number, classification)
            
            # 2. Tenta avançar para o próximo exame
            if self.data_manager.move_to_next_folder():
                self.display_current_exam()
            else:
                # Se não houver próximo, exibe mensagem de fim
                self.display_message("Fim da lista de exames!")

    def on_close(self, event):
        """Garante que a thread do buffer seja parada ao fechar a janela."""
        print("Janela fechada. Encerrando a aplicação...")
        self.data_manager.stop_buffer_thread()

    def show(self):
        """Mostra a janela da aplicação."""
        plt.show()