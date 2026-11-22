bu kod odamlarni suratga oladi bildirmasdan!



import datetime
import os
import time
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
from PIL import Image, ImageTk


class AutoCameraApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Avtomatik Kamera — Odamni Rasmga Olish")
        self.root.geometry("920x660")
        self.root.resizable(False, False)

        self.save_dir = "captures"
        os.makedirs(self.save_dir, exist_ok=True)

        # OpenCV yuz (odam) aniqlash modeli
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            messagebox.showerror("Xatolik", "Yuz aniqlash (Haar Cascade) modeli yuklanmadi.")

        self.cap = None
        self.running = False
        self.auto_capture = True
        self.last_capture_time = 0.0
        self.cooldown_seconds = 3.0  # Bir xil odam uchun qayta rasmga olish oralig'i (soniya)
        self.captured_count = 0
        self.current_frame = None

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Kamera:").pack(side=tk.LEFT, padx=(0, 4))
        self.cam_index_var = tk.StringVar(value="0")
        cam_combo = ttk.Combobox(
            top_frame,
            textvariable=self.cam_index_var,
            values=["0", "1", "2"],
            width=5,
            state="readonly",
        )
        cam_combo.pack(side=tk.LEFT, padx=(0, 12))

        self.start_btn = ttk.Button(top_frame, text="Kamerani yoqish", command=self.start_camera)
        self.start_btn.pack(side=tk.LEFT, padx=4)

        self.stop_btn = ttk.Button(
            top_frame, text="To'xtatish", command=self.stop_camera, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=4)

        self.manual_btn = ttk.Button(
            top_frame, text="Qo'lda rasmga ol", command=self.capture_now, state=tk.DISABLED
        )
        self.manual_btn.pack(side=tk.LEFT, padx=4)

        self.auto_var = tk.BooleanVar(value=True)
        auto_chk = ttk.Checkbutton(
            top_frame,
            text="Avtomatik suratga olish",
            variable=self.auto_var,
            command=self._toggle_auto,
        )
        auto_chk.pack(side=tk.LEFT, padx=(14, 10))

        ttk.Label(top_frame, text="Interval (s):").pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value="3")
        interval_spin = ttk.Spinbox(
            top_frame,
            from_=1,
            to=30,
            textvariable=self.interval_var,
            width=5,
            command=self._update_interval,
        )
        interval_spin.pack(side=tk.LEFT, padx=4)

        # Video oynasi
        video_frame = ttk.LabelFrame(self.root, text="Jonli Kamera", padding=8)
        video_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        self.video_label = tk.Label(
            video_frame,
            text="Kamera o'chirilgan. 'Kamerani yoqish' tugmasini bosing.",
            bg="#111827",
            fg="#e5e7eb",
            font=("Segoe UI", 12),
        )
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Pastki holat satri
        status_frame = ttk.Frame(self.root, padding=(12, 6))
        status_frame.pack(fill=tk.X)

        self.status_var = tk.StringVar(value="Holat: Tayyor")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)

        self.count_var = tk.StringVar(value="Olingan rasmlar: 0 ta")
        ttk.Label(status_frame, textvariable=self.count_var).pack(side=tk.RIGHT)

    def _toggle_auto(self):
        self.auto_capture = self.auto_var.get()

    def _update_interval(self):
        try:
            val = float(self.interval_var.get())
            if val >= 0.5:
                self.cooldown_seconds = val
        except ValueError:
            pass

    def start_camera(self):
        if self.running:
            return

        try:
            cam_idx = int(self.cam_index_var.get())
        except ValueError:
            cam_idx = 0

        self.cap = cv2.VideoCapture(cam_idx)
        if not self.cap.isOpened():
            messagebox.showerror(
                "Kamera xatoligi",
                f"Kamera ({cam_idx}) ochilmadi. Boshqa kamera raqamini tanlang yoki ruxsatni tekshiring.",
            )
            self.cap = None
            return

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.manual_btn.config(state=tk.NORMAL)
        self.status_var.set("Holat: Kamera ishlamoqda (odam kutilmoqda...)")
        self._update_frame()

    def stop_camera(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.manual_btn.config(state=tk.DISABLED)
        self.video_label.config(image="", text="Kamera to'xtatildi.")
        self.status_var.set("Holat: To'xtatilgan")

    def _save_image(self, frame, reason: str):
        now = datetime.datetime.now()
        filename = now.strftime("person_%Y%m%d_%H%M%S_%f")[:-3] + ".jpg"
        filepath = os.path.join(self.save_dir, filename)
        cv2.imwrite(filepath, frame)

        self.captured_count += 1
        self.last_capture_time = time.time()
        self.count_var.set(f"Olingan rasmlar: {self.captured_count} ta")
        self.status_var.set(f"Holat: Rasm saqlandi ({reason}) -> {filename}")

    def capture_now(self):
        if self.current_frame is not None:
            self._save_image(self.current_frame, "qo'lda")

    def _update_frame(self):
        if not self.running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.status_var.set("Holat: Kadr o'qib bo'lmadi")
            self.root.after(30, self._update_frame)
            return

        clean_frame = frame.copy()
        self.current_frame = clean_frame

        # Yuz/odamni aniqlash
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.15,
            minNeighbors=5,
            minSize=(70, 70),
        )

        person_detected = len(faces) > 0
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (34, 197, 94), 2)
            cv2.putText(
                frame,
                "Odam aniqlandi",
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (34, 197, 94),
                2,
            )

        self._update_interval()
        if person_detected and self.auto_capture:
            elapsed = time.time() - self.last_capture_time
            if elapsed >= self.cooldown_seconds:
                self._save_image(clean_frame, f"avto, {len(faces)} ta yuz")
            else:
                rem = round(self.cooldown_seconds - elapsed, 1)
                self.status_var.set(f"Holat: Odam kadrda ({rem}s kutish)")
        elif not person_detected and self.running:
            self.status_var.set("Holat: Kamera faol — kadrda odam kutilmoqda")

        # Tkinter uchun rasm formatiga o'tkazish
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (880, 495))
        img_tk = ImageTk.PhotoImage(Image.fromarray(resized))

        self.video_label.img_tk = img_tk
        self.video_label.config(image=img_tk, text="")

        self.root.after(20, self._update_frame)

    def on_close(self):
        self.stop_camera()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = AutoCameraApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
