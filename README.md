# 🚀 Profile Vector

**An AI-powered desktop application for generating demographic and persona insights from social media follower lists.**

Profile Vector is a user-friendly tool designed to automate the analysis of spreadsheet data containing user profiles. By leveraging the power of the Google Gemini API, it takes a list of usernames and full names and enriches it with valuable, AI-driven predictions, helping you understand the composition of an audience quickly and efficiently.

---

### ✨ Features

*   **Simple Graphical User Interface:** No command-line knowledge needed. A clean UI built with PyQt6.
*   **Flexible File Input:** Select any `.xlsx` or `.csv` file from your computer using a file browser.
*   **Dynamic Column Mapping:** Smart dropdowns automatically detect the columns in your file, allowing you to map them to "Full Name" and "Username" fields.
*   **AI-Powered Analysis:** Utilizes the `gemini-1.5-flash-latest` model to infer key metrics for each profile.
*   **Comprehensive Insights:** Generates predictions for:
    *   Predicted Gender
    *   Predicted Ethno-Geographic Origin
    *   Deduced Language
    *   Inferred User Persona (e.g., "Tech Enthusiast," "Golf Professional," "Personal Account")
*   **Confidence Scoring:** Each prediction is accompanied by a confidence score (0.0 to 1.0) to help you gauge the model's certainty.
*   **In-App Results Viewer:** Once the analysis is complete, the results are displayed in a sortable table directly within the application window.
*   **Safe & Robust:**
    *   **Stop Button:** Safely interrupt the analysis at any time. Progress is saved.
    *   **Built-in Rate Limiting:** Automatically pauses between requests to respect free API tier limits and prevent quota errors.
    *   **Responsive UI:** Analysis runs on a separate thread to ensure the application never freezes.

---

### 📸 Screenshot

*(Add a screenshot of the application window here after you run it. For now, this is a placeholder.)*

![Application Screenshot](https://i.imgur.com/your-screenshot-url.png)

---

### ⚙️ Getting Started

Follow these steps to get Profile Vector running on your local machine.

#### Prerequisites

*   **Python 3.8+** must be installed on your system.
    *   You can download it from [python.org](https://www.python.org/downloads/).
    *   **For Windows users:** During installation, make sure to check the box that says **"Add Python to PATH"**.

#### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/Profile-Vector.git
    cd Profile-Vector
    ```
    *(Alternatively, you can download the project as a ZIP file and extract it.)*

2.  **Create a Virtual Environment**
    This creates an isolated space for the project's dependencies.
    ```bash
    # Create the environment
    python -m venv venv

    # Activate it (Windows)
    venv\Scripts\activate

    # Activate it (macOS/Linux)
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    This command reads the `requirements.txt` file and installs all necessary libraries.
    ```bash
    pip install -r requirements.txt
    ```

---

### ▶️ How to Use

1.  **Activate the Virtual Environment** (if it's not already active from the installation step).
    ```bash
    # On Windows
    venv\Scripts\activate
    
    # On macOS/Linux
    source venv/bin/activate
    ```

2.  **Run the Application**
    From the root `Profile-Vector` directory, run:
    ```bash
    python main.py
    ```

3.  **Using the UI:**
    *   **Paste your Google Gemini API key** into the top input field.
    *   Click **"1. Browse for Spreadsheet"** and select your `.csv` or `.xlsx` file.
    *   Use the **"2. Select Full Name Column"** and **"3. Select Username Column"** dropdowns to match the columns in your file.
    *   Click **"4. Run Analysis"**.
    *   Monitor the progress in the "Status Log". You can click the "Stop Analysis" button at any time.
    *   When the process is finished, the results will appear in the table at the bottom. A new file named `your-file-name_output.csv` will also be saved in the same folder as your input file.

---

### 🛠️ How It Works

*   **Frontend:** The graphical user interface is built using **PyQt6**.
*   **Backend:** Core logic is written in **Python**.
*   **Data Handling:** The **Pandas** library is used for reading and processing spreadsheet data.
*   **AI Engine:** The **Google Gemini API** (`gemini-1.5-flash-latest` model) provides the core inference capabilities.
*   **Responsiveness:** The long-running analysis task is offloaded to a `QThread`, ensuring the UI remains responsive and the "Stop" button works instantly.

---

### 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.
