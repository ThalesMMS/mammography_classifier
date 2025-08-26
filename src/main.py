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

    if not os.path.isdir(archive_path_check):
        print(f"ERRO: Pasta 'archive' não encontrada em '{archive_path_check}'. Certifique-se de que ela existe.")
    else:
        try:
            dm = DataManager(project_root=project_root) 
            
            if not dm._all_valid_patient_folders:
                print("Nenhuma pasta de paciente válida foi encontrada no diretório 'archive'. Encerrando.")
                exit() 

            # --- ETAPAS DE CONFIGURAÇÃO (Backup e Filtro) ---
            while True:
                answer_backup = input("\nDeseja fazer BACKUP do arquivo de classificações (classificacao.csv) existente? (s/n): ").strip().lower()
                if answer_backup in ['s', 'sim', 'n', 'nao', 'não', 'no']: break
                print("Resposta inválida. Por favor, responda com 's' ou 'n'.")
            if answer_backup.startswith('s'):
                backup_classification_csv(project_root)

            while True:
                answer_filter = input("\nDeseja exibir APENAS os exames ainda não classificados? (s/n): ").strip().lower()
                if answer_filter in ['s', 'sim', 'n', 'nao', 'não', 'no']: break
                print("Resposta inválida. Por favor, responda com 's' ou 'n'.")
            
            show_only_unclassified = answer_filter.startswith('s')
            dm.filter_folders(only_unclassified=show_only_unclassified)
            
            # --- NOVA ETAPA: Carregamento Inicial de TODOS os Exames ---
            if dm.get_total_navigable_folders() > 0:
                print("\n--- Iniciando pré-carregamento de todos os exames na RAM ---")
                print("Isso pode levar alguns segundos, dependendo do número de exames...")
                
                # Esta função agora carrega tudo e exibe uma barra de progresso
                dm.load_all_exams_in_parallel()

                print("\n--- Carregamento concluído. Iniciando Interface Gráfica ---")
                viewer_app = ImageViewerUI(data_manager=dm) 
                viewer_app.show()
            else:
                print("\nNenhuma pasta para exibir com os critérios selecionados. Encerrando.")

        except SystemExit as e:
            print(f"Aplicação encerrada: {e}")
        except FileNotFoundError as e: 
            print(f"Erro de arquivo não encontrado: {e}")
        except KeyboardInterrupt:
            print("\nExecução interrompida pelo usuário.") 
        except Exception as e:
            print(f"Ocorreu um erro inesperado ao executar a aplicação: {e}")
            traceback.print_exc()