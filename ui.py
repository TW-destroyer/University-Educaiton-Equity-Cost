"""
Tkinter UI: University Resources & Outcomes Dashboard
--------------------------------------------------------------
This prototype loads CSV datasets and lets users explore relationships
between university funding and student outcomes.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mysql.connector
from dotenv import load_dotenv

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "university_equity"),
}


def get_db_connection():
    """Create and return a new MySQL database connection."""
    return mysql.connector.connect(**DB_CONFIG)


def load_main_dataframe():
    """Load main dashboard data from MySQL into a pandas DataFrame."""
    query = """
        SELECT
            tc.name AS university_name,
            tc.state AS state,
            tc.type AS type,
            tc.in_state_total AS funding_per_student,
            NULL AS graduation_rate
        FROM tuition_cost tc
        LIMIT 5000;
    """
    conn = get_db_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df


class EducationDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("University Resources vs Outcomes")
        self.geometry("1100x700")

        self.df = pd.DataFrame()  # placeholder for loaded dataset

        # Layout of the window
        self.create_header()
        self.create_sidebar()
        self.create_main_area()

    # Header
    def create_header(self):
        header = tk.Label(
            self, text="University Resources & Outcomes Dashboard",
            font=("Segoe UI", 18, "bold"), bg="#2C3E50", fg="white", pady=10
        )
        header.pack(side="top", fill="x")

    # Sidebar
    def create_sidebar(self):
        sidebar = tk.Frame(self, width=250, bg="#ECF0F1")
        sidebar.pack(side="left", fill="y")

        # Load CSV Button
        load_btn = ttk.Button(sidebar, text="Load CSV Dataset", command=self.load_csv)
        load_btn.pack(padx=10, pady=10, fill="x")

        # Load from MySQL Database button
        load_db_btn = ttk.Button(sidebar, text="Load from Database", command=self.load_data_from_db)
        load_db_btn.pack(padx=10, pady=5, fill="x")

        ttk.Label(sidebar, text="Filter by State:", background="#ECF0F1").pack(padx=10, anchor="w", pady=(15, 0))
        self.state_var = tk.StringVar()
        self.state_combo = ttk.Combobox(sidebar, textvariable=self.state_var, state="readonly")
        self.state_combo.pack(padx=10, pady=5, fill="x")

        ttk.Label(sidebar, text="University Type:", background="#ECF0F1").pack(padx=10, anchor="w", pady=(10, 0))
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(sidebar, textvariable=self.type_var, state="readonly")
        self.type_combo.pack(padx=10, pady=5, fill="x")

        ttk.Label(sidebar, text="Chart Metric:", background="#ECF0F1").pack(padx=10, anchor="w", pady=(10, 0))
        self.metric_var = tk.StringVar()
        self.metric_combo = ttk.Combobox(
            sidebar, textvariable=self.metric_var, state="readonly"
        )
        self.metric_combo.pack(padx=10, pady=5, fill="x")

        update_btn = ttk.Button(sidebar, text="Update Charts", command=self.update_charts)
        update_btn.pack(padx=10, pady=20, fill="x")

    # Main Window
    def create_main_area(self):
        main = tk.Frame(self, bg="white")
        main.pack(side="right", fill="both", expand=True)

        # Metrics frame
        metrics_frame = tk.Frame(main, bg="white")
        metrics_frame.pack(fill="x", pady=5)

        self.metric_labels = {
            "universities": tk.Label(metrics_frame, text="Universities: N/A", font=("Segoe UI", 12), bg="white"),
            "avg_funding": tk.Label(metrics_frame, text="Avg Funding: N/A", font=("Segoe UI", 12), bg="white"),
            "avg_grad": tk.Label(metrics_frame, text="Avg Graduation Rate: N/A", font=("Segoe UI", 12), bg="white")
        }
        for lbl in self.metric_labels.values():
            lbl.pack(side="left", padx=25, pady=10)

        # Chart area
        self.chart_frame = tk.Frame(main, bg="white")
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Table
        self.table = ttk.Treeview(main, columns=("Name", "State", "Funding", "GradRate"), show="headings")
        for col in ("Name", "State", "Funding", "GradRate"):
            self.table.heading(col, text=col)
        self.table.pack(fill="both", expand=True, padx=10, pady=5)

    # Logic
    def detect_columns(self):
        """Detect and map columns from the loaded CSV to standard names."""
        # This maps various column names to standardized names
        column_map = {}
        
        # Detect name column
        for col in self.df.columns:
            col_lower = col.lower()
            if 'name' in col_lower and 'state' not in col_lower:
                column_map['name'] = col
                break
        
        # Detect state column
        for col in self.df.columns:
            col_lower = col.lower()
            if col_lower in ['state', 'state_name', 'state_code']:
                column_map['state'] = col
                break
        
        # Detect type/category column
        for col in self.df.columns:
            col_lower = col.lower()
            if col_lower in ['type', 'category', 'income_lvl']:
                column_map['type'] = col
                break
        
        return column_map

    def get_numeric_columns(self):
        """Get all numeric columns from the dataframe."""
        numeric_cols = []
        for col in self.df.columns:
            # Try to convert to numeric
            try:
                pd.to_numeric(self.df[col], errors='coerce')
                # Check if at least 50% of values are numeric
                numeric_count = pd.to_numeric(self.df[col], errors='coerce').notna().sum()
                if numeric_count > len(self.df) * 0.5:
                    numeric_cols.append(col)
            except:
                pass
        return numeric_cols

    def load_data_from_db(self):
        """Load data for the dashboard directly from the MySQL database."""
        try:
            df = load_main_dataframe()
            if df.empty:
                messagebox.showwarning("No Data", "Database query returned no rows.")
                return

            self.df = df
            self.df.columns = [c.strip() for c in self.df.columns]

            self.setup_ui_after_load()
            messagebox.showinfo("Data Loaded", f"Loaded {len(self.df)} rows from database.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load data from MySQL:\n{e}")

    def load_csv(self):
        """Load a CSV file selected by the user."""
        file_path = filedialog.askopenfilename(
            title="Select dataset CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.df = pd.read_csv(file_path)
            self.df.columns = [c.strip() for c in self.df.columns]

            self.setup_ui_after_load()
            messagebox.showinfo("Data Loaded", f"Loaded {len(self.df)} rows successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load CSV: {e}")

    def setup_ui_after_load(self):
        """Setup UI elements after data is loaded."""
        column_map = self.detect_columns()

        # Setup state filter
        if 'state' in column_map:
            states = sorted(self.df[column_map['state']].dropna().unique().tolist())
            self.state_combo["values"] = ["(All)"] + states
            self.state_combo.current(0)
        else:
            self.state_combo["values"] = ["(All)"]
            self.state_combo.current(0)

        # Setup type filter
        if 'type' in column_map:
            types = sorted(self.df[column_map['type']].dropna().unique().tolist())
            self.type_combo["values"] = ["(All)"] + types
            self.type_combo.current(0)
        else:
            self.type_combo["values"] = ["(All)"]
            self.type_combo.current(0)

        # Setup metric dropdown with numeric columns
        numeric_cols = self.get_numeric_columns()
        if numeric_cols:
            self.metric_combo["values"] = numeric_cols
            self.metric_combo.current(0)
            self.metric_var.set(numeric_cols[0])
        else:
            self.metric_combo["values"] = []
            messagebox.showwarning("No Numeric Columns", "No numeric columns found in the dataset.")

        self.update_summary()
        self.update_charts()

    def apply_filters(self):
        """Apply filters to the dataframe."""
        if self.df.empty:
            return self.df

        df = self.df.copy()
        column_map = self.detect_columns()

        # Apply state filter
        if 'state' in column_map and self.state_var.get() and self.state_var.get() != "(All)":
            df = df[df[column_map['state']] == self.state_var.get()]

        # Apply type filter
        if 'type' in column_map and self.type_var.get() and self.type_var.get() != "(All)":
            df = df[df[column_map['type']] == self.type_var.get()]

        return df

    def update_summary(self):
        """Update summary statistics."""
        if self.df.empty:
            return

        df = self.apply_filters()
        column_map = self.detect_columns()

        # Count universities/records
        if 'name' in column_map:
            uni_count = df[column_map['name']].nunique()
            self.metric_labels["universities"].config(text=f"Universities: {uni_count}")
        else:
            self.metric_labels["universities"].config(text=f"Records: {len(df)}")

        # Get current metric for calculations
        metric = self.metric_var.get()
        if metric and metric in df.columns:
            metric_data = pd.to_numeric(df[metric], errors='coerce')
            avg_value = metric_data.mean()
            median_value = metric_data.median()

            if pd.notna(avg_value):
                # Format based on metric name
                if any(word in metric.lower() for word in ['cost', 'tuition', 'price', 'pay', 'salary']):
                    self.metric_labels["avg_funding"].config(text=f"Avg {metric.replace('_', ' ').title()}: ${avg_value:,.2f}")
                    self.metric_labels["avg_grad"].config(text=f"Median {metric.replace('_', ' ').title()}: ${median_value:,.2f}")
                elif 'percent' in metric.lower() or 'pct' in metric.lower():
                    self.metric_labels["avg_funding"].config(text=f"Avg {metric.replace('_', ' ').title()}: {avg_value:.1f}%")
                    self.metric_labels["avg_grad"].config(text=f"Median {metric.replace('_', ' ').title()}: {median_value:.1f}%")
                else:
                    self.metric_labels["avg_funding"].config(text=f"Avg {metric.replace('_', ' ').title()}: {avg_value:,.2f}")
                    self.metric_labels["avg_grad"].config(text=f"Median {metric.replace('_', ' ').title()}: {median_value:,.2f}")
            else:
                self.metric_labels["avg_funding"].config(text="Avg: N/A")
                self.metric_labels["avg_grad"].config(text="Median: N/A")
        else:
            self.metric_labels["avg_funding"].config(text="Avg Funding: N/A")
            self.metric_labels["avg_grad"].config(text="Avg Graduation Rate: N/A")

    def update_charts(self):
        """Update charts and table."""
        if self.df.empty:
            messagebox.showwarning("No Data", "Please load a CSV first.")
            return

        df = self.apply_filters()
        column_map = self.detect_columns()
        self.update_summary()

        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        metric = self.metric_var.get()
        if not metric or metric not in df.columns:
            messagebox.showwarning("Missing Column", f"Please select a valid metric.")
            return

        # Convert metric to numeric
        df_plot = df.copy()
        df_plot[metric] = pd.to_numeric(df_plot[metric], errors='coerce')

        # Create chart
        fig, ax = plt.subplots(figsize=(7, 4))
        
        if 'state' in column_map:
            # Group by state and get top 10 states
            grouped = df_plot.groupby(column_map['state'])[metric].mean().nlargest(10)
            
            if not grouped.empty:
                grouped.plot(kind="bar", ax=ax, color="#3498DB")
                ax.set_title(f"Top 10 States by Average {metric.replace('_',' ').title()}", 
                           fontsize=12, fontweight='bold')
                ax.set_ylabel(metric.replace('_',' ').title())
                ax.set_xlabel("State")
                ax.grid(axis="y", linestyle="--", alpha=0.7)
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
            else:
                ax.text(0.5, 0.5, "No valid data for selected metric", 
                       ha="center", va="center", fontsize=12)
                ax.axis("off")
        else:
            # If no state column, show distribution
            df_plot[metric].dropna().hist(bins=20, ax=ax, color="#3498DB", edgecolor='black')
            ax.set_title(f"Distribution of {metric.replace('_',' ').title()}", 
                        fontsize=12, fontweight='bold')
            ax.set_xlabel(metric.replace('_',' ').title())
            ax.set_ylabel("Frequency")
            ax.grid(axis="y", linestyle="--", alpha=0.7)
            plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Update table
        self.update_table(df, column_map)

    def update_table(self, df, column_map):
        """Update the data table."""
        # Clear existing rows
        for row in self.table.get_children():
            self.table.delete(row)

        # Determine columns to display
        display_cols = []
        col_headers = []
        
        # Name column
        if 'name' in column_map:
            display_cols.append(column_map['name'])
            col_headers.append("Name")
        
        # State column
        if 'state' in column_map:
            display_cols.append(column_map['state'])
            col_headers.append("State")
        
        # Current metric
        metric = self.metric_var.get()
        if metric and metric in df.columns:
            if metric not in display_cols:
                display_cols.append(metric)
                col_headers.append(metric.replace('_', ' ').title())
        
        # Add one more numeric column if available
        numeric_cols = self.get_numeric_columns()
        for col in numeric_cols:
            if col not in display_cols and len(display_cols) < 4:
                display_cols.append(col)
                col_headers.append(col.replace('_', ' ').title())
                break

        # Reconfigure table columns
        self.table["columns"] = col_headers
        for i, header in enumerate(col_headers):
            self.table.heading(header, text=header)
            self.table.column(header, width=200, anchor="w")

        # Insert data
        for _, row in df.head(30).iterrows():
            values = []
            for col in display_cols:
                val = row[col]
                if pd.isna(val):
                    values.append("N/A")
                elif isinstance(val, (int, float)):
                    if isinstance(val, float) and val > 1000:
                        values.append(f"{val:,.2f}")
                    else:
                        values.append(f"{val:,.2f}" if isinstance(val, float) else str(val))
                else:
                    values.append(str(val)[:50])  # Truncate long strings
            self.table.insert("", "end", values=values)

# Run App
if __name__ == "__main__":
    app = EducationDashboard()
    app.mainloop()
