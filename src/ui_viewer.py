# src/ui_viewer.py

import cv2
import numpy as np
from data_manager import DataManager

class ImageViewerUI:
    def __init__(self, data_manager: DataManager):
        print("Inicializando UI com OpenCV (Modo On-Demand)...")
        self.data_manager = data_manager
        self.window_name = 'Ferramenta de Classificacao de Densidade Mamaria'
        
        self.classification_labels = {
            1: "1: Adiposa", 2: "2: Predominantemente Adiposa", 3: "3: Predominantemente Densa",
            4: "4: Densa", 5: "5: Pular / Problema"
        }

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 800, 1000)

    def display_current_exam(self):
        """Busca a imagem sob demanda e a exibe."""
        details = self.data_manager.get_current_folder_details()
        if not details:
            self.display_message("Fim da lista de exames!")
            cv2.waitKey(5000)
            return False

        accession_number = details["accession_number"]
        
        # --- MUDANÇA PRINCIPAL ---
        # Carrega a imagem do disco neste exato momento
        image_array = self.data_manager.load_single_exam(accession_number)
        # ---------------------------
        
        if image_array is None:
            self.display_message(f"Erro ao carregar imagem para:\n{accession_number}")
            cv2.waitKey(2000)
            return True

        image_to_display = cv2.cvtColor(image_array, cv2.COLOR_GRAY2BGR)
        self._draw_text_info(image_to_display, accession_number)
        cv2.imshow(self.window_name, image_to_display)
        return True

    def _draw_text_info(self, image, accession_number):
        font = cv2.FONT_HERSHEY_SIMPLEX; font_scale = 1.2; thickness = 2; line_type = cv2.LINE_AA
        total = self.data_manager.get_total_navigable_folders()
        current = self.data_manager.get_current_folder_index_display()
        info_text = f"Exame: {accession_number} ({current}/{total})"
        cv2.putText(image, info_text, (15, 45), font, font_scale, (255, 255, 255), thickness, line_type)
        classification = self.data_manager.get_classification(accession_number)
        if classification:
            label = self.classification_labels.get(classification, f"Classe: {classification}")
            status_text = f"Ja Classificado: {label}"
            cv2.putText(image, status_text, (15, image.shape[0] - 30), font, 1.4, (0, 255, 0), thickness + 1, line_type)

    def display_message(self, message: str):
        message_screen = np.zeros((600, 800, 3), dtype=np.uint8)
        y0, dy = 280, 50
        for i, line in enumerate(message.split('\n')):
            y = y0 + i * dy
            cv2.putText(message_screen, line, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow(self.window_name, message_screen)
    
    def show(self):
        if self.data_manager.get_total_navigable_folders() <= 0:
            self.display_message("Nenhuma pasta encontrada.")
            cv2.waitKey(3000)
            cv2.destroyAllWindows()
            return
            
        running = self.display_current_exam()
        while running:
            key = cv2.waitKey(0) & 0xFF
            if key == ord('q') or key == 27: running = False
            elif key == 82: # Seta Cima
                if self.data_manager.move_to_previous_folder(): running = self.display_current_exam()
            elif key == 84: # Seta Baixo
                if self.data_manager.move_to_next_folder(): running = self.display_current_exam()
            elif ord('1') <= key <= ord('5'):
                details = self.data_manager.get_current_folder_details()
                if details:
                    self.data_manager.save_classification(details["accession_number"], int(chr(key)))
                    if not self.data_manager.move_to_next_folder():
                        running = False
                        self.display_message("Fim da lista de exames!")
                        cv2.waitKey(5000)
                    else:
                        running = self.display_current_exam()
        cv2.destroyAllWindows()