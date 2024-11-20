import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import pyperclip
import asyncio

ASCII_CHARS = "@%#*+=-:. "

def resize_image(image, new_width):
    """Resize the image while maintaining aspect ratio."""
    width, height = image.size
    aspect_ratio = height / width
    new_height = int(new_width * aspect_ratio * 0.55)
    return image.resize((new_width, new_height))

def grayify(image):
    """Convert image to grayscale."""
    return image.convert("L")

def pixels_to_ascii(image):
    """Convert image pixels to ASCII characters."""
    pixels = list(image.getdata())
    return ''.join([ASCII_CHARS[min(pixel // 25, len(ASCII_CHARS) - 1)] for pixel in pixels])

async def image_to_ascii(image_path, new_width):
    """Convert image to ASCII art asynchronously."""
    try:
        with Image.open(image_path) as image:
            image = resize_image(image, new_width)
            image = grayify(image)
            ascii_str = pixels_to_ascii(image)
            ascii_width = image.width
            return '\n'.join([ascii_str[i:i + ascii_width] for i in range(0, len(ascii_str), ascii_width)])
    except Exception as e:
        return f"Error: {e}"

def select_image():
    """Open file dialog to select an image."""
    global selected_image_path
    file_path = filedialog.askopenfilename(
        title="選擇圖片",
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
    )
    if file_path:
        selected_image_path = file_path
        messagebox.showinfo("提示", "圖片已選擇成功！")
    else:
        selected_image_path = None

def detect_width():
    """自動偵測圖片寬度並建議合適的 ASCII 輸出寬度"""
    global selected_image_path
    if not selected_image_path:
        messagebox.showerror("錯誤", "請先選擇圖片！")
        return
    try:
        with Image.open(selected_image_path) as image:
            width, height = image.size
            suggested_width = max(50, min(200, width // 10))  # 限制建議寬度範圍
            width_entry.delete(0, tk.END)  # 清空寬度輸入框
            width_entry.insert(0, str(suggested_width))  # 插入建議寬度
        messagebox.showinfo("提示", f"自動偵測的建議寬度為：{suggested_width}")
    except Exception as e:
        messagebox.showerror("錯誤", f"無法偵測圖片寬度：{e}")

async def generate_ascii():
    """Generate ASCII art and save it to a file."""
    global selected_image_path
    if not selected_image_path:
        messagebox.showerror("錯誤", "請先選擇圖片！")
        return

    try:
        new_width = int(width_entry.get())
        if new_width <= 0:
            raise ValueError("寬度必須為正整數")
        ascii_art = await image_to_ascii(selected_image_path, new_width)
        if ascii_art:
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, ascii_art)
            with open("output.txt", "w", encoding="utf-8") as f:
                f.write(ascii_art)
            messagebox.showinfo("完成", "ASCII 藝術已保存到 output.txt")
    except ValueError as e:
        messagebox.showerror("錯誤", f"寬度輸入無效：{e}")

def copy_to_clipboard():
    """Copy ASCII art to clipboard in a code block format."""
    global selected_image_path
    if not selected_image_path:
        messagebox.showerror("錯誤", "請先選擇圖片！")
        return

    try:
        new_width = int(width_entry.get())
        if new_width <= 0:
            raise ValueError("寬度必須為正整數")
        asyncio.run(generate_ascii())
        ascii_art = output_text.get("1.0", tk.END).strip()
        if ascii_art:
            code_block = "```\n" + ascii_art + "\n```"
            pyperclip.copy(code_block)
            messagebox.showinfo("完成", "ASCII 藝術已複製到剪貼簿，現在可以將它貼到 Discord！")
    except ValueError as e:
        messagebox.showerror("錯誤", f"寬度輸入無效：{e}")

def on_closing():
    """Handle window closing event."""
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.quit()

# GUI Setup
root = tk.Tk()
root.title("圖片轉 ASCII 藝術")
root.configure(bg="#2C3E50")  # 設置背景顏色

# Title
title_label = tk.Label(root, text="圖片轉 ASCII 藝術", font=("Segoe UI", 18, "bold"), fg="#ECF0F1", bg="#2C3E50")
title_label.pack(pady=20)

# Width entry
width_frame = tk.Frame(root, bg="#2C3E50")
width_frame.pack(pady=10)
width_label = tk.Label(width_frame, text="輸出寬度：", font=("Segoe UI", 12), fg="#ECF0F1", bg="#2C3E50")
width_label.pack(side=tk.LEFT, padx=10)
width_entry = tk.Entry(width_frame, width=10, font=("Segoe UI", 12), bg="#34495E", fg="#ECF0F1", borderwidth=2, relief="solid")
width_entry.pack(side=tk.LEFT, padx=10)
width_entry.insert(0, "100")

# Button area
button_frame = tk.Frame(root, bg="#2C3E50")
button_frame.pack(pady=20)

# Buttons
select_button = tk.Button(button_frame, text="選擇圖片", command=select_image, font=("Segoe UI", 12), bg="#3498DB", fg="white", relief="flat", padx=10, pady=5)
select_button.grid(row=0, column=0, padx=10)

detect_button = tk.Button(button_frame, text="自動偵測寬度", command=detect_width, font=("Segoe UI", 12), bg="#2ECC71", fg="white", relief="flat", padx=10, pady=5)
detect_button.grid(row=0, column=1, padx=10)

generate_button = tk.Button(button_frame, text="生成 ASCII 藝術", command=lambda: asyncio.run(generate_ascii()), font=("Segoe UI", 12), bg="#E74C3C", fg="white", relief="flat", padx=10, pady=5)
generate_button.grid(row=0, column=2, padx=10)

copy_button = tk.Button(button_frame, text="複製至 Discord", command=copy_to_clipboard, font=("Segoe UI", 12), bg="#F39C12", fg="white", relief="flat", padx=10, pady=5)
copy_button.grid(row=0, column=3, padx=10)

# Text box to display ASCII art with vertical and horizontal scrollbar
text_frame = tk.Frame(root, bg="#2C3E50")
text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

x_scrollbar = tk.Scrollbar(text_frame, orient="horizontal")
x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

y_scrollbar = tk.Scrollbar(text_frame, orient="vertical")
y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

output_text = tk.Text(
    text_frame,
    wrap=tk.NONE,
    font=("Courier", 8),
    bg="#2C3E50",
    fg="white",
    xscrollcommand=x_scrollbar.set,
    yscrollcommand=y_scrollbar.set,
    borderwidth=2,
    relief="solid"
)
output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
x_scrollbar.config(command=output_text.xview)
y_scrollbar.config(command=output_text.yview)

# Global Variables
selected_image_path = None

# Handle window closing
root.protocol("WM_DELETE_WINDOW", on_closing)

# Run the application
if __name__ == "__main__":
    root.mainloop()
