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

        # Cria a janela do OpenCV. Ela pode ser redimensionada.
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        # Define um tamanho inicial razoável
        cv2.resizeWindow(self.window_name, 800, 1000)

    def display_current_exam(self):
        """Busca a imagem e a exibe na janela do OpenCV."""
        details = self.data_manager.get_current_folder_details()
        if not details:
            self.display_message("Fim da lista de exames!")
            # Espera 5 segundos antes de fechar para o usuário poder ler a mensagem
            cv2.waitKey(5000)
            return False # Sinaliza para o loop principal terminar

        accession_number = details["accession_number"]
        
        # A imagem já está na RAM como um array uint8 pronto para uso
        image_array = self.data_manager.get_exam_data_from_buffer(accession_number)
        
        if image_array is None:
            self.display_message(f"Erro ao carregar imagem para:\n{accession_number}")
            cv2.waitKey(2000) # Pausa por 2s em caso de erro
            return True # Continua o loop

        # Adiciona as informações de texto diretamente na imagem
        self._draw_text_info(image_array, accession_number)
        
        # Exibe a imagem final na tela. Esta operação é extremamente rápida.
        cv2.imshow(self.window_name, image_array)
        return True

    def _draw_text_info(self, image, accession_number):
        """Desenha os textos de informação diretamente sobre a imagem com OpenCV."""
        # Configurações de fonte
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        font_color = (255, 255, 255) # Branco
        thickness = 2
        line_type = cv2.LINE_AA

        # Informação do exame no canto superior esquerdo
        total = self.data_manager.get_total_navigable_folders()
        current = self.data_manager.get_current_folder_index_display()
        info_text = f"Exame: {accession_number} ({current}/{total})"
        cv2.putText(image, info_text, (15, 45), font, font_scale, font_color, thickness, line_type)

        # Status da classificação no canto inferior esquerdo
        classification = self.data_manager.get_classification(accession_number)
        if classification:
            label = self.classification_labels.get(classification, f"Classe: {classification}")
            status_text = f"Ja Classificado: {label}"
            # Usa verde para o status, para diferenciar
            cv2.putText(image, status_text, (15, image.shape[0] - 30), font, 1.4, (0, 255, 0), thickness + 1, line_type)

    def display_message(self, message: str):
        """Cria uma imagem preta e exibe uma mensagem de status."""
        # Cria uma tela preta para exibir a mensagem
        message_screen = np.zeros((600, 800), dtype=np.uint8)
        
        # Quebra a mensagem em múltiplas linhas se necessário
        y0, dy = 280, 50
        for i, line in enumerate(message.split('\n')):
            y = y0 + i * dy
            cv2.putText(message_screen, line, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
        cv2.imshow(self.window_name, message_screen)
    
    def show(self):
        """Inicia o loop principal da aplicação para exibição e captura de teclas."""
        if self.data_manager.get_total_navigable_folders() <= 0:
            self.display_message("Nenhuma pasta encontrada para os criterios de filtro.")
            cv2.waitKey(3000)
            cv2.destroyAllWindows()
            return
            
        running = self.display_current_exam()

        while running:
            # cv2.waitKey(0) espera indefinidamente por uma tecla
            key = cv2.waitKey(0) & 0xFF

            # Tecla 'q' ou ESC para sair
            if key == ord('q') or key == 27:
                running = False

            # Teclas de Navegação (Setas)
            # Os códigos podem variar, estes são comuns para Windows
            elif key == 82: # Seta para Cima
                if self.data_manager.move_to_previous_folder():
                    running = self.display_current_exam()
            elif key == 84: # Seta para Baixo
                if self.data_manager.move_to_next_folder():
                    running = self.display_current_exam()

            # Teclas de Classificação (1-5)
            elif ord('1') <= key <= ord('5'):
                details = self.data_manager.get_current_folder_details()
                if details:
                    classification = int(chr(key))
                    self.data_manager.save_classification(details["accession_number"], classification)
                    
                    if not self.data_manager.move_to_next_folder():
                        running = False
                        self.display_message("Fim da lista de exames!")
                        cv2.waitKey(5000)
                    else:
                        running = self.display_current_exam()

        # Garante que a janela seja fechada ao sair do loop
        cv2.destroyAllWindows()