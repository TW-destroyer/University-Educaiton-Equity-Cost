"""
Tkinter Rough Draft UI: University Resources & Outcomes Dashboard
--------------------------------------------------------------
This prototype loads a CSV dataset and lets users explore relationships
between university funding and student outcomes (e.g., graduation rates).
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mysql.connector
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file if present

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
    """Load main dashboard data from MySQL into a pandas DataFrame.

    Adjust the SQL query and aliases to match your schema/columns if needed.
    """
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

# Comment out to run since this is needed for Travis to run
# os.environ['TCL_LIBRARY'] = r"C:\Users\twsho\AppData\Local\Programs\Python\Python313\tcl\tcl8.6"
# os.environ['TK_LIBRARY'] = r"C:\Users\twsho\AppData\Local\Programs\Python\Python313\tcl\tk8.6"
# ...
class EducationDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("University Resources vs Outcomes")
        self.geometry("1100x700")

        self.df = pd.DataFrame()  # placeholder for loaded dataset

        # ---------- LAYOUT ----------
        self.create_header()
        self.create_sidebar()
        self.create_main_area()

    # ---------- Header ----------
    def create_header(self):
        header = tk.Label(
            self, text="University Resources & Outcomes Dashboard",
            font=("Segoe UI", 18, "bold"), bg="#2C3E50", fg="white", pady=10
        )
        header.pack(side="top", fill="x")

    # ---------- Sidebar ----------
    def create_sidebar(self):
        sidebar = tk.Frame(self, width=250, bg="#ECF0F1")
        sidebar.pack(side="left", fill="y")

        # Load CSV Button
        load_btn = ttk.Button(sidebar, text="Load CSV Dataset", command=self.load_csv)
        load_btn.pack(padx=10, pady=10, fill="x")

        # Load from MySQL Database button
        load_db_btn = ttk.Button(sidebar, text="Load from Database", command=self.load_data_from_db)
        load_db_btn.pack(padx=10, pady=5, fill="x")

        ttk.Label(sidebar, text="Filter by State:").pack(padx=10, anchor="w")
        self.state_var = tk.StringVar()
        self.state_combo = ttk.Combobox(sidebar, textvariable=self.state_var, state="readonly")
        self.state_combo.pack(padx=10, pady=5, fill="x")

        ttk.Label(sidebar, text="University Type:").pack(padx=10, anchor="w")
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(sidebar, textvariable=self.type_var, state="readonly")
        self.type_combo.pack(padx=10, pady=5, fill="x")

        ttk.Label(sidebar, text="Chart Metric:").pack(padx=10, anchor="w")
        self.metric_var = tk.StringVar(value="funding_per_student")
        self.metric_combo = ttk.Combobox(
            sidebar, textvariable=self.metric_var,
            values=["funding_per_student", "graduation_rate"], state="readonly"
        )
        self.metric_combo.pack(padx=10, pady=5, fill="x")

        update_btn = ttk.Button(sidebar, text="Update Charts", command=self.update_charts)
        update_btn.pack(padx=10, pady=20, fill="x")

    # ---------- Main Area ----------
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

    # ---------- Logic ----------
    def load_data_from_db(self):
        """Load data for the dashboard directly from the MySQL database."""
        try:
            df = load_main_dataframe()
            if df.empty:
                messagebox.showwarning("No Data", "Database query returned no rows.")
                return

            self.df = df
            self.df.columns = [c.strip() for c in self.df.columns]

            # Populate filters from DB data
            if "state" in self.df.columns:
                states = sorted(self.df["state"].dropna().unique().tolist())
                self.state_combo["values"] = ["(All)"] + states
                self.state_combo.current(0)

            if "type" in self.df.columns:
                types = sorted(self.df["type"].dropna().unique().tolist())
                self.type_combo["values"] = ["(All)"] + types
                self.type_combo.current(0)

            messagebox.showinfo("Data Loaded", f"Loaded {len(self.df)} rows from database.")
            self.update_summary()
            self.update_charts()
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load data from MySQL:\n{e}")

    def load_csv(self):
        file_path = filedialog.askopenfilename(
            title="Select dataset CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.df = pd.read_csv(file_path)
            self.df.columns = [c.strip() for c in self.df.columns]

            # Fill filters
            if "state" in self.df.columns:
                states = sorted(self.df["state"].dropna().unique().tolist())
                self.state_combo["values"] = ["(All)"] + states
                self.state_combo.current(0)

            if "type" in self.df.columns:
                types = sorted(self.df["type"].dropna().unique().tolist())
                self.type_combo["values"] = ["(All)"] + types
                self.type_combo.current(0)

            messagebox.showinfo("Data Loaded", f"Loaded {len(self.df)} rows successfully.")
            self.update_summary()
            self.update_charts()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load CSV: {e}")

    def apply_filters(self):
        if self.df.empty:
            return self.df

        df = self.df.copy()
        if self.state_var.get() and self.state_var.get() != "(All)" and "state" in df.columns:
            df = df[df["state"] == self.state_var.get()]

        if self.type_var.get() and self.type_var.get() != "(All)" and "type" in df.columns:
            df = df[df["type"] == self.type_var.get()]

        return df

    def update_summary(self):
        if self.df.empty:
            return

        df = self.apply_filters()

        uni_count = df["university_name"].nunique() if "university_name" in df.columns else len(df)
        avg_funding = df["funding_per_student"].mean() if "funding_per_student" in df.columns else None
        avg_grad = df["graduation_rate"].mean() if "graduation_rate" in df.columns else None

        self.metric_labels["universities"].config(text=f"Universities: {uni_count}")
        self.metric_labels["avg_funding"].config(
            text=f"Avg Funding: ${avg_funding:,.2f}" if avg_funding else "Avg Funding: N/A")
        self.metric_labels["avg_grad"].config(
            text=f"Avg Graduation Rate: {avg_grad:.2f}%" if avg_grad else "Avg Graduation Rate: N/A")

    def update_charts(self):
        if self.df.empty:
            messagebox.showwarning("No Data", "Please load a CSV first.")
            return

        df = self.apply_filters()
        self.update_summary()

        # clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        metric = self.metric_var.get()
        if metric not in df.columns:
            messagebox.showwarning("Missing Column", f"Column '{metric}' not found in dataset.")
            return

        # plot top 10 states or universities
        if "state" in df.columns:
            grouped = df.groupby("state")[metric].mean().nlargest(10)
            fig, ax = plt.subplots(figsize=(6, 4))
            grouped.plot(kind="bar", ax=ax, color="#3498DB")
            ax.set_title(f"Top 10 States by Average {metric.replace('_',' ').title()}")
            ax.set_ylabel(metric.title())
            ax.grid(axis="y", linestyle="--", alpha=0.7)
        else:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.text(0.5, 0.5, "No 'state' column available", ha="center", va="center", fontsize=12)
            ax.axis("off")

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # update table
        for row in self.table.get_children():
            self.table.delete(row)
        cols = ["university_name", "state", "funding_per_student", "graduation_rate"]
        for _, r in df.head(30)[cols].fillna("N/A").iterrows():
            self.table.insert("", "end", values=(r[cols[0]], r[cols[1]], r[cols[2]], r[cols[3]]))


# ---------- Run App ----------
if __name__ == "__main__":
    app = EducationDashboard()
    app.mainloop()
