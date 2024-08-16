import tkinter as tk
from PIL import Image, ImageTk
import mss
import pytesseract
import win32gui
import win32con
import win32api
import ctypes
import pyautogui
from googletrans import Translator
import keyboard

# Get translation of word
def translate_word(word, target_language='pt'):
    translator = Translator()
    try:
        translation = translator.translate(word, dest=target_language)
    except:
        print("Not a valid word")
        return ""
    return translation.text

# Get mouse position
def get_mouse_position():
    return pyautogui.position()

# Preprocess image to grayscale
def preprocess_image(img):
    img = img.convert('L')
    img = img.point(lambda x: 0 if x < 128 else 255)
    return img

# Function to capture the screen and detect text
def capture_and_detect_text():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Capture the primary monitor
        screenshot = sct.grab(monitor)
        img = Image.frombytes('RGB', (screenshot.width, screenshot.height), screenshot.rgb)
        img = preprocess_image(img)
        custom_config = r'--oem 3 --psm 12'
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_config)
        return img, data

# Function to create an overlay window
def create_overlay(screen_width, screen_height):
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    root.attributes('-transparentcolor', '#000000')

    root.geometry(f"{screen_width}x{screen_height}+0+0")

    canvas = tk.Canvas(root, width=screen_width, height=screen_height, highlightthickness=0, bg='black')
    canvas.pack(fill=tk.BOTH, expand=True)

    # Create a label to display the translation
    translation_label = tk.Label(root, bg='#282C34', fg='#61AFEF', font=('Arial', 14))
    translation_label.pack()

    root.update_idletasks()
    root.update()

    hwnd = win32gui.GetForegroundWindow()
    print(f"Window Handle: {hwnd}")

    extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    extended_style |= (win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style)
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, extended_style)
    ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 0, win32con.LWA_COLORKEY)

    return root, canvas, translation_label

# Function to draw highlights on the overlay
def get_word_under_Mouse(canvas, data):
    try:
        canvas.delete('all')
        for i in range(len(data['level'])):
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            text = data['text'][i].strip()
            if text and x <= get_mouse_position().x <= x + w and y <= get_mouse_position().y <= y + h:
                return data['text'][i], x, y, w, h
        return None, None, None, None, None
    except:
        print("Could not retrieve word under mouse")
        return None, None, None, None, None

# Draw Highlight
def highlight_word(canvas, x, y, w, h):
    canvas.create_rectangle(x, y, x + w, y + h, outline='green', width=2)

# Update translation box position and text
def update_translation_box(label, word):
    if word:
        translated_word = translate_word(word, 'pt')
        label.config(text=translated_word)
        mouse_x, mouse_y = get_mouse_position()
        label.place(x=mouse_x + 10, y=mouse_y + 10)  # Position the label near the mouse

# Main function to update the overlay
def main():
    detecting_active = False
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screen_width = monitor['width']
        screen_height = monitor['height']
    
    root, canvas, translation_label = create_overlay(screen_width, screen_height)
    
    while True:
        if keyboard.is_pressed('ctrl') and not detecting_active:
            img, data = capture_and_detect_text()
            detecting_active = True

        if detecting_active:
            word, x, y, w, h = get_word_under_Mouse(canvas, data)
            if word:
                highlight_word(canvas, x, y, w, h)
                update_translation_box(translation_label, word)
            root.update_idletasks()
            root.update()

        if not keyboard.is_pressed('ctrl'):
            canvas.delete('all')
            translation_label.place_forget()
            root.update_idletasks()
            root.update()
            detecting_active = False

if __name__ == "__main__":
    main()
