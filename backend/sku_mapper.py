import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import pandas as pd
import os
import logging
from fuzzywuzzy import process
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SKUMappingTool:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("SKU Mapping Tool - WMS MVP")
        self.root.geometry("1200x800")
        
        # Initialize data
        self.mapping_df = None
        self.sales_df = None
        self.sku_to_msku = {}
        self.unmapped_skus = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="🏭 SKU Mapping Tool", 
                                  font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=10)
        
        # File upload section
        self.create_file_upload_section(main_frame)
        
        # Mapping display section
        self.create_mapping_display_section(main_frame)
        
        # Results section
        self.create_results_section(main_frame)
        
    def create_file_upload_section(self, parent):
        upload_frame = ctk.CTkFrame(parent)
        upload_frame.pack(fill="x", padx=10, pady=10)
        
        # Mapping file upload
        mapping_label = ctk.CTkLabel(upload_frame, text="📋 SKU Mapping File (CSV/Excel):")
        mapping_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        mapping_button = ctk.CTkButton(upload_frame, text="Select Mapping File", 
                                      command=self.load_mapping_file)
        mapping_button.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Sales data upload
        sales_label = ctk.CTkLabel(upload_frame, text="📊 Sales Data File (CSV/Excel/JSON):")
        sales_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        sales_button = ctk.CTkButton(upload_frame, text="Select Sales File", 
                                    command=self.load_sales_file)
        sales_button.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Process button
        process_button = ctk.CTkButton(upload_frame, text="🔄 Process Mapping", 
                                      command=self.process_mapping,
                                      fg_color="green")
        process_button.pack(anchor="w", padx=10, pady=(10, 10))
        
    def create_mapping_display_section(self, parent):
        display_frame = ctk.CTkFrame(parent)
        display_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(display_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Mapping tab
        self.mapping_tab = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.mapping_tab, text="SKU Mappings")
        
        # Sales data tab
        self.sales_tab = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.sales_tab, text="Sales Data")
        
        # Results tab
        self.results_tab = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.results_tab, text="Mapping Results")
        
    def create_results_section(self, parent):
        results_frame = ctk.CTkFrame(parent)
        results_frame.pack(fill="x", padx=10, pady=10)
        
        # Stats
        self.stats_label = ctk.CTkLabel(results_frame, text="📈 Statistics: No data loaded")
        self.stats_label.pack(anchor="w", padx=10, pady=5)
        
        # Export button
        export_button = ctk.CTkButton(results_frame, text="💾 Export Results", 
                                     command=self.export_results)
        export_button.pack(anchor="w", padx=10, pady=5)
        
    def load_mapping_file(self):
        file_path = filedialog.askopenfilename(
            title="Select SKU Mapping File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.mapping_df = pd.read_csv(file_path)
                else:
                    self.mapping_df = pd.read_excel(file_path)
                
                # Validate columns
                required_cols = ['SKU', 'MSKU']
                if not all(col in self.mapping_df.columns for col in required_cols):
                    messagebox.showerror("Error", f"Mapping file must contain columns: {required_cols}")
                    return
                
                # Create mapping dictionary
                self.sku_to_msku = dict(zip(self.mapping_df['SKU'], self.mapping_df['MSKU']))
                
                # Update display
                self.update_mapping_display()
                
                messagebox.showinfo("Success", f"Loaded {len(self.mapping_df)} SKU mappings")
                logger.info(f"Loaded mapping file: {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load mapping file: {str(e)}")
                logger.error(f"Error loading mapping file: {e}")
    
    def load_sales_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Sales Data File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), 
                      ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    self.sales_df = pd.DataFrame(data)
                elif file_path.endswith('.csv'):
                    self.sales_df = pd.read_csv(file_path)
                else:
                    self.sales_df = pd.read_excel(file_path)
                
                # Update display
                self.update_sales_display()
                
                messagebox.showinfo("Success", f"Loaded {len(self.sales_df)} sales records")
                logger.info(f"Loaded sales file: {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load sales file: {str(e)}")
                logger.error(f"Error loading sales file: {e}")
    
    def update_mapping_display(self):
        # Clear existing widgets
        for widget in self.mapping_tab.winfo_children():
            widget.destroy()
        
        if self.mapping_df is not None:
            # Create treeview
            tree = ttk.Treeview(self.mapping_tab, columns=list(self.mapping_df.columns), show="headings")
            
            # Set column headings
            for col in self.mapping_df.columns:
                tree.heading(col, text=col)
                tree.column(col, width=150)
            
            # Add data
            for idx, row in self.mapping_df.iterrows():
                tree.insert("", "end", values=list(row))
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(self.mapping_tab, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
    
    def update_sales_display(self):
        # Clear existing widgets
        for widget in self.sales_tab.winfo_children():
            widget.destroy()
        
        if self.sales_df is not None:
            # Create treeview
            tree = ttk.Treeview(self.sales_tab, columns=list(self.sales_df.columns), show="headings")
            
            # Set column headings
            for col in self.sales_df.columns:
                tree.heading(col, text=col)
                tree.column(col, width=150)
            
            # Add data (limit to first 100 rows for performance)
            for idx, row in self.sales_df.head(100).iterrows():
                tree.insert("", "end", values=list(row))
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(self.sales_tab, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
    
    def process_mapping(self):
        if self.sales_df is None or self.sku_to_msku == {}:
            messagebox.showwarning("Warning", "Please load both mapping and sales files first")
            return
        
        try:
            # Find SKU column in sales data
            sku_column = None
            for col in self.sales_df.columns:
                if 'sku' in col.lower():
                    sku_column = col
                    break
            
            if sku_column is None:
                messagebox.showerror("Error", "No SKU column found in sales data")
                return
            
            # Apply mapping
            self.sales_df['MSKU'] = self.sales_df[sku_column].apply(self.map_sku)
            
            # Find unmapped SKUs
            self.unmapped_skus = self.sales_df[self.sales_df['MSKU'] == 'Unmapped'][sku_column].unique()
            
            # Update results display
            self.update_results_display()
            
            # Update statistics
            total_records = len(self.sales_df)
            mapped_records = len(self.sales_df[self.sales_df['MSKU'] != 'Unmapped'])
            unmapped_count = len(self.unmapped_skus)
            
            stats_text = f"📈 Statistics: {mapped_records}/{total_records} records mapped ({mapped_records/total_records*100:.1f}%)"
            if unmapped_count > 0:
                stats_text += f" | {unmapped_count} unmapped SKUs"
            
            self.stats_label.configure(text=stats_text)
            
            messagebox.showinfo("Success", f"Mapping completed!\n{mapped_records}/{total_records} records mapped")
            logger.info(f"Mapping completed: {mapped_records}/{total_records} records mapped")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process mapping: {str(e)}")
            logger.error(f"Error processing mapping: {e}")
    
    def map_sku(self, sku):
        if pd.isna(sku):
            return "Unmapped"
        
        # Normalize SKU
        sku_str = str(sku).strip().upper()
        
        # Direct mapping
        if sku_str in self.sku_to_msku:
            return self.sku_to_msku[sku_str]
        
        # Fuzzy matching for similar SKUs
        if len(self.sku_to_msku) > 0:
            best_match = process.extractOne(sku_str, self.sku_to_msku.keys())
            if best_match and best_match[1] >= 80:  # 80% similarity threshold
                return self.sku_to_msku[best_match[0]]
        
        return "Unmapped"
    
    def update_results_display(self):
        # Clear existing widgets
        for widget in self.results_tab.winfo_children():
            widget.destroy()
        
        if self.sales_df is not None:
            # Create treeview
            tree = ttk.Treeview(self.results_tab, columns=list(self.sales_df.columns), show="headings")
            
            # Set column headings
            for col in self.sales_df.columns:
                tree.heading(col, text=col)
                tree.column(col, width=150)
            
            # Add data (limit to first 100 rows for performance)
            for idx, row in self.sales_df.head(100).iterrows():
                tree.insert("", "end", values=list(row))
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(self.results_tab, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
    
    def export_results(self):
        if self.sales_df is None:
            messagebox.showwarning("Warning", "No data to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.sales_df.to_csv(file_path, index=False)
                else:
                    self.sales_df.to_excel(file_path, index=False)
                
                messagebox.showinfo("Success", f"Results exported to {file_path}")
                logger.info(f"Results exported to: {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results: {str(e)}")
                logger.error(f"Error exporting results: {e}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SKUMappingTool()
    app.run() 