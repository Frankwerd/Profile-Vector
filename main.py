import sys
import os
import pandas as pd
import google.generativeai as genai
import json
import time # <-- Added for rate limiting
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QFileDialog, QTextEdit, QComboBox,
                             QTableWidget, QTableWidgetItem, QHeaderView) # <-- Added for results table
from PyQt6.QtCore import QThread, QObject, pyqtSignal

# --- Worker for Offloading the Analysis to a Separate Thread ---
# This is crucial to prevent the UI from freezing during analysis.
class Worker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, api_key, input_filepath, fullname_col, username_col):
        super().__init__()
        self.api_key = api_key
        self.input_filepath = input_filepath
        self.fullname_col = fullname_col
        self.username_col = username_col
        self.is_running = True # Flag to control the loop

    def run(self):
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.5-pro')
            self.progress.emit("Gemini API configured successfully.")

            if self.input_filepath.endswith('.csv'):
                df = pd.read_csv(self.input_filepath)
            else:
                df = pd.read_excel(self.input_filepath, engine='openpyxl')
            
            self.progress.emit(f"Successfully loaded {os.path.basename(self.input_filepath)}.")
            
            if self.fullname_col not in df.columns or self.username_col not in df.columns:
                self.error.emit(f"Column Error: Please ensure '{self.fullname_col}' and '{self.username_col}' exist in the file.")
                return
                
            self.progress.emit(f"Found {len(df)} rows to analyze.")

            results = []
            total_rows = len(df)
            for index, row in df.iterrows():
                # --- NEW: Check if the stop button was clicked ---
                if not self.is_running:
                    self.progress.emit("\nAnalysis stopped by user.")
                    return # Exit the function cleanly

                full_name = row[self.fullname_col]
                username = row[self.username_col]
                
                if pd.isna(full_name): full_name = ""
                if pd.isna(username): username = ""
                
                self.progress.emit(f"Analyzing row {index + 1}/{total_rows}: {username}...")
                
                prompt = f"""
                Analyze the following social media user data:
                Full Name: "{full_name}"
                Username: "{username}"
                As a world-class cultural and demographic analyst, infer the following metrics.
                Your response MUST be a single, valid JSON object. Each prediction must include a 'value' and a 'confidence' score between 0.0 and 1.0.
                JSON structure:
                {{
                "predicted_gender": {{"value": "Male", "Female", or "Unisex/Unknown", "confidence": float}},
                "predicted_origin": {{"value": "Likely ethno-geographic origin", "confidence": float}},
                "deduced_language": {{"value": "Language detected in names", "confidence": float}},
                "user_persona": {{"value": "Inferred interest or category", "confidence": float}}
                }}
                """
                try:
                    response = model.generate_content(prompt)
                    cleaned_response = response.text.replace('```json', '').replace('```', '').strip()
                    insights = json.loads(cleaned_response)
                except Exception as e:
                    self.progress.emit(f"Warning: API call failed for {username}. Error: {e}")
                    insights = {"error": str(e)}

                flattened_insights = {}
                if 'error' not in insights:
                    for key, value in insights.items():
                        if isinstance(value, dict):
                            flattened_insights[f'{key}_value'] = value.get('value')
                            flattened_insights[f'{key}_confidence'] = value.get('confidence')
                else:
                    flattened_insights['error'] = insights['error']
                results.append(flattened_insights)
                
                # --- NEW: Pause to respect API rate limits ---
                time.sleep(3) 

            results_df = pd.DataFrame(results)
            final_df = pd.concat([df.reset_index(drop=True), results_df.reset_index(drop=True)], axis=1)
            
            dir_name = os.path.dirname(self.input_filepath)
            base_name = os.path.basename(self.input_filepath)
            file_name, file_ext = os.path.splitext(base_name)
            output_filepath = os.path.join(dir_name, f"{file_name}_output.csv")
            
            final_df.to_csv(output_filepath, index=False)
            self.finished.emit(output_filepath)

        except Exception as e:
            self.error.emit(f"A critical error occurred: {str(e)}")

