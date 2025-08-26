# Ferramenta de Classificação de Densidade Mamária

Esta é uma aplicação Python desenvolvida para auxiliar na classificação de densidade de exames de mamografia. A ferramenta exibe todas as imagens DICOM de um exame simultaneamente em um grid, permitindo que o usuário classifique o exame de forma rápida e eficiente usando o teclado. As classificações são salvas em um arquivo `classificacao.csv`.

A aplicação é otimizada para agilidade, pré-carregando os exames seguintes em segundo plano para eliminar o tempo de espera.

## Como Rodar

PowerShell

    # Exemplo usando PowerShell
    PS D:\dicom_workplace> .\.venv\Scripts\activate
    (.venv) PS D:\dicom_workplace> python .\src\main.py
    

## Funcionalidades Principais

*   **Visualização de Exame Completo:** Carrega e exibe todas as imagens DICOM de um exame simultaneamente em um grid dinâmico.
    
*   **Classificação por Teclado:** Permite ao usuário classificar a densidade do exame usando as teclas numéricas de 1 a 4.
    
*   **Navegação Ágil:**
    
    *   Avança automaticamente para o próximo exame após uma classificação ser feita.
        
    *   Permite navegação manual entre exames com as setas (Cima/Baixo).
        
*   **Registro de Classificações:** Salva cada classificação em um arquivo `classificacao.csv` na raiz do projeto, contendo o identificador do exame (`AccessionNumber`), a classe e a data/hora da classificação.
    
*   **Performance Otimizada:** Utiliza um sistema de pré-carregamento (*pre-loading*) para manter os próximos exames em memória, garantindo uma transição instantânea entre os casos.
    
*   **Feedback Visual:** Exibe na tela o identificador do exame atual e informa se ele já foi classificado anteriormente.
    
*   **Opções de Inicialização (via console):**
    
    1.  **Backup das Classificações:** Opção para fazer backup do arquivo `classificacao.csv` existente.
        
    2.  **Filtro de Navegação:** Opção para exibir apenas os exames que ainda não foram classificados.
        

## Estrutura do Projeto

    dicom_workplace/
    │
    ├── archive/                     # Contém as subpastas de exames DICOM e train.csv
    │   ├── 002000/
    │   │   ├── imagem1.dcm
    │   │   └── ...
    │   ├── ...
    │   └── train.csv
    │
    ├── backups/                     # Criado para backups do classificacao.csv
    │   └── backup_classificacao_YYYYMMDD_HHMMSS/
    │       └── classificacao.csv
    │
    ├── src/                         # Código fonte da aplicação
    │   ├── main.py                  # Ponto de entrada principal
    │   ├── ui_viewer.py             # Interface gráfica do usuário (grid de visualização)
    │   ├── data_manager.py          # Lógica de dados, classificação e buffer de pré-carregamento
    │   ├── dicom_loader.py          # Carregador e processador de imagens DICOM
    │   └── utils.py                 # Funções utilitárias (backup)
    │
    ├── .gitignore                   # Arquivos ignorados pelo Git
    ├── requirements.txt             # Dependências Python
    ├── classificacao.csv            # Arquivo de saída gerado com as classificações
    └── README.md                    # Este arquivo
    

## Pré-requisitos

*   Python (recomendado: 3.9 ou superior)
    
*   Bibliotecas listadas em `requirements.txt`. As principais são:
    
    *   `pandas`
        
    *   `pydicom`
        
    *   `matplotlib`
        
    *   `numpy`
        
*   Para descompressão de certos arquivos DICOM (ex: JPEG Lossless):
    
    *   `pylibjpeg`
        
    *   `pylibjpeg-libjpeg`
        

## Configuração do Ambiente

1.  **Clone o Repositório (se estiver no Git):**
    
    Bash
    
        git clone <url_do_repositorio>
        cd <nome_do_projeto>
        
    
2.  **Crie um Ambiente Virtual:**
    
    Bash
    
        python -m venv .venv
        
    
3.  **Ative o Ambiente Virtual:**
    
    *   Windows (PowerShell):
        
        PowerShell
        
            .venv\Scripts\Activate.ps1
            
        
    *   Linux/macOS:
        
        Bash
        
            source .venv/bin/activate
            
        
4.  **Instale as Dependências:**
    
    Bash
    
        pip install -r requirements.txt
        
    
    Para garantir a capacidade de lidar com DICOMs comprimidos, instale também:
    
    Bash
    
        pip install pylibjpeg pylibjpeg-libjpeg
        
    
5.  **Prepare os Dados:**
    
    *   Certifique-se de que a pasta `archive/` existe na raiz do projeto.
        
    *   Dentro de `archive/`, coloque as subpastas dos exames (nomeadas com `AccessionNumber`).
        
    *   O arquivo `train.csv` deve estar presente dentro da pasta `archive/` para identificar os exames válidos.
        

## Como Executar a Aplicação

1.  Certifique-se de que o ambiente virtual está ativo.
    
2.  Execute o script `main.py` a partir da raiz do projeto:
    
    Bash
    
        python src/main.py
        
    
3.  Responda às perguntas de configuração inicial que aparecerão no console.
    

## Instruções de Uso (Teclas de Atalho)

*   **Teclas `1`, `2`, `3`, `4`:** Classificam o exame atual e avançam para o próximo.
    
    *   `1`: Adiposa
        
    *   `2`: Predominantemente Adiposa
        
    *   `3`: Predominantemente Densa
        
    *   `4`: Densa
        
*   **Setas Cima/Baixo:** Navegar manualmente para o exame anterior/seguinte. Permite revisar ou corrigir uma classificação.
    

## Solução de Problemas Comuns

*   **Erro "Unable to decompress..." ao carregar DICOMs:** Isso geralmente significa que o arquivo DICOM está comprimido e as bibliotecas necessárias para descompressão não estão instaladas. Siga o passo 4 da "Configuração do Ambiente".
    
*   **"FileNotFoundError" para `archive` ou `train.csv`:** Verifique se a estrutura de pastas está correta. A aplicação espera que a pasta `archive/` (contendo os exames e o `train.csv`) esteja na raiz do projeto.
    

## Possíveis Melhorias Futuras

*   Implementar zoom e pan na imagem clicada dentro do grid.
    
*   Permitir ajuste manual de janelamento (Window Center/Width).
    
*   Adicionar uma interface gráfica para as opções de inicialização.
    
*   Salvar o estado do último exame visualizado para continuar de onde parou.
    
*   Exibir mais metadados do DICOM (ex: tipo de incidência - MLO, CC) em cada subplot.
    
*   Adicionar um modo de "revisão" onde a classificação não avança automaticamente.