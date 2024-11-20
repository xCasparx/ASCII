import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import pyperclip  # 用於複製到剪貼簿

# 定義灰階對應的字符集，字符由深到淺排列
ASCII_CHARS = "@%#*+=-:. "

def resize_image(image, new_width):
    """調整圖片大小，保持寬高比例"""
    width, height = image.size
    aspect_ratio = height / width
    new_height = int(new_width * aspect_ratio * 0.55)  # 調整比例適應字符高度
    return image.resize((new_width, new_height))

def grayify(image):
    """將圖片轉為灰階"""
    return image.convert("L")

def pixels_to_ascii(image):
    """將灰階圖片的像素值轉為 ASCII 字符"""
    pixels = image.getdata()
    ascii_str = "".join([ASCII_CHARS[min(pixel // 25, len(ASCII_CHARS) - 1)] for pixel in pixels])
    return ascii_str

def image_to_ascii(image_path, new_width):
    """將圖片轉為 ASCII 藝術"""
    try:
        image = Image.open(image_path)
    except Exception as e:
        messagebox.showerror("錯誤", f"無法打開圖片：{e}")
        return None
    
    # 調整大小與灰階處理
    image = resize_image(image, new_width)
    image = grayify(image)

    # 生成 ASCII 藝術
    ascii_str = pixels_to_ascii(image)
    ascii_width = image.width
    ascii_art = "\n".join([ascii_str[i:i + ascii_width] for i in range(0, len(ascii_str), ascii_width)])
    
    return ascii_art

def detect_width():
    """自動偵測寬度，根據圖片尺寸計算合理寬度"""
    global selected_image_path
    if not selected_image_path:
        messagebox.showerror("錯誤", "請先選擇圖片！")
        return

    try:
        image = Image.open(selected_image_path)
        width, height = image.size
        # 設定最大和最小寬度限制
        max_width = 200
        min_width = 50
        suggested_width = max(min_width, min(max_width, width // 10))
        width_entry.delete(0, tk.END)
        width_entry.insert(0, str(suggested_width))  # 在寬度輸入框中顯示建議值
        messagebox.showinfo("提示", f"自動偵測的建議寬度為：{suggested_width}")
    except Exception as e:
        messagebox.showerror("錯誤", f"無法偵測圖片寬度：{e}")

def select_image():
    """選擇圖片"""
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

def generate_ascii():
    """生成 ASCII 藝術"""
    global selected_image_path
    if not selected_image_path:
        messagebox.showerror("錯誤", "請先選擇圖片！")
        return

    try:
        new_width = int(width_entry.get())
        if new_width <= 0:
            raise ValueError("寬度必須為正整數")
    except ValueError as e:
        messagebox.showerror("錯誤", f"寬度輸入無效：{e}")
        return

    ascii_art = image_to_ascii(selected_image_path, new_width=new_width)
    if ascii_art:
        # 顯示結果
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, ascii_art)
        # 儲存 ASCII 藝術到檔案
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(ascii_art)
        messagebox.showinfo("完成", "ASCII 藝術已保存到 output.txt")

def copy_to_clipboard():
    """將 ASCII 藝術複製到剪貼簿，適合直接貼到 Discord"""
    global selected_image_path
    if not selected_image_path:
        messagebox.showerror("錯誤", "請先選擇圖片！")
        return

    try:
        new_width = int(width_entry.get())
        if new_width <= 0:
            raise ValueError("寬度必須為正整數")
    except ValueError as e:
        messagebox.showerror("錯誤", f"寬度輸入無效：{e}")
        return

    ascii_art = image_to_ascii(selected_image_path, new_width=new_width)
    if ascii_art:
        # 以程式碼區塊格式複製到剪貼簿
        code_block = "```\n" + ascii_art + "\n```"
        pyperclip.copy(code_block)
        messagebox.showinfo("完成", "ASCII 藝術已複製到剪貼簿，現在可以將它貼到 Discord！")

# 創建主界面
root = tk.Tk()
root.title("圖片轉 ASCII 藝術")

# 標題
title_label = tk.Label(root, text="圖片轉 ASCII 藝術", font=("Arial", 16, "bold"))
title_label.pack(pady=10)

# 寬度輸入框
width_frame = tk.Frame(root)
width_frame.pack(pady=5)
width_label = tk.Label(width_frame, text="輸出寬度：", font=("Arial", 12))
width_label.pack(side=tk.LEFT)
width_entry = tk.Entry(width_frame, width=10, font=("Arial", 12))
width_entry.pack(side=tk.LEFT)
width_entry.insert(0, "100")  # 預設寬度為 100

# 按鈕區域
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# 按鈕
select_button = tk.Button(button_frame, text="選擇圖片", command=select_image, font=("Arial", 12))
select_button.grid(row=0, column=0, padx=5)

detect_button = tk.Button(button_frame, text="自動偵測寬度", command=detect_width, font=("Arial", 12))
detect_button.grid(row=0, column=1, padx=5)

generate_button = tk.Button(button_frame, text="生成 ASCII 藝術", command=generate_ascii, font=("Arial", 12))
generate_button.grid(row=0, column=2, padx=5)

copy_button = tk.Button(button_frame, text="複製至 Discord", command=copy_to_clipboard, font=("Arial", 12))
copy_button.grid(row=0, column=3, padx=5)

# 文本框顯示 ASCII 藝術
output_text = tk.Text(root, wrap=tk.NONE, font=("Courier", 8), bg="black", fg="white")
output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# 全局變量
selected_image_path = None

# 啟動主循環
root.mainloop()
