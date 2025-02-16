from flask import Flask, request, send_file, render_template
import barcode
from barcode.writer import ImageWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
import os

app = Flask(__name__)  # ✅ Исправлено __name__

def generate_barcode(code, folder="static/barcodes"):
    """Создание штрихкода без встроенного текста, с обрезкой по высоте"""
    if not os.path.exists(folder):
        os.makedirs(folder)  # Создаем папку, если её нет

    barcode_class = barcode.get_barcode_class('code128')
    filename = os.path.join(folder, code)  # Файл без расширения

    try:
        barcode_instance = barcode_class(code, writer=ImageWriter())
        barcode_instance.save(filename, {
            "module_width": 0.3,  
            "module_height": 40,  
            "font_size": 1,  
            "dpi": 300  
        })

        png_path = filename + ".png"
        if not os.path.exists(png_path):
            raise FileNotFoundError(f"Файл {png_path} не был создан!")

        img = Image.open(png_path)
        width, height = img.size
        cropped_img = img.crop((0, 0, width, int(height * 0.5)))  
        cropped_img.save(png_path)

        absolute_path = os.path.abspath(png_path).replace("\\", "/")
        print(f"✅ Штрихкод сохранен: {absolute_path}")

        return absolute_path  
    except Exception as e:
        print(f"❌ Ошибка при создании штрихкода: {e}")
        return None

def generate_pdf(location, count):
    """Генерация PDF, где штрихкоды расположены ближе к левому краю и текст центрирован."""
    pdf_path = os.path.abspath("static/generated_barcodes.pdf").replace("\\", "/")

    if not os.path.exists("static"):
        os.makedirs("static")  

    c = canvas.Canvas(pdf_path, pagesize=letter)
    page_width, page_height = letter  
    margin_x = 20  # Левый отступ
    margin_y = page_height - 100  # Верхний отступ
    row_gap = 105  # Расстояние между штрихкодами
    max_rows = 6  # Количество строк на одной странице
    row = 0  

    for i in range(1, count + 1):
        code = f"{location}{i}"
        img_path = generate_barcode(code)  

        print(f"🔍 Проверка перед вставкой в PDF: {img_path}")  

        if img_path and os.path.exists(img_path):  
            x = margin_x  
            y = margin_y - (row * row_gap)  

            barcode_width = 250  
            barcode_height = 50  
            c.drawImage(img_path, x, y + 20, width=barcode_width, height=barcode_height, mask='auto')

            # 🔥 Устанавливаем шрифт 28 и центрируем текст
            c.setFont("Helvetica-Bold", 28)  # Размер шрифта 28
            text_x = x + (barcode_width / 2) - (len(code) * 7)  # Подгоняем центрирование
            c.drawString(text_x, y - 8, code)  # Текст размещается ниже штрихкода

            row += 1  
            if row >= max_rows:  
                c.showPage()
                row = 0  
                margin_y = page_height - 100  
        else:
            print(f"⚠ Ошибка: Файл {img_path} не найден!")

    c.save()
    print(f"✅ PDF успешно создан: {pdf_path}")
    return pdf_path


@app.route('/')
def home():
    return render_template("index.html")

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    location = data.get("location", "TXT")
    count = int(data.get("count", 60))
    
    print(f"🔹 Генерация PDF для: {location}1 - {location}{count}")

    try:
        pdf_file = generate_pdf(location, count)
        print(f"✅ PDF создан: {pdf_file}")
        return send_file(pdf_file, as_attachment=True)
    except Exception as e:
        print(f"❌ Ошибка при создании PDF: {e}")
        return {"error": str(e)}, 500

if __name__ == '__main__':  # ✅ Исправлено __name__
    app.run(debug=True)
