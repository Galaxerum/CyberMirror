import tkinter as tk
import time
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageTk
import cv2
import mediapipe as mp
import pyaudio
import numpy as np
import configparser

from wake_word_detector import WakeWordDetector
from weather import get_weather
from news import news_pars


class GestureHandler:
    def __init__(self, app, ping):
        self.app = app
        self.ping = ping
        self.cap = cv2.VideoCapture(0)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.6)
        self.mp_drawing = mp.solutions.drawing_utils
        self.process_hand_gesture()

    def process_hand_gesture(self):
        # Захватываем кадр с веб-камеры
        ret, image = self.cap.read()
        if not ret:
            return

        # Переворачиваем изображение по горизонтали и конвертируем его в RGB формат
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        # Обрабатываем изображение с помощью Mediapipe
        results = self.hands.process(image)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                palm_x = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST].x
                thumb_tip_y = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP].y
                index_finger_y = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP].y

                is_right_hand = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_MCP].x > \
                                hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_MCP].x

                # Распознавание жеста сжатия кулака
                if is_right_hand and palm_x > 0.5 and thumb_tip_y < index_finger_y:
                    print("Правая рука сжата в кулак")
                    self.app.next_time()
                elif not is_right_hand and palm_x < 0.5 and thumb_tip_y < index_finger_y:
                    print("левая рука сжата в кулак")
                    self.app.prev_time()

                # Отображаем результаты распознавания на изображении
                self.mp_drawing.draw_landmarks(image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        # Отображаем изображение с результатами распознавания жестов
        cv2.imshow('Hand Gestures Recognition', cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        self.app.root.after(self.ping, self.process_hand_gesture)


class AudioHandler:
    def __init__(self, app, config):
        self.app = app
        self.config = config

        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1280
        self.audio = pyaudio.PyAudio()
        self.mic_stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True,
                                          input_device_index=1,
                                          frames_per_buffer=self.CHUNK)

        inference_framework = 'onnx'
        model_path_weather = f"models/weather.{inference_framework}"
        model_path_news = f"models/news.{inference_framework}"

        cooldown = 2
        predict_weather = float(self.config['Default']['predict_weather']) / 100
        predict_news = float(self.config['Default']['predict_news']) / 100

        # Загружаем модели для распознавания ключевых слов
        self.wake_word_detector_news = WakeWordDetector(model_path_news, inference_framework, cooldown, predict_news)
        self.wake_word_detector_weather = WakeWordDetector(model_path_weather, inference_framework, cooldown,
                                                           predict_weather)

        # Запускаем прослушивание аудио для распознавания ключевых слов
        self.wake_word()

    def wake_word(self):
        mic_audio = np.frombuffer(self.mic_stream.read(self.CHUNK), dtype=np.int16)
        process_news = self.wake_word_detector_news.process_audio(mic_audio)
        process_weather = self.wake_word_detector_weather.process_audio(mic_audio)

        # Обработка результатов распознавания ключевых слов
        if process_news[0] == 'news':
            self.app.current_mode = 'news'
            self.app.diod_label.config(background='#5EC4CD', text='(:)')
            print('Режим изменен на новости', process_news[1])
        elif process_weather[0] == 'weather':
            self.app.current_mode = 'weather'
            self.app.diod_label.config(background='#5FD3B3', text='')
            print('Режим изменен на погоду', process_news[1])

        self.app.root.after(50, self.wake_word)


class CyberApp:
    def __init__(self, root):
        self.root = root
        self.config = configparser.ConfigParser()
        self.config.read("settings.ini")

        self.current_string = 0
        self.current_mode = 'weather'
        self.ping = int(self.config['Default']['ping'])

        self.weather_forecast = get_weather()
        self.news_strings = news_pars()

        self.setup_gui()
        self.gesture_handler = GestureHandler(self, self.ping)
        self.audio_handler = AudioHandler(self, self.config)

        self.update_time_date()
        self.scroll_all_strings()

    def setup_gui(self):
        # Создаем графический интерфейс
        self.root.geometry("800x600")
        self.root.resizable(width=False, height=False)
        self.root.title('Кибер зеркало')

        # Фрейм для отображения погоды
        self.weather_frame = tk.Frame(self.root, bg="#DEDEDE")
        self.weather_frame.place(relx=0.05, rely=0.15, relwidth=0.25, relheight=0.8)

        self.icon_label = tk.Label(self.weather_frame, bg="#DEDEDE")
        self.icon_label.pack(side="top")

        self.weather_label = tk.Label(self.weather_frame, font=('Arial', 12), bg="#DEDEDE")
        self.weather_label.pack()

        self.current_time = tk.StringVar(value=self.find_time())
        self.show_weather_info(self.current_time.get())

        # Фрейм для отображения времени
        self.top_frame = tk.Frame(self.root, bg="#5FD3B3")
        self.top_frame.place(relx=0.05, rely=0.04, relwidth=0.9, relheight=0.09)

        self.time_label = tk.Label(self.top_frame, text="время", font=("Arial", 12), bg="#5FD3B3")
        self.date_label = tk.Label(self.top_frame, text="дата", font=("Arial", 12), bg="#5FD3B3")
        self.time_label.pack(side="right")
        self.date_label.pack(side="right")

        self.news_label = tk.Label(self.top_frame, font=("Arial", 12), wraplength=400, bg="#5FD3B3")
        self.news_label.pack(side="left")

        self.diod_label = tk.Label(self.top_frame, font=('Arial', 12), wraplength=50, bg="#5FD3B3")
        self.diod_label.pack(side="right")

        # Фрейм для кнопок
        self.button_frame = tk.Frame(self.weather_frame, bg="#DEDEDE")
        self.button_frame.pack(side="bottom")

        self.prev_weather_button = tk.Button(self.button_frame, text='Previous', command=self.prev_time)
        self.prev_weather_button.pack(pady=5, side="left")

        self.next_weather_button = tk.Button(self.button_frame, text='Next', command=self.next_time)
        self.next_weather_button.pack(pady=5, side="right")

        self.switch_button = tk.Button(self.button_frame, text='(0)', command=self.switch_mode)
        self.switch_button.pack(pady=5, side="bottom")

    def find_time(self):
        # Определяем текущее время
        current_time = datetime.now().time()
        times = list(self.weather_forecast.keys())
        times.sort()
        for i in range(len(times) - 1):
            if datetime.strptime(times[i], '%H:%M').time() <= current_time < datetime.strptime(times[i + 1],
                                                                                               '%H:%M').time():
                return times[i]
        return times[-1]

    def switch_mode(self):
        # Переключаем режим отображения между погодой и новостями
        self.current_mode = 'news' if self.current_mode == 'weather' else 'weather'

    def show_weather_info(self, time):
        # Отображаем информацию о погоде
        info = self.weather_forecast[time]
        info_str = (f"Time: {time}\n"
                    f"{info['description'].capitalize()}\n"
                    f"Чувствуется как: {info['feels_like']}°C\n"
                    f"Температура: {info['temperature']}°C\n"
                    f"Влажность: {info['humidity']}%\n"
                    f"Ветер: {info['wind_speed']} м/с")
        self.weather_label['text'] = info_str
        icon_image = ImageTk.PhotoImage(Image.open(BytesIO(info["icon"])))
        self.icon_label.image = icon_image
        self.icon_label.config(image=icon_image)

    def show_news(self):
        # Отображаем новости
        self.news_label.config(text=self.news_strings[self.current_string])

    def scroll_all_strings(self):
        # Прокручиваем все строки новостей
        if self.current_mode == 'weather':
            self.news_label.config(text=self.news_strings[self.current_string])
            self.current_string = (self.current_string + 1) % len(self.news_strings)
            self.news_label.after(2000, self.scroll_all_strings)
        else:
            self.news_label.config(text=self.news_strings[self.current_string])
            self.news_label.after(2000, self.scroll_all_strings)

    def prev_time(self):
        # Переходим к предыдущему времени (погода) или новости
        if self.current_mode == 'weather':
            times = list(self.weather_forecast.keys())
            current_index = times.index(self.current_time.get())
            next_index = (current_index - 1) % len(times)
            self.current_time.set(times[next_index])
            self.show_weather_info(times[next_index])
        else:
            self.current_string = (self.current_string - 1) % len(self.news_strings)
            self.show_news()

    def next_time(self):
        # Переходим к следующему времени (погода) или новости
        if self.current_mode == 'weather':
            times = list(self.weather_forecast.keys())
            current_index = times.index(self.current_time.get())
            next_index = (current_index + 1) % len(times)
            self.current_time.set(times[next_index])
            self.show_weather_info(times[next_index])
        else:
            self.current_string = (self.current_string + 1) % len(self.news_strings)
            self.show_news()

    def update_time_date(self):
        # Обновляем время и дату каждую секунду
        current_time = time.strftime("%H:%M:%S")
        current_date = time.strftime("%d-%m-%Y")
        self.time_label.config(text=current_time)
        self.date_label.config(text=current_date)
        self.root.after(1000, self.update_time_date)


if __name__ == '__main__':
    root = tk.Tk()
    app = CyberApp(root)
    root.mainloop()
