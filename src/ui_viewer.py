# src/ui_viewer.py

import cv2
import numpy as np
from data_manager import DataManager

class ImageViewerUI:
    def __init__(self, data_manager: DataManager):
        print("Inicializando UI Otimizada com OpenCV...")
        self.data_manager = data_manager
        self.window_name = 'Ferramenta de Classificacao de Densidade Mamaria'
        
        self.classification_labels = {
            1: "1: Adiposa", 2: "2: Predominantemente Adiposa", 3: "3: Predominantemente Densa",
            4: "4: Densa", 5: "5: Pular / Problema"
        }

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_ASPECT_RATIO, cv2.WINDOW_KEEPRATIO)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_AUTOSIZE, cv2.WINDOW_AUTOSIZE)
        cv2.resizeWindow(self.window_name, 800, 1000)

    def display_current_exam(self):
        """Busca a imagem e a exibe na janela do OpenCV, com aspect ratio corrigido."""
        details = self.data_manager.get_current_folder_details()
        if not details:
            self.display_message("Fim da lista de exames!")
            cv2.waitKey(5000)
            return False

        accession_number = details["accession_number"]
        image_array = self.data_manager.get_exam_data_from_buffer(accession_number)
        
        if image_array is None:
            self.display_message(f"Erro ao carregar imagem para:\n{accession_number}")
            cv2.waitKey(2000)
            return True
        
        # --- CORREÇÃO 1: ASPECT RATIO E TELA PRETA ---
        # Obtém as dimensões da janela e da imagem
        _, _, win_w, win_h = cv2.getWindowImageRect(self.window_name)
        img_h, img_w = image_array.shape[:2]

        # Calcula a escala para caber na janela mantendo a proporção
        scale = min(win_w / img_w, win_h / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)
        
        # Redimensiona a imagem
        resized_img = cv2.resize(image_array, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Cria uma "tela" preta do tamanho da janela
        canvas = np.zeros((win_h, win_w), dtype=np.uint8)

        # Calcula a posição para centralizar a imagem na tela
        x_offset = (win_w - new_w) // 2
        y_offset = (win_h - new_h) // 2

        # "Cola" a imagem redimensionada na tela preta
        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized_img
        
        # Converte a tela para o formato de cor (BGR) para poder desenhar texto colorido
        canvas_bgr = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)
        # -----------------------------------------------

        self._draw_text_info(canvas_bgr, accession_number)
        
        cv2.imshow(self.window_name, canvas_bgr)
        return True

    def _draw_text_info(self, image, accession_number):
        """Desenha os textos de informação sobre a imagem."""
        # --- CORREÇÃO 2: FONTES MAIORES E DINÂMICAS ---
        # O tamanho da fonte agora é relativo à altura da janela (imagem)
        font_scale = max(1.0, image.shape[0] / 1200)
        thickness = max(1, int(image.shape[0] / 500))
        # ------------------------------------------------
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        line_type = cv2.LINE_AA

        total = self.data_manager.get_total_navigable_folders()
        current = self.data_manager.get_current_folder_index_display()
        info_text = f"Exame: {accession_number} ({current}/{total})"
        cv2.putText(image, info_text, (15, 45), font, font_scale, (255, 255, 255), thickness, line_type)

        classification = self.data_manager.get_classification(accession_number)
        if classification:
            label = self.classification_labels.get(classification, f"Classe: {classification}")
            status_text = f"Ja Classificado: {label}"
            cv2.putText(image, status_text, (15, image.shape[0] - 30), font, font_scale * 1.2, (0, 255, 0), thickness + 1, line_type)

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
            # --- CORREÇÃO 3: CAPTURA DE TECLAS ESPECIAIS (SETAS) ---
            # waitKeyEx() retorna o código completo da tecla
            key = cv2.waitKeyEx(0)
            # -------------------------------------------------------

            # --- CORREÇÃO 4: FECHAMENTO CIVILIZADO DA JANELA ---
            # Verifica se a janela ainda está visível. Se o usuário clicou no "X", ela não estará.
            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
            # ----------------------------------------------------

            if key == ord('q') or key == 27: # 'q' ou ESC para sair
                break
            
            # Códigos das setas (padrão para Windows e muitos Linux)
            elif key == 2490368: # Seta para Cima
                if self.data_manager.move_to_previous_folder(): running = self.display_current_exam()
            elif key == 2621440: # Seta para Baixo
                if self.data_manager.move_to_next_folder(): running = self.display_current_exam()

            # Teclas de Classificação
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