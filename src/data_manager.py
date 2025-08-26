# src/data_manager.py

import os
import pandas as pd
import threading
import time
from datetime import datetime
import multiprocessing
from dicom_loader import load_dicom_task

class DataManager:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.archive_dir = os.path.join(self.project_root, "archive")
        self.train_csv_path = os.path.join(self.archive_dir, "train.csv")
        self.classification_csv_path = os.path.join(self.project_root, "classificacao.csv")

        self.patient_data_df = None
        self.classifications_df = None
        self._all_valid_patient_folders = []
        self.navigable_folders = []
        self.current_folder_index = -1

        # --- Lógica de Multiprocessing ---
        try:
            # Garante compatibilidade entre sistemas operacionais
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            pass # O método de início só pode ser definido uma vez

        self.manager = multiprocessing.Manager()
        self.image_buffer = self.manager.dict() # Dicionário seguro para processos
        num_workers = max(1, os.cpu_count() // 2) # Usa metade dos núcleos da CPU
        print(f"Iniciando pool com {num_workers} processos trabalhadores...")
        self.pool = multiprocessing.Pool(processes=num_workers)
        
        self.pending_jobs = {} # Rastreia tarefas em andamento
        self.control_thread_stop_event = threading.Event()
        self.control_thread = threading.Thread(target=self._manage_buffer_jobs, daemon=True)
        # ------------------------------------

        if not os.path.isdir(self.archive_dir):
            raise FileNotFoundError(f"O diretório 'archive' não foi encontrado em: {self.archive_dir}")
        if not os.path.isfile(self.train_csv_path):
            raise FileNotFoundError(f"O arquivo 'train.csv' não foi encontrado em: {self.train_csv_path}")

        self._load_train_data()
        self._scan_patient_folders()
        self._load_classifications()

        self.navigable_folders = list(self._all_valid_patient_folders)
        if self.navigable_folders:
            self.current_folder_index = 0

    def start_loader(self):
        """Inicia o gerenciador de tarefas de carregamento paralelo."""
        if not self.control_thread.is_alive():
            print("Iniciando gerenciador de tarefas...")
            self.control_thread.start()

    def shutdown_loader(self):
        """Encerra a piscina de processos de forma limpa."""
        print("Encerrando pool de processos de carregamento...")
        self.control_thread_stop_event.set()
        self.control_thread.join(timeout=2)
        self.pool.close()
        self.pool.join()

    def _manage_buffer_jobs(self):
        """Thread de controle que distribui tarefas para a piscina de processos."""
        while not self.control_thread_stop_event.is_set():
            if self.current_folder_index < 0:
                time.sleep(0.1)
                continue

            buffer_size = 8
            indices_to_load = {self.current_folder_index + i for i in range(buffer_size) if 0 <= self.current_folder_index + i < len(self.navigable_folders)}
            accessions_to_load = {self.navigable_folders[i] for i in indices_to_load}

            # Limpa jobs pendentes que já terminaram
            for acc, job in list(self.pending_jobs.items()):
                if job.ready():
                    del self.pending_jobs[acc]

            # Envia novos jobs para o pool
            for accession in accessions_to_load:
                if accession not in self.image_buffer and accession not in self.pending_jobs:
                    dicom_files = self.get_dicom_files(accession)
                    if dicom_files:
                        file_path = os.path.join(self.archive_dir, accession, dicom_files[0])
                        job = self.pool.apply_async(load_dicom_task, args=(file_path, accession, self.image_buffer))
                        self.pending_jobs[accession] = job
                    else:
                        self.image_buffer[accession] = None

            # Limpa do buffer os exames que ficaram para trás
            for accession in list(self.image_buffer.keys()):
                if accession not in accessions_to_load and accession not in self.pending_jobs:
                    del self.image_buffer[accession]
            
            time.sleep(0.1)

    def _load_train_data(self):
        try:
            df = pd.read_csv(self.train_csv_path, dtype={'AccessionNumber': str})
            df.set_index('AccessionNumber', inplace=True)
            self.patient_data_df = df
        except Exception as e:
            print(f"Erro inesperado ao carregar '{self.train_csv_path}': {e}")
            self.patient_data_df = pd.DataFrame()

    def _scan_patient_folders(self):
        if self.patient_data_df is None or self.patient_data_df.empty:
            return
        self._all_valid_patient_folders = [
            item for item in sorted(os.listdir(self.archive_dir))
            if os.path.isdir(os.path.join(self.archive_dir, item)) and item in self.patient_data_df.index
        ]
        print(f"Encontradas {len(self._all_valid_patient_folders)} pastas de pacientes válidas e com gabarito.")

    def _load_classifications(self):
        try:
            self.classifications_df = pd.read_csv(self.classification_csv_path, dtype={'AccessionNumber': str})
            self.classifications_df.set_index('AccessionNumber', inplace=True)
            print(f"Arquivo 'classificacao.csv' carregado. {len(self.classifications_df)} exames já classificados.")
        except FileNotFoundError:
            print("Arquivo 'classificacao.csv' não encontrado. Criando um novo DataFrame.")
            self.classifications_df = pd.DataFrame(columns=['Classification', 'ClassificationDate'])
            self.classifications_df.index.name = 'AccessionNumber'
        except Exception as e:
            print(f"Erro ao carregar 'classificacao.csv': {e}")
            self.classifications_df = pd.DataFrame()

    def save_classification(self, accession_number: str, classification: int):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.classifications_df.loc[accession_number] = {'Classification': classification, 'ClassificationDate': now}
        try:
            self.classifications_df.to_csv(self.classification_csv_path)
            print(f"Classificação para {accession_number} salva como '{classification}'.")
        except IOError as e:
            print(f"ERRO: Não foi possível salvar em '{self.classification_csv_path}': {e}")

    def get_classification(self, accession_number: str) -> int | None:
        if accession_number in self.classifications_df.index:
            return int(self.classifications_df.loc[accession_number, 'Classification'])
        return None

    def filter_folders(self, only_unclassified: bool):
        print("\nAplicando filtros de navegação...")
        self.navigable_folders = list(self._all_valid_patient_folders)
        if only_unclassified:
            classified_exams = set(self.classifications_df.index)
            self.navigable_folders = [f for f in self.navigable_folders if f not in classified_exams]
            print(f"- Filtro 'Apenas não classificados': {len(self.navigable_folders)} pastas restantes.")
        else:
            print("- Filtro 'Apenas não classificados': Desativado.")

        if self.navigable_folders: self.current_folder_index = 0
        else: self.current_folder_index = -1
        print(f"Total de pastas navegáveis: {len(self.navigable_folders)}")

    def get_dicom_files(self, accession_number: str) -> list:
        folder_path = os.path.join(self.archive_dir, accession_number)
        if not os.path.isdir(folder_path): return []
        return [f for f in sorted(os.listdir(folder_path)) if f.lower().endswith('.dcm')]

    def get_current_folder_details(self) -> dict | None:
        if not self.navigable_folders or self.current_folder_index < 0: return None
        return {"accession_number": self.navigable_folders[self.current_folder_index]}

    def get_exam_data_from_buffer(self, accession_number: str) -> tuple | None:
        timeout, start_time = 10, time.time() # Aumentado timeout por segurança
        while accession_number not in self.image_buffer:
            if time.time() - start_time > timeout:
                print(f"ERRO: Timeout esperando pelo exame '{accession_number}' no buffer.")
                return None
            time.sleep(0.05)
        return self.image_buffer.get(accession_number)

    def move_to_next_folder(self) -> bool:
        if not self.navigable_folders or self.current_folder_index >= len(self.navigable_folders) - 1: return False
        self.current_folder_index += 1
        return True

    def move_to_previous_folder(self) -> bool:
        if not self.navigable_folders or self.current_folder_index <= 0: return False
        self.current_folder_index -= 1
        return True
    
    def get_total_navigable_folders(self) -> int:
        return len(self.navigable_folders)

    def get_current_folder_index_display(self) -> int:
        if self.current_folder_index == -1: return 0
        return self.current_folder_index + 1