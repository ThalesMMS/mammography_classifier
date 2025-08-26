# src/main.py
import os
import traceback 

from data_manager import DataManager
from ui_viewer import ImageViewerUI
# Importa a nova função de backup e remove as antigas
from utils import backup_classification_csv

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__)) 
    project_root = os.path.dirname(script_dir) 
    
    # O caminho para a pasta 'archive' agora é gerenciado internamente pelo DataManager,
    # mas verificamos sua existência aqui para um feedback inicial rápido.
    archive_path_check = os.path.join(project_root, "archive")
    print(f"Verificando a pasta 'archive' em: {archive_path_check}")

    if not os.path.isdir(archive_path_check):
        print(f"ERRO: Pasta 'archive' não encontrada em '{archive_path_check}'. Certifique-se de que ela existe.")
    else:
        try:
            # DataManager agora é inicializado com a raiz do projeto
            dm = DataManager(project_root=project_root) 
            
            # Verifica se alguma pasta de exame válida foi encontrada
            if not dm._all_valid_patient_folders:
                print("Nenhuma pasta de paciente válida foi encontrada no diretório 'archive'. Encerrando.")
                exit() 

            # --- ETAPA DE BACKUP (MODIFICADA) ---
            while True:
                answer_backup = input("\nDeseja fazer BACKUP do arquivo de classificações (classificacao.csv) existente? (s/n): ").strip().lower()
                if answer_backup in ['s', 'sim', 'n', 'nao', 'não', 'no']: break
                print("Resposta inválida. Por favor, responda com 's' ou 'n'.")
            if answer_backup.startswith('s'):
                # Chama a nova função de backup do CSV
                backup_classification_csv(project_root)

            # --- ETAPA DE FILTROS PARA NAVEGAÇÃO (MODIFICADA) ---
            while True:
                answer_filter = input("\nDeseja exibir APENAS os exames ainda não classificados? (s/n): ").strip().lower()
                if answer_filter in ['s', 'sim', 'n', 'nao', 'não', 'no']: break
                print("Resposta inválida. Por favor, responda com 's' ou 'n'.")
            
            show_only_unclassified = answer_filter.startswith('s')
            
            # Aplica o novo filtro no DataManager
            dm.filter_folders(only_unclassified=show_only_unclassified)
            
            # --- Inicia a UI se houver pastas para navegar ---
            if dm.get_total_navigable_folders() == 0: 
                print("\nNenhuma pasta para exibir com os critérios selecionados. Encerrando.")
            else:
                print("\n--- Iniciando Interface Gráfica de Classificação ---")
                viewer_app = ImageViewerUI(data_manager=dm) 
                viewer_app.show()

        except SystemExit as e:
            print(f"Aplicação encerrada: {e}")
            raise
        except FileNotFoundError as e: 
            print(f"Erro de arquivo não encontrado: {e}")
        except KeyboardInterrupt:
            print("\nExecução interrompida pelo usuário.") 
        except Exception as e:
            print(f"Ocorreu um erro inesperado ao executar a aplicação: {e}")
            traceback.print_exc()