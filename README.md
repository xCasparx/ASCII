# 圖片轉ASCLL工具

這是一個使用 Python 開發的圖片轉ascll工具，可以將圖片中的文字轉換為可編輯的文字格式。

## 功能特點

- 支援多種圖片格式（PNG、JPG、JPEG、BMP）
- 支援繁體中文和英文識別
- 批次處理多張圖片
- 自動保存識別結果

## 安裝需求

1. Python 3.8 或以上版本
2. Tesseract OCR 引擎
3. 必要的 Python 套件（見 requirements.txt）

## 安裝步驟

1. 安裝 Tesseract OCR：
   - 從 [Tesseract 官網](https://github.com/UB-Mannheim/tesseract/wiki) 下載並安裝
   
2. 安裝 Python 套件：
```bash
pip install -r requirements.txt
```

## 注意事項

- 確保圖片清晰度良好
- 支援的圖片格式：PNG、JPG、JPEG、BMP
