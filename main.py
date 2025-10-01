#!/usr/bin/env python3
import argparse
import sys
import wave
import os
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


def detect_encoding(raw_bytes):
    """Автоопределение кодировки stdin.
    Поддержка: UTF-8 (+ BOM), UTF-16 LE/BE (PowerShell 5.x), cp1251, cp866.
    Алгоритм:
    1. Проверка BOM (UTF-8, UTF-16 LE/BE)
    2. Эвристика для UTF-16 (много нулевых байтов)
    3. Попытки декодирования в нескольких кодировках с подсчетом кириллицы
    """
    # 1. BOM checks
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        try:
            return "utf-8-sig", raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            pass
    if raw_bytes.startswith(b"\xff\xfe"):
        try:
            return "utf-16-le", raw_bytes.decode("utf-16-le")
        except UnicodeDecodeError:
            pass
    if raw_bytes.startswith(b"\xfe\xff"):
        try:
            return "utf-16-be", raw_bytes.decode("utf-16-be")
        except UnicodeDecodeError:
            pass

    # 2. UTF-16 heuristic: доля нулевых байтов > 20% и почти каждый второй байт нуль
    if raw_bytes:
        null_count = raw_bytes.count(b"\x00")
        if null_count / len(raw_bytes) > 0.2:
            # Попробуем LE, затем BE
            for enc in ("utf-16-le", "utf-16-be"):
                try:
                    text = raw_bytes.decode(enc)
                    # Если текст содержит читаемые буквы (не только контрольные символы)
                    if any(ch.isprintable() and not ch.isspace() for ch in text[:100]):
                        return enc, text
                except UnicodeDecodeError:
                    continue

    # 3. Generic candidates (порядок важен)
    candidates = ["utf-8", "cp1251", "cp866", "windows-1251"]
    best = None
    best_score = -1
    for enc in candidates:
        try:
            text = raw_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
        cyrillic_count = sum(1 for ch in text if '\u0400' <= ch <= '\u04FF')
        score = cyrillic_count
        if score > best_score:
            best = (enc, text)
            best_score = score
        if cyrillic_count and cyrillic_count == len(text.strip()):  # все символы кириллица
            break
    if best:
        return best

    # 4. Fallback: строгий UTF-8, затем с заменами
    try:
        return "utf-8", raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return "utf-8", raw_bytes.decode("utf-8", errors="replace")


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


def main():
    parser = argparse.ArgumentParser(description="TTS с использованием Piper")
    parser.add_argument("text", nargs="?", help="Текст для синтеза речи")
    parser.add_argument("-l", "--language", default="ru", help="Язык модели (по умолчанию: ru)")
    parser.add_argument("-o", "--output", help="Имя выходного WAV файла")
    parser.add_argument("--list-models", action="store_true", help="Показать доступные модели")
    parser.add_argument(
        "-e", "--encoding", default="auto",
        help=(
            "Кодировка stdin (utf-8, cp1251, cp866, utf-16-le, utf-16-be, auto — по умолчанию). "
            "PowerShell 5.x обычно использует UTF-16 LE в пайпах."
        ),
    )
    parser.add_argument("--debug-stdin", action="store_true", help="Показать отладочную информацию о stdin (сырые байты/hex)")
    parser.add_argument("--fail-on-question", action="store_true", help="Прервать выполнение, если весь введённый текст деградировал до '?' до декодирования")

    args = parser.parse_args()

    # Создаем экземпляр TTS процессора
    tts = TTSProcessor()

    if args.list_models:
        tts.list_available_models()
        return

    input_text = args.text
    raw = None
    used_encoding = None
    if not input_text and not sys.stdin.isatty():
        raw = sys.stdin.buffer.read()
        if args.encoding.lower() == "auto":
            used_encoding, input_text = detect_encoding(raw)
        else:
            enc = args.encoding.lower()
            try:
                input_text = raw.decode(enc)
                used_encoding = enc
            except LookupError:
                print(f"Неизвестная кодировка: {enc}. Использую автоопределение.")
                used_encoding, input_text = detect_encoding(raw)
            except UnicodeDecodeError:
                print(f"Ошибка декодирования в кодировке {enc}. Использую автоопределение.")
                used_encoding, input_text = detect_encoding(raw)
        print(f"(stdin кодировка: {used_encoding})")
        input_text = input_text.strip()

    # Strip BOM if present (from UTF-8/UTF-16 decoding cases)
    if input_text:
        input_text = input_text.lstrip('\ufeff')

    lost_cyr = False
    if raw is not None and input_text:
        has_cyr = any('\u0400' <= ch <= '\u04FF' for ch in input_text)
        if not has_cyr and all(ch == '?' or ch.isspace() for ch in input_text) and b'?' in raw:
            lost_cyr = True
            print("\n[ПРЕДУПРЕЖДЕНИЕ] Похоже, кириллица была заменена на '?' ЕЩЁ ДО того, как Python получил данные.")
            print("Причина: консоль/pipe не смогла представить символы и подставила '?'.")
            print("Решения:")
            print("  1. PowerShell (Windows 5.x):  [Console]::InputEncoding = [System.Text.Encoding]::UTF8; ")
            print("     [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $OutputEncoding = [System.Text.Encoding]::UTF8")
            print("  2. Используйте аргумент: python main.py \"Привет мир\" -l ru")
            print("  3. Либо файл UTF-8: type text.txt | python main.py -l ru")
            print("  4. В cmd.exe: chcp 65001 перед запуском")
            print("  5. Убедитесь, что шрифт консоли поддерживает кириллицу (Cascadia Mono, Lucida Console)")
            print("  6. PowerShell 7+: echo Привет | python .\\main.py -l ru (обычно работает сразу)")
            if not args.debug_stdin:
                print("  7. Для подробностей запустите с --debug-stdin")
            if args.fail_on_question:
                print("\n--fail-on-question: синтез прерван.")
                return

    if args.debug_stdin and raw is not None:
        hex_preview = raw[:128].hex()
        print(f"[DEBUG] raw bytes len={len(raw)} preview(hex first 128): {hex_preview}")

    if not input_text:
        print("Ошибка: Не указан текст для синтеза")
        print("Использование: python main.py 'Текст для синтеза' -l ru")
        print("Либо передайте через stdin: echo Текст | python main.py -l ru")
        print("Для просмотра доступных моделей: python main.py --list-models")
        print("При проблемах с русскими символами попробуйте: chcp 65001 или параметр -e cp1251 / -e utf-16-le")
        return

    try:
        if lost_cyr:
            print("\nПродолжаю синтез с тем, что осталось (все '?'). Для корректного результата устраните проблему ввода.")
        output_file = tts.text_to_speech(input_text, args.language, args.output)
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
