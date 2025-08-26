# src/ui_viewer.py

import cv2
import numpy as np
from data_manager import DataManager

class ImageViewerUI:
    def __init__(self, data_manager: DataManager):
        print("Inicializando UI Otimizada com Loop de Renderização...")
        self.data_manager = data_manager
        self.window_name = 'Ferramenta de Classificacao de Densidade Mamaria'
        
        self.classification_labels = {
            1: "1: Adiposa", 2: "2: Predominantemente Adiposa", 3: "3: Predominantemente Densa",
            4: "4: Densa", 5: "5: Pular / Problema"
        }

        # Voltamos para o WINDOW_NORMAL, pois agora controlaremos o aspect ratio manualmente
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 800, 1000)
        
        # Variáveis para controlar o redesenho
        self.last_window_size = (0, 0)
        self.redraw_needed = True

    def display_current_exam(self):
        """Prepara e exibe a imagem atual com letterbox para manter o aspect ratio."""
        details = self.data_manager.get_current_folder_details()
        if not details:
            self.display_message("Fim da lista de exames!")
            cv2.waitKey(5000)
            return False, None

        accession_number = details["accession_number"]
        image_array = self.data_manager.get_exam_data_from_buffer(accession_number)
        
        if image_array is None:
            self.display_message(f"Erro ao carregar imagem para:\n{accession_number}")
            cv2.waitKey(2000)
            return True, None

        # --- LÓGICA DE LETTERBOX EM TEMPO REAL ---
        # Obtém o tamanho ATUAL da área interna da janela
        try:
            _, _, win_w, win_h = cv2.getWindowImageRect(self.window_name)
        except cv2.error:
             # Se a janela foi minimizada, pode dar erro. Usamos o último tamanho conhecido.
            win_w, win_h = self.last_window_size if self.last_window_size != (0,0) else (800, 1000)

        img_h, img_w = image_array.shape[:2]

        if img_w == 0 or img_h == 0 or win_w == 0 or win_h == 0:
            return True, None # Evita divisão por zero se a janela for muito pequena

        scale = min(win_w / img_w, win_h / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)
        resized_img = cv2.resize(image_array, (new_w, new_h), interpolation=cv2.INTER_AREA)

        canvas = np.zeros((win_h, win_w), dtype=np.uint8)
        x_offset = (win_w - new_w) // 2
        y_offset = (win_h - new_h) // 2
        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized_img
        canvas_bgr = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)
        # -----------------------------------------------

        self._draw_text_info(canvas_bgr, accession_number)
        cv2.imshow(self.window_name, canvas_bgr)
        self.redraw_needed = False
        return True, (win_w, win_h)

    def _draw_text_info(self, image, accession_number):
        """Desenha os textos de informação sobre a imagem."""
        font_scale = max(0.8, image.shape[0] / 1200)
        thickness = max(1, int(image.shape[0] / 500))
        
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
        """Inicia o loop principal "vivo" da aplicação."""
        if self.data_manager.get_total_navigable_folders() <= 0:
            self.display_message("Nenhuma pasta encontrada.")
            cv2.waitKey(3000)
            cv2.destroyAllWindows()
            return
            
        while True:
            # Verifica se a janela foi fechada pelo "X"
            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
            
            # Verifica se a janela foi redimensionada
            try:
                _, _, win_w, win_h = cv2.getWindowImageRect(self.window_name)
                current_size = (win_w, win_h)
                if self.last_window_size != current_size:
                    self.redraw_needed = True
            except cv2.error:
                 # Ignora erros se a janela estiver minimizada, por exemplo
                 pass

            # Redesenha a imagem somente se for necessário
            if self.redraw_needed:
                running, new_size = self.display_current_exam()
                if not running: break
                if new_size: self.last_window_size = new_size
            
            # Espera por uma tecla por 20ms. Se nenhuma tecla for pressionada, o loop continua.
            key = cv2.waitKeyEx(20) 
            if key == -1: # Nenhuma tecla pressionada
                continue

            if key == ord('q') or key == 27:
                break
            
            # Lógica de navegação e classificação
            action_taken = False
            if key == 2490368: # Seta Cima
                if self.data_manager.move_to_previous_folder(): action_taken = True
            elif key == 2621440: # Seta Baixo
                if self.data_manager.move_to_next_folder(): action_taken = True
            elif ord('1') <= key <= ord('5'):
                details = self.data_manager.get_current_folder_details()
                if details:
                    self.data_manager.save_classification(details["accession_number"], int(chr(key)))
                    if not self.data_manager.move_to_next_folder():
                        self.display_message("Fim da lista de exames!")
                        cv2.waitKey(5000)
                        break
                    action_taken = True

            if action_taken:
                self.redraw_needed = True
        
        cv2.destroyAllWindows()