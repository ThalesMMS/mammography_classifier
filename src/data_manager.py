# src/data_manager.py

import os
import pandas as pd
import threading
import time
from datetime import datetime

# Importar o DicomImageLoader para ser usado internamente no pré-carregamento
from dicom_loader import DicomImageLoader

class DataManager:
    def __init__(self, project_root: str):
        """
        Inicializa o DataManager.

        Args:
            project_root (str): O caminho para o diretório raiz do projeto.
        """
        self.project_root = project_root
        self.archive_dir = os.path.join(self.project_root, "archive")
        self.train_csv_path = os.path.join(self.archive_dir, "train.csv")
        self.classification_csv_path = os.path.join(self.project_root, "classificacao.csv")

        # Componentes
        self.dicom_loader = DicomImageLoader()
        self.patient_data_df = None # Metadados do train.csv
        self.classifications_df = None # DataFrame para classificações

        # Listas de pastas
        self._all_valid_patient_folders = []
        self.navigable_folders = []
        self.current_folder_index = -1

        # Buffer de pré-carregamento
        self.image_buffer = {}
        self.buffer_stop_event = threading.Event()
        self.buffer_thread = threading.Thread(target=self._update_buffer, daemon=True)

        # Validação de caminhos
        if not os.path.isdir(self.archive_dir):
            raise FileNotFoundError(f"O diretório 'archive' não foi encontrado em: {self.archive_dir}")
        if not os.path.isfile(self.train_csv_path):
            raise FileNotFoundError(f"O arquivo 'train.csv' não foi encontrado em: {self.train_csv_path}")

        # Carregamento inicial de dados
        self._load_train_data()
        self._scan_patient_folders()
        self._load_classifications()

        # Inicialmente, todas as pastas válidas são navegáveis
        self.navigable_folders = list(self._all_valid_patient_folders)
        if self.navigable_folders:
            self.current_folder_index = 0

    def start_buffer_thread(self):
        """Inicia a thread de pré-carregamento em segundo plano."""
        if not self.buffer_thread.is_alive():
            print("Iniciando thread de pré-carregamento de imagens...")
            self.buffer_thread.start()

    def stop_buffer_thread(self):
        """Sinaliza para a thread de pré-carregamento parar."""
        print("Parando thread de pré-carregamento...")
        self.buffer_stop_event.set()
        self.buffer_thread.join(timeout=2) # Espera a thread terminar

    def _load_train_data(self):
        """Carrega o arquivo train.csv para identificar pastas válidas."""
        try:
            # Carregamos apenas o necessário para validar as pastas
            df = pd.read_csv(self.train_csv_path, dtype={'AccessionNumber': str})
            df.set_index('AccessionNumber', inplace=True)
            self.patient_data_df = df
        except Exception as e:
            print(f"Erro inesperado ao carregar '{self.train_csv_path}': {e}")
            self.patient_data_df = pd.DataFrame()

    def _scan_patient_folders(self):
        """Verifica o diretório 'archive' para encontrar pastas de pacientes válidas."""
        if self.patient_data_df is None or self.patient_data_df.empty:
            return
        
        found_folders = [
            item for item in sorted(os.listdir(self.archive_dir))
            if os.path.isdir(os.path.join(self.archive_dir, item)) and item in self.patient_data_df.index
        ]
        self._all_valid_patient_folders = found_folders
        print(f"Encontradas {len(self._all_valid_patient_folders)} pastas de pacientes válidas e com gabarito.")

    def _load_classifications(self):
        """Carrega o arquivo de classificações (classificacao.csv) se ele existir."""
        try:
            self.classifications_df = pd.read_csv(self.classification_csv_path, dtype={'AccessionNumber': str})
            self.classifications_df.set_index('AccessionNumber', inplace=True)
            print(f"Arquivo 'classificacao.csv' carregado. {len(self.classifications_df)} exames já classificados.")
        except FileNotFoundError:
            print("Arquivo 'classificacao.csv' não encontrado. Criando um novo DataFrame de classificações.")
            self.classifications_df = pd.DataFrame(columns=['Classification', 'ClassificationDate'])
            self.classifications_df.index.name = 'AccessionNumber'
        except Exception as e:
            print(f"Erro ao carregar 'classificacao.csv': {e}")
            self.classifications_df = pd.DataFrame() # DataFrame vazio em caso de erro

    def save_classification(self, accession_number: str, classification: int):
        """Salva ou atualiza a classificação de um exame e salva no CSV."""
        if self.classifications_df is None:
            return

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_data = {'Classification': classification, 'ClassificationDate': now}
        
        # Atualiza ou adiciona a linha no DataFrame
        self.classifications_df.loc[accession_number] = new_data
        
        # Salva o DataFrame inteiro de volta no arquivo CSV
        try:
            self.classifications_df.to_csv(self.classification_csv_path)
            print(f"Classificação para {accession_number} salva como '{classification}'.")
        except IOError as e:
            print(f"ERRO: Não foi possível salvar as alterações em '{self.classification_csv_path}': {e}")

    def get_classification(self, accession_number: str) -> int | None:
        """Retorna a classificação de um exame, se existir."""
        if accession_number in self.classifications_df.index:
            # Retorna o valor da coluna 'Classification' como inteiro
            return int(self.classifications_df.loc[accession_number, 'Classification'])
        return None

    def filter_folders(self, only_unclassified: bool):
        """Filtra a lista de pastas navegáveis."""
        print("\nAplicando filtros de navegação...")
        
        candidate_folders = list(self._all_valid_patient_folders)
        
        if only_unclassified:
            classified_exams = set(self.classifications_df.index)
            candidate_folders = [
                folder for folder in candidate_folders
                if folder not in classified_exams
            ]
            print(f"- Filtro 'Apenas não classificados': {len(candidate_folders)} pastas restantes.")
        else:
            print("- Filtro 'Apenas não classificados': Desativado (mostrando todas).")

        self.navigable_folders = candidate_folders
        if self.navigable_folders:
            self.current_folder_index = 0
            print(f"Total de pastas navegáveis após filtros: {len(self.navigable_folders)}")
        else:
            self.current_folder_index = -1
            print("Aviso: Nenhuma pasta corresponde aos critérios de filtro selecionados.")

    def get_dicom_files(self, accession_number: str) -> list:
        """Retorna a lista de arquivos .dcm para um paciente."""
        folder_path = os.path.join(self.archive_dir, accession_number)
        if not os.path.isdir(folder_path):
            return []
        return [f for f in sorted(os.listdir(folder_path)) if f.lower().endswith('.dcm')]

    def get_current_folder_details(self) -> dict | None:
        """Retorna detalhes básicos da pasta atual."""
        if not self.navigable_folders or self.current_folder_index < 0:
            return None
        
        accession_number = self.navigable_folders[self.current_folder_index]
        return {
            "accession_number": accession_number,
            "dicom_files_count": len(self.get_dicom_files(accession_number))
        }

    # --- MÉTODOS DE PRÉ-CARREGAMENTO (BUFFER) ---

    def _update_buffer(self):
        """Função executada pela thread para carregar e descarregar imagens do buffer."""
        while not self.buffer_stop_event.is_set():
            if self.current_folder_index < 0:
                time.sleep(0.5)
                continue

            # 1. Determinar quais exames devem estar no buffer (atual + 2 próximos)
            indices_to_load = set()
            for i in range(3):
                idx = self.current_folder_index + i
                if 0 <= idx < len(self.navigable_folders):
                    indices_to_load.add(idx)
            
            accessions_to_load = {self.navigable_folders[i] for i in indices_to_load}

            # 2. Carregar exames que ainda não estão no buffer
            for accession in accessions_to_load:
                if accession not in self.image_buffer:
                    print(f"[Buffer Thread] Carregando exame: {accession}")
                    dicom_files = self.get_dicom_files(accession)
                    image_data_list = []
                    for fname in dicom_files:
                        fpath = os.path.join(self.archive_dir, accession, fname)
                        pixel_data, view_params = self.dicom_loader.load_dicom_data(fpath)
                        if pixel_data is not None:
                            image_data_list.append((pixel_data, view_params))
                    self.image_buffer[accession] = image_data_list
            
            # 3. Descarregar exames que não são mais necessários
            accessions_in_buffer = list(self.image_buffer.keys())
            for accession in accessions_in_buffer:
                if accession not in accessions_to_load:
                    print(f"[Buffer Thread] Descarregando exame: {accession}")
                    del self.image_buffer[accession]
            
            time.sleep(0.5) # Pausa para não consumir 100% da CPU

    def get_exam_data_from_buffer(self, accession_number: str) -> list | None:
        """Obtém os dados de imagem de um exame do buffer. Pode esperar se não estiver pronto."""
        # Espera até que o exame esteja no buffer (com um timeout)
        timeout = 5  # segundos
        start_time = time.time()
        while accession_number not in self.image_buffer:
            if time.time() - start_time > timeout:
                print(f"ERRO: Timeout esperando pelo exame '{accession_number}' no buffer.")
                return None
            time.sleep(0.1)
        return self.image_buffer.get(accession_number)

    # --- MÉTODOS DE NAVEGAÇÃO ---

    def move_to_next_folder(self) -> bool:
        if not self.navigable_folders or self.current_folder_index >= len(self.navigable_folders) - 1:
            return False
        self.current_folder_index += 1
        return True

    def move_to_previous_folder(self) -> bool:
        if not self.navigable_folders or self.current_folder_index <= 0:
            return False
        self.current_folder_index -= 1
        return True
    
    def get_total_navigable_folders(self) -> int:
        return len(self.navigable_folders)

    def get_current_folder_index_display(self) -> int:
        if self.current_folder_index == -1: return 0
        return self.current_folder_index + 1