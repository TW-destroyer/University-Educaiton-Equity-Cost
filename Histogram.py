import tkinter as tk
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np # For generating sample data
import os

os.environ['TCL_LIBRARY'] = r"C:\Users\twsho\AppData\Local\Programs\Python\Python313\tcl\tcl8.6"
os.environ['TK_LIBRARY'] = r"C:\Users\twsho\AppData\Local\Programs\Python\Python313\tcl\tk8.6"
matplotlib.use("TkAgg")

root =tk.Tk()
root.title("histogram")

plot_frame = tk.Frame(root)
plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

fig = Figure(figsize=(6,4), dpi=100)
ax = fig.add_subplot(111)

    # Example data
data = np.random.randn(1000) * 10 + 50 # Gaussian distribution around 50

ax.hist(data, bins=30, edgecolor='black')
ax.set_title("Sample Histogram")
ax.set_xlabel("Value")
ax.set_ylabel("Frequency")

canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

root.mainloop()
