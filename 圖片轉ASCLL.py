#說明：

#1. threading 替換 asyncio ：導入了 threading 模塊。
#2. 同步圖像轉換 ： `image_to_ascii` 被重命名為 `image_to_ascii_sync` 並移除了 async 關鍵字。錯誤處理現在使用 root.after(0, ...) 將 messagebox 調用安排回主線程執行。
#3. 線程化生成 ：創建了 `generate_ascii_threaded` 函數，它會啟動一個新線程來運行 `run_image_conversion` 。 `run_image_conversion` 包含實際的圖像轉換和文件保存邏輯。GUI 更新（如更新文本框、顯示消息框）通過 root.after(0, ...) 被調度回主線程執行。
#4. 線程化保存圖片 ：創建了 `save_ascii_as_image_threaded` 和 `run_image_saving` 來在後台線程中執行 `text_to_image` 。
#5. 禁用/啟用按鈕 ：添加了 `disable_buttons` 和 `enable_buttons` 輔助函數，在耗時操作開始時禁用所有按鈕，操作完成後再啟用它們，以提供更好的用戶反饋並防止用戶在處理過程中觸發其他操作。
#6. 優化 copy_to_clipboard ： `copy_to_clipboard` 現在直接從 output_text 獲取內容，不再調用生成函數。添加了對 pyperclip 可能拋出的異常的處理。
#7. 改進 text_to_image ：
  # - 添加了對 mingliu.ttc 字體加載失敗的回退處理，嘗試使用 Pillow 的默認字體。
  # - 使用 font.getbbox() (推薦) 或 draw.textsize() (舊版兼容) 來更準確地計算文本尺寸，以確定最終圖像的大小。
  # - 將錯誤和成功消息的顯示也放到了 root.after(0, ...) 中，確保從線程安全地更新 GUI。
#8. 更新按鈕命令 ：將"生成 ASCII 藝術"和"保存為圖片"按鈕的 command 分別指向新的線程化函數 `generate_ascii_threaded` 和 `save_ascii_as_image_threaded` 。
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk
import pyperclip
import threading
import logging
import os
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ascii_converter.log'),
        logging.StreamHandler()
    ]
)

ASCII_CHARS = "@%#*+=-:. "

# ... resize_image, grayify, pixels_to_ascii 函數保持不變 ...

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

# 將 image_to_ascii 改為同步函數
def image_to_ascii_sync(image_path, new_width):
    """Convert image to ASCII art synchronously."""
    try:
        with Image.open(image_path) as image:
            image = resize_image(image, new_width)
            image = grayify(image)
            ascii_str = pixels_to_ascii(image)
            ascii_width = image.width
            return '\n'.join([ascii_str[i:i + ascii_width] for i in range(0, len(ascii_str), ascii_width)])
    except Exception as e:
        # 在主線程中顯示錯誤信息
        root.after(0, lambda: messagebox.showerror("錯誤", f"圖片轉換失敗：{e}"))
        return None

# ... select_image, detect_width 函數保持不變 ...
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


# 修改 generate_ascii 以使用線程
def generate_ascii_threaded():
    """Generate ASCII art in a separate thread."""
    global selected_image_path
    if not selected_image_path:
        messagebox.showerror("錯誤", "請先選擇圖片！")
        return

    try:
        new_width = int(width_entry.get())
        if new_width <= 0:
            raise ValueError("寬度必須為正整數")

        # 禁用按鈕，防止重複點擊
        disable_buttons()

        # 在新線程中執行圖片轉換
        thread = threading.Thread(target=run_image_conversion, args=(selected_image_path, new_width))
        thread.start()

    except ValueError as e:
        messagebox.showerror("錯誤", f"寬度輸入無效：{e}")
        enable_buttons() # 出錯時恢復按鈕