# --- Main Application Window ---
class PersonaScopeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.input_filepath = None
        self.thread = None
        self.worker = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PersonaScope')
        self.setGeometry(200, 200, 700, 600)
        
        layout = QVBoxLayout()

        # API Key Input
        self.api_key_label = QLabel('Enter Your Gemini API Key:')
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_key_label)
        layout.addWidget(self.api_key_input)

        # File Selection
        self.file_button = QPushButton('1. Browse for Spreadsheet (.xlsx or .csv)')
        self.file_button.clicked.connect(self.browse_file)
        self.file_label = QLabel('No file selected.')
        layout.addWidget(self.file_button)
        layout.addWidget(self.file_label)

        # Column Mapping UI
        self.mapping_widget = QWidget()
        mapping_layout = QHBoxLayout()
        fullname_vbox = QVBoxLayout()
        self.fullname_label = QLabel('2. Select Full Name Column:')
        self.fullname_combo = QComboBox()
        fullname_vbox.addWidget(self.fullname_label)
        fullname_vbox.addWidget(self.fullname_combo)
        username_vbox = QVBoxLayout()
        self.username_label = QLabel('3. Select Username Column:')
        self.username_combo = QComboBox()
        username_vbox.addWidget(self.username_label)
        username_vbox.addWidget(self.username_combo)
        mapping_layout.addLayout(fullname_vbox)
        mapping_layout.addLayout(username_vbox)
        self.mapping_widget.setLayout(mapping_layout)
        layout.addWidget(self.mapping_widget)
        self.mapping_widget.setVisible(False)

        # --- NEW: Run and Stop Buttons in a horizontal layout ---
        button_layout = QHBoxLayout()
        self.run_button = QPushButton('4. Run Analysis')
        self.run_button.clicked.connect(self.start_analysis)
        self.run_button.setEnabled(False) 
        button_layout.addWidget(self.run_button)
        
        self.stop_button = QPushButton('Stop Analysis')
        self.stop_button.clicked.connect(self.stop_analysis)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        # Status Log
        self.log_label = QLabel('Status Log:')
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150) # Keep log area smaller
        layout.addWidget(self.log_label)
        layout.addWidget(self.log_output)
        
        # --- NEW: Results Table ---
        self.results_label = QLabel('Analysis Results:')
        self.results_table = QTableWidget()
        layout.addWidget(self.results_label)
        layout.addWidget(self.results_table)
        self.results_label.setVisible(False)
        self.results_table.setVisible(False)

        self.setLayout(layout)

    def browse_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, 'Select Input File', '', 'Spreadsheet Files (*.xlsx *.csv)')
        if filepath:
            self.input_filepath = filepath
            self.file_label.setText(f'Selected: {os.path.basename(filepath)}')
            self.results_table.setVisible(False) # Hide old results
            self.results_label.setVisible(False)
            try:
                if filepath.endswith('.csv'):
                    headers = pd.read_csv(filepath, nrows=0).columns.tolist()
                else:
                    headers = pd.read_excel(filepath, nrows=0).columns.tolist()
                self.fullname_combo.clear(); self.username_combo.clear()
                self.fullname_combo.addItems(headers); self.username_combo.addItems(headers)
                
                if 'Fullname' in headers: self.fullname_combo.setCurrentText('Fullname')
                if 'Full Name' in headers: self.fullname_combo.setCurrentText('Full Name')
                if 'Username' in headers: self.username_combo.setCurrentText('Username')

                self.mapping_widget.setVisible(True)
                self.run_button.setEnabled(True)
            except Exception as e:
                self.log_output.append(f"Error reading file headers: {e}")
                self.run_button.setEnabled(False)

    def start_analysis(self):
        api_key = self.api_key_input.text()
        fullname_col = self.fullname_combo.currentText()
        username_col = self.username_combo.currentText()
        if not api_key: self.log_output.append("Error: Please enter your Gemini API key."); return
        if not fullname_col or not username_col: self.log_output.append("Error: Please select both a fullname and username column."); return

        self.run_button.setEnabled(False); self.stop_button.setEnabled(True)
        self.file_button.setEnabled(False); self.log_output.clear()
        self.log_output.append("Starting analysis..."); self.results_table.setRowCount(0)

        self.thread = QThread()
        self.worker = Worker(api_key, self.input_filepath, fullname_col, username_col)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.analysis_finished)
        self.worker.error.connect(self.analysis_error)
        self.worker.progress.connect(self.update_log)
        self.worker.finished.connect(self.thread.quit); self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        
    def stop_analysis(self):
        if self.worker:
            self.worker.is_running = False
        self.stop_button.setEnabled(False)
        self.reset_ui_state()

    def update_log(self, message):
        self.log_output.append(message)
    
    def analysis_finished(self, output_filepath):
        self.log_output.append("\nAnalysis complete!")
        self.log_output.append(f"Results saved to: {output_filepath}")
        self.display_results(output_filepath)
        self.reset_ui_state()

    def analysis_error(self, error_message):
        self.log_output.append(f"\nERROR: {error_message}")
        self.reset_ui_state()
        
    def reset_ui_state(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.file_button.setEnabled(True)

    def display_results(self, filepath):
        self.log_output.append("Loading results into table...")
        try:
            df = pd.read_csv(filepath)
            df = df.fillna('') # Replace NaN with empty strings for display
            
            self.results_table.setRowCount(df.shape[0])
            self.results_table.setColumnCount(df.shape[1])
            self.results_table.setHorizontalHeaderLabels(df.columns)
            
            for i in range(df.shape[0]):
                for j in range(df.shape[1]):
                    self.results_table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))
            
            self.results_table.resizeColumnsToContents()
            self.results_table.setVisible(True)
            self.results_label.setVisible(True)
            self.log_output.append("Results loaded successfully.")
        except Exception as e:
            self.log_output.append(f"Error displaying results: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PersonaScopeApp()
    ex.show()
    sys.exit(app.exec())
