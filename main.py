#!/usr/bin/env python3
import argparse
import sys
import wave
import os
import base64
from pathlib import Path

try:
    from piper import PiperVoice
except ImportError:
    print("Ошибка: Не установлен piper-tts. Установите зависимости: pip install -r requirements.txt")
    sys.exit(1)


def get_resource_path(relative_path):
    """Получает правильный путь к ресурсам для PyInstaller"""
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class TTSProcessor:
    def __init__(self, models_dir="models"):
        # Используем функцию для получения правильного пути к моделям
        self.models_dir = Path(get_resource_path(models_dir))
        self.voice = None
        self.current_language = None

    def load_model(self, language):
        """Загружает модель для указанного языка"""
        model_path = self.models_dir / f"{language}.onnx"
        config_path = self.models_dir / f"{language}.onnx.json"

        if not model_path.exists():
            raise FileNotFoundError(f"Модель {model_path} не найдена")
        if not config_path.exists():
            raise FileNotFoundError(f"Конфигурация {config_path} не найдена")

        print(f"Загружаю модель для языка: {language}")
        self.voice = PiperVoice.load(str(model_path), str(config_path))
        self.current_language = language
        print(f"Модель {language} успешно загружена")

    def text_to_speech(self, text, language, output_filename=None):
        """Преобразует текст в речь и сохраняет в WAV файл"""
        # Загружаем модель если нужно
        if self.current_language != language:
            self.load_model(language)

        # Генерируем имя файла если не указано
        if output_filename is None:
            output_filename = f"output_{language}.wav"

        output_path = Path(output_filename)

        print(f"Синтезирую речь: '{text}'")
        print(f"Язык: {language}")
        print(f"Выходной файл: {output_path}")

        # Синтезируем речь используя правильный API
        audio_data = bytes()
        for audio_chunk in self.voice.synthesize(text):
            # Используем правильный атрибут для получения байтовых данных
            audio_data += audio_chunk.audio_int16_bytes

        # Сохраняем аудио данные в WAV файл
        with wave.open(str(output_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # моно
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.voice.config.sample_rate)
            wav_file.writeframes(audio_data)

        print(f"Аудио сохранено в: {output_path.absolute()}")
        return output_path

    def write_wav_file(self, file_handle, audio_data, sample_rate):
        """Записывает WAV файл с правильными заголовками"""
        import struct

        # WAV заголовок
        file_handle.write(b'RIFF')
        file_handle.write(struct.pack('<I', 36 + len(audio_data)))  # размер файла
        file_handle.write(b'WAVE')

        # fmt chunk
        file_handle.write(b'fmt ')
        file_handle.write(struct.pack('<I', 16))  # размер fmt chunk
        file_handle.write(struct.pack('<H', 1))   # PCM формат
        file_handle.write(struct.pack('<H', 1))   # моно
        file_handle.write(struct.pack('<I', sample_rate))  # частота дискретизации
        file_handle.write(struct.pack('<I', sample_rate * 2))  # байт в секунду
        file_handle.write(struct.pack('<H', 2))   # байт на семпл
        file_handle.write(struct.pack('<H', 16))  # бит на семпл

        # data chunk
        file_handle.write(b'data')
        file_handle.write(struct.pack('<I', len(audio_data)))
        file_handle.write(audio_data)

    def save_wav(self, audio_array, sample_rate, output_path):
        """Сохраняет аудио данные в WAV файл"""
        with wave.open(str(output_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # моно
            wav_file.setsampwidth(2)  # 16-бит
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_array.tobytes())

    def list_available_models(self):
        """Показывает доступные модели в папке models"""
        models = []
        for file in self.models_dir.glob("*.onnx"):
            config_file = file.with_suffix(".onnx.json")
            if config_file.exists():
                models.append(file.stem)

        if models:
            print("Доступные языки:")
            for model in sorted(models):
                print(f"  - {model}")
        else:
            print("Модели не найдены в папке models/")
            print("Поместите файлы *.onnx и *.onnx.json в папку models/")

        return models


def decode_base64_text(base64_text):
    """Декодирует текст из base64 формата"""
    try:
        # Удаляем возможные пробелы и переносы строк
        cleaned_base64 = base64_text.replace(' ', '').replace('\n', '').replace('\r', '')
        # Декодируем из base64
        decoded_bytes = base64.b64decode(cleaned_base64)
        # Преобразуем в строку с UTF-8 кодировкой
        decoded_text = decoded_bytes.decode('utf-8')
        return decoded_text
    except Exception as e:
        raise ValueError(f"Ошибка декодирования base64: {e}")


def main():
    parser = argparse.ArgumentParser(description="TTS с использованием Piper")
    parser.add_argument("text", nargs="?", help="Текст для синтеза речи")
    parser.add_argument("-l", "--language", default="ru", help="Язык модели (по умолчанию: ru)")
    parser.add_argument("-o", "--output", help="Имя выходного WAV файла")
    parser.add_argument("--list-models", action="store_true", help="Показать доступные модели")
    parser.add_argument("--base64", action="store_true", help="Входной текст закодирован в base64")

    args = parser.parse_args()

    # Создаем экземпляр TTS процессора
    tts = TTSProcessor()

    # Показываем доступные модели
    if args.list_models:
        tts.list_available_models()
        return

    # Проверяем, что передан текст
    if not args.text:
        print("Ошибка: Не указан текст для синтеза")
        print("Использование: python main.py 'Текст для синтеза' -l ru")
        print("Использование с base64: python main.py 'base64_строка' --base64 -l ru")
        print("Для просмотра доступных моделей: python main.py --list-models")
        return

    try:
        # Обрабатываем входной текст
        if args.base64:
            try:
                text_to_synthesize = decode_base64_text(args.text)
                print(f"Декодированный текст: '{text_to_synthesize}'")
            except ValueError as e:
                print(f"Ошибка: {e}")
                return
        else:
            text_to_synthesize = args.text

        # Выполняем синтез речи
        output_file = tts.text_to_speech(text_to_synthesize, args.language, args.output)
        print(f"\nГотово! Аудио файл: {output_file}")

    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
        print(f"\nУбедитесь, что в папке models/ есть файлы:")
        print(f"  - {args.language}.onnx")
        print(f"  - {args.language}.onnx.json")
        print("\nДля просмотра доступных моделей: python main.py --list-models")

    except Exception as e:
        print(f"Ошибка при синтезе речи: {e}")


if __name__ == '__main__':
    main()