def run_image_conversion(image_path, new_width):
    """Worker function for image conversion."""
    ascii_art = image_to_ascii_sync(image_path, new_width)
    if ascii_art:
        # 使用 root.after 將 GUI 更新操作放回主線程
        root.after(0, update_output_text, ascii_art)
        try:
            with open("output.txt", "w", encoding="utf-8") as f:
                f.write(ascii_art)
            root.after(0, lambda: messagebox.showinfo("完成", "ASCII 藝術已保存到 output.txt"))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("錯誤", f"保存文件失敗: {e}"))
    # 轉換完成後，在主線程中啟用按鈕
    root.after(0, enable_buttons)

def update_output_text(ascii_art):
    """Update the output text widget in the main thread."""
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, ascii_art)

def copy_to_clipboard():
    """Copy ASCII art from the text widget to clipboard."""
    ascii_art = output_text.get("1.0", tk.END).strip()
    if ascii_art:
        code_block = "```\n" + ascii_art + "\n```"
        try:
            pyperclip.copy(code_block)
            messagebox.showinfo("完成", "ASCII 藝術已複製到剪貼簿，現在可以將它貼到 Discord！")
        except pyperclip.PyperclipException as e:
             messagebox.showerror("錯誤", f"複製到剪貼簿失敗: {e}\n請確保已安裝 xclip (Linux) 或其他剪貼簿工具。")
    else:
        messagebox.showerror("錯誤", "請先生成 ASCII 藝術！")

# ... on_closing 函數保持不變 ...
def on_closing():
    """Handle window closing event."""
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.quit()

# 修改 text_to_image 以便在線程中調用，並處理潛在的字體錯誤
def text_to_image(text, font_path="mingliu.ttc", font_size=10, output_path="ascii_image.png"):
    """將 ASCII 藝術轉換為圖片並保存 (可在線程中安全調用)"""
    try:
        # 嘗試加載字體
        try:
            font = ImageFont.truetype(font_path, font_size, encoding="unic")
        except IOError:
            # 如果找不到指定字體，嘗試使用 Pillow 的默認字體
            print(f"警告：找不到字體 {font_path}，嘗試使用默認字體。")
            try:
                font = ImageFont.load_default()
                # 重新計算字體大小，因為默認字體大小可能不同
                # 注意：Pillow 的默認字體是點陣字體，效果可能不如 truetype
                # 這裡的 font_size 可能需要調整或忽略
            except IOError:
                 # 如果連默認字體都加載失敗
                 root.after(0, lambda: messagebox.showerror("錯誤", "無法加載字體，無法生成圖片。"))
                 return False # 表示失敗

        lines = text.split('\n')
        # 使用 getbbox 計算文本邊界，更精確地確定圖像尺寸
        max_width = 0
        total_height = 0
        line_heights = []

        # Pillow 9.2.0 及之後版本推薦使用 getbbox
        if hasattr(font, 'getbbox'):
            for line in lines:
                 # left, top, right, bottom
                 bbox = font.getbbox(line)
                 line_width = bbox[2] - bbox[0]
                 line_height = bbox[3] - bbox[1]
                 max_width = max(max_width, line_width)
                 total_height += line_height
                 line_heights.append(line_height)
            # 可能需要添加一些邊距
            padding = 5
            width = max_width + 2 * padding
            height = total_height + 2 * padding
            # 創建空白圖片，背景為灰色
            image = Image.new("RGB", (width, height), color="#2C3E50")
            draw = ImageDraw.Draw(image)
            current_y = padding
            for i, line in enumerate(lines):
                bbox = font.getbbox(line)
                # 使用 bbox[1] 作為 y 偏移量的參考可能更準確
                draw.text((padding, current_y - bbox[1]), line, font=font, fill="white")
                current_y += line_heights[i]

        else: # 兼容舊版 Pillow (使用 getsize)
             for line in lines:
                 try:
                    # 舊版 Pillow 使用 getsize
                    line_width, line_height = draw.textsize(line, font=font)
                 except AttributeError: # 如果連 textsize 都沒有 (非常舊的版本)
                     root.after(0, lambda: messagebox.showerror("錯誤", "Pillow 版本過舊或 textsize 不可用。"))
                     return False
                 max_width = max(max_width, line_width)
                 line_heights.append(line_height)
                 total_height += line_height
             padding = 5
             width = max_width + 2 * padding
             height = total_height + 2 * padding
             image = Image.new("RGB", (width, height), color="#2C3E50")
             draw = ImageDraw.Draw(image)
             current_y = padding
             for i, line in enumerate(lines):
                 draw.text((padding, current_y), line, font=font, fill="white")
                 current_y += line_heights[i]


        # 保存圖片
        image.save(output_path)
        return True # 表示成功
    except Exception as e:
        # 在主線程中顯示錯誤
        root.after(0, lambda: messagebox.showerror("錯誤", f"轉換為圖片時發生錯誤：{e}"))
        return False # 表示失敗

