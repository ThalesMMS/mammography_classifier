# Breast Density Classification Tool

This is a Python application designed to help classify breast density in mammography exams. The tool displays all DICOM images from an exam simultaneously in a grid, allowing the user to classify the exam quickly and efficiently using the keyboard. Classifications are saved to a `classificacao.csv` file.

The application is optimized for speed by preloading upcoming exams in the background to eliminate waiting time.

## How to Run

PowerShell

    # Example using PowerShell
    PS D:\dicom_workplace> .\.venv\Scripts\activate
    (.venv) PS D:\dicom_workplace> python .\src\main.py

## Main Features

* **Full Exam View:** Loads and displays all DICOM images from an exam simultaneously in a dynamic grid.

* **Keyboard-Based Classification:** Lets the user classify exam density using the numeric keys 1 through 4.

* **Fast Navigation:**

    * Automatically moves to the next exam after a classification is made.

    * Allows manual navigation between exams with the Up/Down arrow keys.

* **Classification Logging:** Saves each classification to a `classificacao.csv` file at the project root, containing the exam identifier (`AccessionNumber`), the class, and the classification date/time.

* **Optimized Performance:** Uses a preloading system to keep upcoming exams in memory, ensuring instant transitions between cases.

* **Visual Feedback:** Displays the current exam identifier on screen and indicates whether it has already been classified.

* **Startup Options (via console):**

    1. **Classification Backup:** Option to back up the existing `classificacao.csv` file.

    2. **Navigation Filter:** Option to display only exams that have not yet been classified.

## Project Structure

    dicom_workplace/
    │
    ├── archive/                     # Contains the DICOM exam subfolders and train.csv
    │   ├── 002000/
    │   │   ├── imagem1.dcm
    │   │   └── ...
    │   ├── ...
    │   └── train.csv
    │
    ├── backups/                     # Created for classificacao.csv backups
    │   └── backup_classificacao_YYYYMMDD_HHMMSS/
    │       └── classificacao.csv
    │
    ├── src/                         # Application source code
    │   ├── main.py                  # Main entry point
    │   ├── ui_viewer.py             # Graphical user interface (viewing grid)
    │   ├── data_manager.py          # Data logic, classification, and preload buffer
    │   ├── dicom_loader.py          # DICOM image loader and processor
    │   └── utils.py                 # Utility functions (backup)
    │
    ├── .gitignore                   # Files ignored by Git
    ├── requirements.txt             # Python dependencies
    ├── classificacao.csv            # Output file generated with classifications
    └── README.md                    # This file

## Prerequisites

* Python (recommended: 3.9 or later)

* Libraries listed in `requirements.txt`. The main ones are:

    * `pandas`

    * `pydicom`

    * `matplotlib`

    * `numpy`

* For decompression of certain DICOM files (for example, JPEG Lossless):

    * `pylibjpeg`

    * `pylibjpeg-libjpeg`

## Environment Setup

1. **Clone the Repository (if using Git):**

    Bash

        git clone <repository_url>
        cd <project_name>

2. **Create a Virtual Environment:**

    Bash

        python -m venv .venv

3. **Activate the Virtual Environment:**

    * Windows (PowerShell):

        PowerShell

            .venv\Scripts\Activate.ps1

    * Linux/macOS:

        Bash

            source .venv/bin/activate

4. **Install the Dependencies:**

    Bash

        pip install -r requirements.txt

    To ensure support for compressed DICOM files, also install:

    Bash

        pip install pylibjpeg pylibjpeg-libjpeg

5. **Prepare the Data:**

    * Make sure the `archive/` folder exists at the project root.

    * Inside `archive/`, place the exam subfolders (named with the `AccessionNumber`).

    * The `train.csv` file must be present inside the `archive/` folder to identify valid exams.

## How to Run the Application

1. Make sure the virtual environment is active.

2. Run the `main.py` script from the project root:

    Bash

        python src/main.py

3. Answer the initial setup questions shown in the console.

## Usage Instructions (Keyboard Shortcuts)

* **Keys `1`, `2`, `3`, `4`:** Classify the current exam and move to the next one.

    * `1`: Fatty

    * `2`: Predominantly Fatty

    * `3`: Predominantly Dense

    * `4`: Dense

* **Up/Down Arrow Keys:** Manually navigate to the previous/next exam. This allows you to review or correct a classification.

## Common Troubleshooting

* **"Unable to decompress..." error when loading DICOMs:** This usually means the DICOM file is compressed and the required decompression libraries are not installed. Follow step 4 in "Environment Setup."

* **`FileNotFoundError` for `archive` or `train.csv`:** Check whether the folder structure is correct. The application expects the `archive/` folder (containing the exams and `train.csv`) to be at the project root.

## Possible Future Improvements

* Implement zoom and pan on the clicked image inside the grid.

* Allow manual windowing adjustment (Window Center/Width).

* Add a graphical interface for the startup options.

* Save the state of the last viewed exam so work can continue where it left off.

* Display more DICOM metadata (for example, view type - MLO, CC) in each subplot.

* Add a review mode where classification does not advance automatically.
