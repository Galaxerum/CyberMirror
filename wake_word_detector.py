import time
from openwakeword.model import Model

class WakeWordDetector:
    def __init__(self, model, inference_framework, cooldown, predict):
        # Инициализация модели для обнаружения ключевых слов
        self.model = Model(wakeword_models=[model], inference_framework=inference_framework)
        self.cooldown = cooldown
        self.predict = predict
        #
        self.activation = False
        self.last_save = time.time()


    def process_audio(self, mic_audio):
        # Предсказание активации ключевых слов
        prediction = self.model.predict(mic_audio)
        for mdl in prediction.keys():
            if prediction[mdl] >= self.predict:
                #
                self.activation = True
                # print(prediction[mdl], end='\r')

            if self.activation and (time.time() - self.last_save) >= self.cooldown:
                # Сброс времени активации и возврат сигнала сохранения  
                self.last_save = time.time()
                self.activation = False
                return mdl, prediction[mdl]
            return prediction[mdl], ' '

