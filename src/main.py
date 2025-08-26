# src/main.py
import os
import traceback 

from data_manager import DataManager
from ui_viewer import ImageViewerUI
from utils import backup_classification_csv

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__)) 
    project_root = os.path.dirname(script_dir) 
    
    archive_path_check = os.path.join(project_root, "archive")
    print(f"Verificando a pasta 'archive' em: {archive_path_check}")

    dm = None # Inicializa dm como None
    if not os.path.isdir(archive_path_check):
        print(f"ERRO: Pasta 'archive' não encontrada em '{archive_path_check}'.")
    else:
        try:
            dm = DataManager(project_root=project_root) 
            
            if not dm._all_valid_patient_folders:
                print("Nenhuma pasta de paciente válida foi encontrada. Encerrando.")
                exit() 

            # Configuração
            while True:
                answer_backup = input("\nDeseja fazer BACKUP do arquivo de classificações? (s/n): ").strip().lower()
                if answer_backup in ['s', 'sim', 'n', 'nao', 'não', 'no']: break
                print("Resposta inválida.")
            if answer_backup.startswith('s'):
                backup_classification_csv(project_root)

            while True:
                answer_filter = input("\nDeseja exibir APENAS os exames ainda não classificados? (s/n): ").strip().lower()
                if answer_filter in ['s', 'sim', 'n', 'nao', 'não', 'no']: break
                print("Resposta inválida.")
            
            show_only_unclassified = answer_filter.startswith('s')
            dm.filter_folders(only_unclassified=show_only_unclassified)
            
            # Carregamento
            if dm.get_total_navigable_folders() > 0:
                dm.load_all_exams_in_parallel()

                print("\n--- Carregamento concluído. Iniciando Interface Gráfica ---")
                viewer_app = ImageViewerUI(data_manager=dm) 
                viewer_app.show()
            else:
                print("\nNenhuma pasta para exibir. Encerrando.")

        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            traceback.print_exc()
        finally:
            # Garante que o gerenciador de processos seja encerrado
            if dm and hasattr(dm, 'manager'):
                print("Encerrando gerenciador de memória compartilhada...")
                dm.manager.shutdown()