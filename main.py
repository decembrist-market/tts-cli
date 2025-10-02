#!/usr/bin/env python3
import argparse
import sys
import wave
import os
from pathlib import Path

# Принудительно устанавливаем UTF-8 кодировку для stdout/stderr
# Это особенно важно при запуске через subprocess из других приложений
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Также устанавливаем переменную окружения для Python
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Отключаем espeak-ng для PyInstaller, используем только основной синтезатор Piper
os.environ['PIPER_DISABLE_ESPEAK'] = '1'


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

        # Создаем пустой WAV файл сначала чтобы убедиться что файл будет создан
        try:
            with wave.open(str(output_path), 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)  # временная частота
                wav_file.writeframes(b'')  # пустые данные
        except Exception as e:
            print(f"[ОШИБКА] Не удалось создать WAV файл: {e}")
            return None

        # Синтезируем речь используя правильный API
        audio_data = bytes()
        synthesis_successful = False

        try:
            # Попробуем синтез несколько раз с разными подходами
            for attempt in range(3):
                try:
                    print(f"Попытка синтеза #{attempt + 1}")

                    # Сохраняем оригинальный stderr
                    original_stderr = sys.stderr

                    # Подавляем все вывод в stderr во время синтеза
                    with open(os.devnull, 'w') as devnull:
                        sys.stderr = devnull

                        try:
                            chunk_count = 0
                            for audio_chunk in self.voice.synthesize(text):
                                audio_data += audio_chunk.audio_int16_bytes
                                chunk_count += 1
                                if chunk_count % 10 == 0:  # Прогресс каждые 10 чанков
                                    print(f"Обработано {chunk_count} аудио чанков...")

                            if len(audio_data) > 0:
                                synthesis_successful = True
                                print(f"Синтез успешен! Получено {len(audio_data)} байт аудио данных")
                                break

                        finally:
                            # Восстанавливаем stderr
                            sys.stderr = original_stderr

                except Exception as synthesis_error:
                    sys.stderr = original_stderr
                    print(f"[ПРЕДУПРЕЖДЕНИЕ] Попытка #{attempt + 1} неудачна: {synthesis_error}")
                    if attempt < 2:
                        print("Повторяю попытку...")
                        continue
                    else:
                        print("Все попытки исчерпаны")

        except Exception as general_error:
            print(f"[ОШИБКА] Общая ошибка синтеза: {general_error}")

        # Проверяем, получили ли мы аудио данные
        if not synthesis_successful or len(audio_data) == 0:
            print("[ОШИБКА] Не удалось сгенерировать аудио данные")
            return None  # Возвращаем None при неудаче
        else:
            print(f"Используем синтезированные данные ({len(audio_data)} байт)")

        try:
            # Перезаписываем файл с реальными аудио данными
            with wave.open(str(output_path), 'wb') as wav_file:
                wav_file.setnchannels(1)  # моно
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.voice.config.sample_rate)
                wav_file.writeframes(audio_data)

            print(f"Аудио сохранено в: {output_path.absolute()}")
            return output_path

        except Exception as save_error:
            print(f"[ОШИБКА] Не удалось сохранить WAV файл: {save_error}")
            return None

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


def main():
    parser = argparse.ArgumentParser(description="TTS с использованием Piper")
    parser.add_argument("text", nargs="?", help="Текст для синтеза речи")
    parser.add_argument("-l", "--language", default="ru", help="Язык модели (по умолчанию: ru)")
    parser.add_argument("-o", "--output", help="Имя выходного WAV файла")
    parser.add_argument("--list-models", action="store_true", help="Показать доступные модели")
    parser.add_argument("--debug-stdin", action="store_true", help="Показать отладочную информацию о stdin")

    args = parser.parse_args()

    # Создаем экземпляр TTS процессора
    tts = TTSProcessor()

    if args.list_models:
        tts.list_available_models()
        return

    input_text = args.text

    # Если текст не передан как аргумент, читаем из stdin
    if not input_text and not sys.stdin.isatty():
        try:
            # Читаем stdin как UTF-8 (без автоопределения)
            input_text = sys.stdin.read().strip()
            if args.debug_stdin:
                print(f"[DEBUG] Получен текст из stdin: '{input_text}' (длина: {len(input_text)})")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось прочитать stdin как UTF-8: {e}")
            sys.exit(1)

    if not input_text:
        print("Ошибка: Не указан текст для синтеза")
        print("Использование: python main.py 'Текст для синтеза' -l ru")
        print("Либо передайте через stdin: echo Текст | python main.py -l ru")
        print("Для просмотра доступных моделей: python main.py --list-models")
        sys.exit(1)

    try:
        output_file = tts.text_to_speech(input_text, args.language, args.output)
        if output_file is None:
            print("\n[ОШИБКА] Синтез не удался")
            sys.exit(1)
        print(f"\nГотово! Аудио файл: {output_file}")
    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
        print(f"\nУбедитесь, что в папке models/ есть файлы:")
        print(f"  - {args.language}.onnx")
        print(f"  - {args.language}.onnx.json")
        print("\nДля просмотра доступных моделей: python main.py --list-models")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при синтезе речи: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
