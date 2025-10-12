#!/usr/bin/env python3
import argparse
import sys
import wave
import os
import base64
import json
from pathlib import Path
from queue import Queue
from threading import Thread

def safe_print(*args, **kwargs):
    """Безопасный print для subprocess в Windows"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Если не получается вывести с русскими символами, выводим без них
        try:
            message = ' '.join(str(arg) for arg in args)
            safe_message = message.encode('ascii', 'replace').decode('ascii')
            print(safe_message, **kwargs)
        except:
            pass  # В крайнем случае просто пропускаем вывод

try:
    from piper import PiperVoice
except ImportError:
    safe_print("Error: piper-tts not installed. Install dependencies: pip install -r requirements.txt")
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

        safe_print(f"Загружаю модель для языка: {language}")
        self.voice = PiperVoice.load(str(model_path), str(config_path))
        self.current_language = language
        safe_print(f"Модель {language} успешно загружена")

    def text_to_speech(self, text, language, output_filename=None):
        """Преобразует текст в речь и сохраняет в WAV файл"""
        # Загружаем модель если нужно
        if self.current_language != language:
            self.load_model(language)

        # Генерируем имя файла если не указано
        if output_filename is None:
            output_filename = f"output_{language}.wav"

        output_path = Path(output_filename)

        safe_print(f"Синтезирую речь: '{text}'")
        safe_print(f"Язык: {language}")
        safe_print(f"Выходной файл: {output_path}")

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

        safe_print(f"Аудио сохранено в: {output_path.absolute()}")
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
            safe_print("Доступные языки:")
            for model in sorted(models):
                safe_print(f"  - {model}")
        else:
            safe_print("Модели не найдены в папке models/")
            safe_print("Поместите файлы *.onnx и *.onnx.json в папку models/")

        return models

    def stream_mode(self, default_language="ru", default_output_dir=None):
        """Потоковый режим: читает команды из stdin и обрабатывает их"""
        safe_print("=== TTS Потоковый режим запущен ===")
        safe_print(f"Язык: {default_language}")
        safe_print("Формат команды: base64_текст|путь_к_файлу")
        safe_print("Или просто: base64_текст (файл будет создан автоматически)")
        safe_print("Для завершения введите: exit")
        safe_print("Ожидаю команды...\n")
        sys.stdout.flush()

        task_queue = Queue()

        def worker():
            """Рабочий поток для обработки задач из очереди"""
            while True:
                task = task_queue.get()
                if task is None:  # Сигнал завершения
                    task_queue.task_done()
                    break

                try:
                    base64_text, output_path = task

                    # Декодируем base64
                    text = decode_base64_text(base64_text)

                    # Используем default_output_dir если указан
                    if default_output_dir:
                        output_path = os.path.join(default_output_dir, os.path.basename(output_path))

                    # Генерируем речь с языком из аргументов запуска
                    result = self.text_to_speech(text, default_language, output_path)

                    # Выводим результат
                    safe_print(f"SUCCESS:{result}")
                    sys.stdout.flush()

                except Exception as e:
                    safe_print(f"ERROR:{str(e)}")
                    sys.stdout.flush()

                task_queue.task_done()

        # Запускаем рабочий поток
        worker_thread = Thread(target=worker, daemon=True)
        worker_thread.start()

        # Читаем команды из stdin
        try:
            for line in sys.stdin:
                line = line.strip()

                if not line:
                    continue

                # Команда завершения
                if line.lower() == "exit":
                    safe_print("Получена команда завершения. Завершаю работу...")
                    sys.stdout.flush()
                    break

                # Парсим команду: base64_текст|путь или просто base64_текст
                parts = line.split('|')

                if len(parts) == 1:
                    # Только base64 текст, генерируем имя автоматически
                    base64_text = parts[0]
                    # Генерируем уникальное имя файла
                    import time
                    timestamp = int(time.time() * 1000)
                    output_path = f"output_{timestamp}.wav"
                elif len(parts) == 2:
                    # base64 текст и путь к файлу
                    base64_text, output_path = parts
                else:
                    safe_print(f"ERROR:Неверный формат команды. Ожидается: base64_текст|путь или base64_текст")
                    sys.stdout.flush()
                    continue

                # Добавляем задачу в очередь
                task_queue.put((base64_text, output_path))
                safe_print(f"QUEUED:{output_path}")
                sys.stdout.flush()

        except KeyboardInterrupt:
            safe_print("\nПолучен сигнал прерывания. Завершаю работу...")
            sys.stdout.flush()

        # Ждем завершения всех задач
        task_queue.put(None)  # Сигнал завершения для worker
        task_queue.join()
        worker_thread.join(timeout=5)

        safe_print("=== TTS Потоковый режим завершен ===")
        sys.stdout.flush()


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
    parser.add_argument("-o", "--output", help="Имя выходного WAV файла или директория для потокового режима")
    parser.add_argument("--list-models", action="store_true", help="Показать доступные модели")
    parser.add_argument("--base64", action="store_true", help="Входной текст закодирован в base64")
    parser.add_argument("--stream", action="store_true", help="Потоковый режим: читать команды из stdin")

    args = parser.parse_args()

    # Создаем экземпляр TTS процессора
    tts = TTSProcessor()

    # Показываем доступные модели
    if args.list_models:
        tts.list_available_models()
        return

    # Потоковый режим
    if args.stream:
        tts.stream_mode(
            default_language=args.language,
            default_output_dir=args.output
        )
        return

    # Проверяем, что передан текст
    if not args.text:
        safe_print("Ошибка: Не указан текст для синтеза")
        safe_print("Использование: python main.py 'Текст для синтеза' -l ru")
        safe_print("Использование с base64: python main.py 'base64_строка' --base64 -l ru")
        safe_print("Для просмотра доступных моделей: python main.py --list-models")
        return

    try:
        # Обрабатываем входной текст
        if args.base64:
            try:
                text_to_synthesize = decode_base64_text(args.text)
                safe_print(f"Декодированный текст: '{text_to_synthesize}'")
            except ValueError as e:
                safe_print(f"Ошибка: {e}")
                return
        else:
            text_to_synthesize = args.text

        # Выполняем синтез речи
        output_file = tts.text_to_speech(text_to_synthesize, args.language, args.output)
        safe_print(f"\nГотово! Аудио файл: {output_file}")

    except FileNotFoundError as e:
        safe_print(f"Ошибка: {e}")
        safe_print(f"\nУбедитесь, что в папке models/ есть файлы:")
        safe_print(f"  - {args.language}.onnx")
        safe_print(f"  - {args.language}.onnx.json")
        safe_print("\nДля просмотра доступных моделей: python main.py --list-models")

    except Exception as e:
        safe_print(f"Ошибка при синтезе речи: {e}")


if __name__ == '__main__':
    main()
