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
        # A linha de cópia foi REMOVIDA. Não há mais transferência de dados.

    # O resto do arquivo permanece o mesmo...
    def _load_train_data(self, *args, **kwargs):
        super(DataManager, self)._load_train_data(*args, **kwargs)

    def _scan_patient_folders(self, *args, **kwargs):
        super(DataManager, self)._scan_patient_folders(*args, **kwargs)

    def _load_classifications(self, *args, **kwargs):
        super(DataManager, self)._load_classifications(*args, **kwargs)

    def save_classification(self, *args, **kwargs):
        super(DataManager, self).save_classification(*args, **kwargs)

    def get_classification(self, *args, **kwargs):
        super(DataManager, self).get_classification(*args, **kwargs)

    def filter_folders(self, *args, **kwargs):
        super(DataManager, self).filter_folders(*args, **kwargs)

    def get_dicom_files(self, *args, **kwargs):
        super(DataManager, self).get_dicom_files(*args, **kwargs)

    def get_current_folder_details(self, *args, **kwargs):
        super(DataManager, self).get_current_folder_details(*args, **kwargs)

    def get_exam_data_from_buffer(self, *args, **kwargs):
        super(DataManager, self).get_exam_data_from_buffer(*args, **kwargs)
    
    def move_to_next_folder(self, *args, **kwargs):
        super(DataManager, self).move_to_next_folder(*args, **kwargs)

    def move_to_previous_folder(self, *args, **kwargs):
        super(DataManager, self).move_to_previous_folder(*args, **kwargs)

    def get_total_navigable_folders(self, *args, **kwargs):
        super(DataManager, self).get_total_navigable_folders(*args, **kwargs)

    def get_current_folder_index_display(self, *args, **kwargs):
        super(DataManager, self).get_current_folder_index_display(*args, **kwargs)