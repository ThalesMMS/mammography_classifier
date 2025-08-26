# src/data_manager.py

import os
import pandas as pd
import time
from datetime import datetime
import multiprocessing
import sys
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

        # --- MUDANÇA CRÍTICA ---
        # O image_buffer agora é o dicionário compartilhado desde o início.
        self.manager = multiprocessing.Manager()
        self.image_buffer = self.manager.dict()
        # ----------------------

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

    def load_all_exams_in_parallel(self):
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            pass
        
        num_workers = max(1, os.cpu_count() - 2)
        pool = multiprocessing.Pool(processes=num_workers)

        jobs = []
        # Passamos o self.image_buffer (que já é compartilhado) para os trabalhadores
        for accession in self.navigable_folders:
            dicom_files = self.get_dicom_files(accession)
            if dicom_files:
                file_path = os.path.join(self.archive_dir, accession, dicom_files[0])
                job = pool.apply_async(load_dicom_task, args=(file_path, accession, self.image_buffer))
                jobs.append(job)

        total_jobs = len(jobs)
        if total_jobs == 0:
            pool.close()
            pool.join()
            return

        print(f"Carregando {total_jobs} exames com {num_workers} processos...")
        while True:
            completed_count = sum(1 for job in jobs if job.ready())
            progress = (completed_count / total_jobs) * 100
            bar_length = 50
            filled_length = int(bar_length * completed_count // total_jobs)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            sys.stdout.write(f'\rProgresso: |{bar}| {progress:.1f}% Completo')
            sys.stdout.flush()
            if completed_count == total_jobs:
                break
            time.sleep(0.1)
        print()

        pool.close()
        pool.join()

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
        """Filtra a lista de pastas navegáveis e a limita a 1000 exames."""
        print("\nAplicando filtros de navegação...")
        self.navigable_folders = list(self._all_valid_patient_folders)
        if only_unclassified:
            classified_exams = set(self.classifications_df.index)
            self.navigable_folders = [f for f in self.navigable_folders if f not in classified_exams]
            print(f"- Filtro 'Apenas não classificados': {len(self.navigable_folders)} pastas restantes.")
        else:
            print("- Filtro 'Apenas não classificados': Desativado.")

        # --- MUDANÇA PRINCIPAL ---
        # Limita a lista de navegação a 1000 exames
        limit = 100 # o normal é 1000, mas para testes vou deixar 100
        if len(self.navigable_folders) > limit:
            print(f"AVISO: Encontrados {len(self.navigable_folders)} exames. Limitando a sessão aos primeiros {limit}.")
            self.navigable_folders = self.navigable_folders[:limit]
        # -------------------------

        if self.navigable_folders: self.current_folder_index = 0
        else: self.current_folder_index = -1
        print(f"Total de pastas a serem carregadas nesta sessão: {len(self.navigable_folders)}")


    def get_dicom_files(self, accession_number: str) -> list:
        folder_path = os.path.join(self.archive_dir, accession_number)
        if not os.path.isdir(folder_path): return []
        return [f for f in sorted(os.listdir(folder_path)) if f.lower().endswith('.dcm')]

    def get_current_folder_details(self) -> dict | None:
        if not self.navigable_folders or self.current_folder_index < 0: return None
        return {"accession_number": self.navigable_folders[self.current_folder_index]}

    def get_exam_data_from_buffer(self, accession_number: str) -> tuple | None:
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