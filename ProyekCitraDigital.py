import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

class ChromaKeyApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Aplikasi Penambahan Backgruound Pada Bingkai")
        self.master.geometry("900x700")
        self.master.configure(bg="#1e1e2f")

        self.image_path = None
        self.bg_path = None
        self.result_image = None

        self.selected_color = tk.StringVar(value="Hijau")

        title_label = tk.Label(master, text="Aplikasi Penambahan Backgruound Pada Bingkai", font=("Helvetica", 20, "bold"), bg="#1e1e2f", fg="#ffffff")
        title_label.pack(pady=10)

        self.button_frame = tk.Frame(master, bg="#1e1e2f")
        self.button_frame.pack(pady=10)

        btn_style = {"font": ("Helvetica", 12), "bg": "#4e8cff", "fg": "white", "width": 20}

        self.select_image_btn = tk.Button(self.button_frame, text="Pilih Gambar Latar", command=self.select_image, **btn_style)
        self.select_image_btn.grid(row=0, column=0, padx=5)

        self.select_bg_btn = tk.Button(self.button_frame, text="Pilih Gambar Utama", command=self.select_background, **btn_style)
        self.select_bg_btn.grid(row=0, column=1, padx=5)

        self.process_btn = tk.Button(self.button_frame, text="Tampilkan Hasil", command=self.process_image, **btn_style)
        self.process_btn.grid(row=0, column=2, padx=5)

        self.reset_btn = tk.Button(self.button_frame, text="Reset", command=self.reset_images, **btn_style)
        self.reset_btn.grid(row=0, column=3, padx=5)

        self.save_btn = tk.Button(self.button_frame, text="Simpan Hasil", command=self.save_image, **btn_style)
        self.save_btn.grid(row=0, column=4, padx=5)

        color_label = tk.Label(self.button_frame, text="Klik pada gambar untuk pilih warna latar", bg="#1e1e2f", fg="white", font=("Helvetica", 12))
        color_label.grid(row=1, column=0, columnspan=5, pady=10)

        self.image_label = tk.Label(master, bg="#1e1e2f")
        self.image_label.pack(pady=20)
        self.image_label.bind("<Button-1>", self.pick_color_from_click)

        self.custom_color = (237, 237, 237)

        self.cv_image = None  # Untuk menyimpan gambar utama dalam format OpenCV

    def select_image(self):
        path = filedialog.askopenfilename(title="Pilih Gambar Latar", filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        if path:
            self.image_path = path
            self.cv_image = cv2.imread(self.image_path)
            img_rgb = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_pil.thumbnail((800, 500))
            self.tk_img = ImageTk.PhotoImage(img_pil)
            self.image_label.configure(image=self.tk_img)
            self.image_label.image = self.tk_img
            messagebox.showinfo("Info", "Gambar Latar berhasil dipilih.")

    def select_background(self):
        path = filedialog.askopenfilename(title="Pilih Gambar Utama", filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        if path:
            self.bg_path = path
            messagebox.showinfo("Info", "Gambar Utama belakang berhasil dipilih.")

    def pick_color_from_click(self, event):
        if self.cv_image is None:
            return

        img = self.cv_image.copy()
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_pil.thumbnail((800, 500))
        scale_x = img.shape[1] / img_pil.size[0]
        scale_y = img.shape[0] / img_pil.size[1]
        x = int(event.x * scale_x)
        y = int(event.y * scale_y)

        if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
            b, g, r = img[y, x]
            self.custom_color = (r, g, b)
            messagebox.showinfo("Warna Dipilih", f"RGB: {self.custom_color}")

    def process_image(self):
        if not self.image_path or not self.bg_path:
            messagebox.showwarning("Peringatan", "Silakan pilih gambar utama dan latar terlebih dahulu.")
            return

        image = cv2.imread(self.image_path)
        background = cv2.imread(self.bg_path)
        if image is None or background is None:
            messagebox.showerror("Error", "Gambar tidak valid atau rusak.")
            return

        h, w = image.shape[:2]
        bg_h, bg_w = background.shape[:2]

        bg_ratio = bg_w / bg_h
        image_ratio = w / h

        if bg_ratio > image_ratio:
            new_width = int(h * bg_ratio)
            new_height = h
        else:
            new_width = w
            new_height = int(w / bg_ratio)

        background = cv2.resize(background, (new_width, new_height))
        top = (new_height - h) // 2
        bottom = new_height - h - top
        left = (new_width - w) // 2
        right = new_width - w - left
        background = background[top:top+h, left:left+w]

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        r, g, b = self.custom_color
        color_bgr = np.uint8([[[b, g, r]]])
        hsv_color = cv2.cvtColor(color_bgr, cv2.COLOR_BGR2HSV)[0][0]

        h_val, s_val, v_val = hsv_color
        lower = np.array([max(h_val - 10, 0), 80, 80])
        upper = np.array([min(h_val + 10, 179), 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.resize(mask, (w, h))

        # Hilangkan noise menggunakan morphological operations ---
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)

        mask_inv = cv2.bitwise_not(mask)

        fg = cv2.bitwise_and(image, image, mask=mask_inv)
        bg = cv2.bitwise_and(background, background, mask=mask)
        result = cv2.add(fg, bg)
        self.result_image = result

        img_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_pil.thumbnail((800, 500))
        img_tk = ImageTk.PhotoImage(img_pil)

        self.image_label.configure(image=img_tk)
        self.image_label.image = img_tk

    def reset_images(self):
        self.image_path = None
        self.bg_path = None
        self.result_image = None
        self.custom_color = (237, 237, 237)
        self.image_label.configure(image=None)
        self.image_label.image = None
        self.cv_image = None
        messagebox.showinfo("Reset", "Gambar dan data berhasil direset.")

    def save_image(self):
        if self.result_image is None:
            messagebox.showwarning("Peringatan", "Belum ada hasil untuk disimpan.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg;*.jpeg")])
        if path:
            cv2.imwrite(path, self.result_image)
            messagebox.showinfo("Info", f"Gambar berhasil disimpan di {path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChromaKeyApp(root)
    root.mainloop()