# 修改 save_ascii_as_image 以使用線程
def save_ascii_as_image_threaded():
    """Save the displayed ASCII art as an image in a separate thread."""
    ascii_art = output_text.get("1.0", tk.END).strip()
    if not ascii_art:
        messagebox.showerror("錯誤", "目前沒有顯示 ASCII 藝術！")
        return

    # 禁用按鈕
    disable_buttons()

    # 在新線程中執行圖片保存
    thread = threading.Thread(target=run_image_saving, args=(ascii_art,))
    thread.start()

def run_image_saving(ascii_art):
    """Worker function for saving ASCII art as an image."""
    output_filename = "ascii_image.png"
    success = text_to_image(ascii_art, output_path=output_filename)
    if success:
        # 在主線程中顯示成功消息
        root.after(0, lambda: messagebox.showinfo("完成", f"ASCII 藝術已保存為圖片：{output_filename}"))
    # 操作完成後，在主線程中啟用按鈕
    root.after(0, enable_buttons)

# --- GUI Setup ---
root = tk.Tk()
root.title("圖片轉 ASCII 藝術")
root.configure(bg="#2C3E50")  # 設置背景顏色

# ... Title, Width entry ...
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

# Buttons - 修改 command 以調用線程函數
select_button = tk.Button(button_frame, text="選擇圖片", command=select_image, font=("Segoe UI", 12), bg="#3498DB", fg="white", relief="flat", padx=10, pady=5)
select_button.grid(row=0, column=0, padx=10)

detect_button = tk.Button(button_frame, text="自動偵測寬度", command=detect_width, font=("Segoe UI", 12), bg="#2ECC71", fg="white", relief="flat", padx=10, pady=5)
detect_button.grid(row=0, column=1, padx=10)

# 修改 generate_button 的 command
generate_button = tk.Button(button_frame, text="生成 ASCII 藝術", command=generate_ascii_threaded, font=("Segoe UI", 12), bg="#E74C3C", fg="white", relief="flat", padx=10, pady=5)
generate_button.grid(row=0, column=2, padx=10)

# copy_button 的 command 不變，因為它現在很快
copy_button = tk.Button(button_frame, text="複製至 Discord", command=copy_to_clipboard, font=("Segoe UI", 12), bg="#F39C12", fg="white", relief="flat", padx=10, pady=5)
copy_button.grid(row=0, column=3, padx=10)

# 修改 save_image_button 的 command
save_image_button = tk.Button(button_frame, text="保存為圖片", command=save_ascii_as_image_threaded, font=("Segoe UI", 12), bg="#9B59B6", fg="white", relief="flat", padx=10, pady=5)
save_image_button.grid(row=0, column=4, padx=10)

# Helper functions to disable/enable buttons during processing
all_buttons = [select_button, detect_button, generate_button, copy_button, save_image_button]
def disable_buttons():
    for btn in all_buttons:
        btn.config(state=tk.DISABLED)

def enable_buttons():
    for btn in all_buttons:
        btn.config(state=tk.NORMAL)


# ... Text box setup ...
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
