import tkinter as tk
from  tkinter import ttk
from PIL import Image, ImageTk

root = tk.Tk()

# Create a photoimage object of the image in the path

test = ImageTk.PhotoImage(Image.open("points.png").resize ((100,100)))
label1 = tk.Label(image=test)
label1.grid (row=0, column=0)
root.mainloop()