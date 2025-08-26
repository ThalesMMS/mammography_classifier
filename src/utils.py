# src/utils.py

import os
import shutil
import datetime

# --- Função Auxiliar para Backup ---

def backup_classification_csv(project_root: str):
    """
    Cria um backup do arquivo 'classificacao.csv' se ele existir.
    
    Args:
        project_root (str): O caminho para o diretório raiz do projeto.
    """
    print("\n--- Iniciando Backup do CSV de Classificações ---")
    
    classification_csv_path = os.path.join(project_root, "classificacao.csv")

    # 1. Verificar se o arquivo de origem existe
    if not os.path.exists(classification_csv_path):
        print("Arquivo 'classificacao.csv' não encontrado. Nenhum backup a ser feito.")
        return

    # 2. Criar o diretório de backup
    backup_base_path = os.path.join(project_root, "backups")
    os.makedirs(backup_base_path, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_target_dir = os.path.join(backup_base_path, f"backup_classificacao_{timestamp}")
    
    try:
        os.makedirs(backup_target_dir)
    except OSError as e:
        print(f"Erro ao criar diretório de backup '{backup_target_dir}': {e}")
        return

    # 3. Copiar o arquivo
    try:
        backup_file_path = os.path.join(backup_target_dir, "classificacao.csv")
        shutil.copy2(classification_csv_path, backup_file_path)
        print(f"Backup concluído com sucesso!")
        print(f"Arquivo 'classificacao.csv' copiado para: {backup_target_dir}")
    except Exception as e:
        print(f"Ocorreu um erro ao copiar 'classificacao.csv' para o backup: {e}")
        # Tenta remover o diretório de backup vazio em caso de falha na cópia
        try:
            if not os.listdir(backup_target_dir):
                os.rmdir(backup_target_dir)
        except OSError:
            pass