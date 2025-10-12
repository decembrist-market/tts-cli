# TTS с Piper

Программа для преобразования текста в речь с использованием Piper TTS.

## Возможности

- 🎯 Синтез речи на разных языках (русский, английский и др.)
- 🚀 **Потоковый режим** — обработка множества задач без перезапуска процесса
- 🔐 Поддержка **base64** кодирования текста
- 📝 Чтение текста из аргументов командной строки или stdin
- 🔄 Автоматическое определение кодировки
- 📦 Готов к упаковке в исполняемый файл (PyInstaller)

## Установка

Убедитесь, что у вас установлены зависимости:
```bash
pip install -r requirements.txt
```

## Модели

Поместите языковые модели в папку `models/`:
- `ru.onnx` и `ru.onnx.json` для русского языка
- `en.onnx` и `en.onnx.json` для английского языка
- и т.д.

Модели можно скачать с [официального репозитория Piper](https://github.com/rhasspy/piper/releases).

## Использование

### 1. Базовое использование (текст из аргумента):
```bash
python main.py "Привет, мир!" -l ru
```

### 2. Текст с base64 кодированием:
```bash
python main.py "0J/RgNC40LLQtdGCINC80LjRgCE=" --base64 -l ru
```

### 3. Чтение текста из stdin (pipe):
```bash
echo "Это текст из pipe" | python main.py -l ru
```
или (Windows PowerShell):
```powershell
"Это текст из pipe" | python main.py -l ru
```
или чтение из файла:
```bash
type input.txt | python main.py -l ru
# или
python main.py -l ru < input.txt
```

### 4. 🚀 Потоковый режим (Stream mode):

**Запуск потокового режима:**
```bash
python main.py --stream -l ru -o "D:/output"
```

**Формат команд через stdin:**
```
base64_текст|имя_файла
```
или просто:
```
base64_текст
```
(файл создастся автоматически с уникальным именем)

**Завершение работы:**
```
exit
```

**Пример использования из Python:**
```python
import subprocess
import base64

# Запускаем процесс в потоковом режиме
process = subprocess.Popen(
    ['python', 'main.py', '--stream', '-l', 'ru', '-o', 'D:/output'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    encoding='utf-8'
)

# Кодируем текст в base64
text1 = base64.b64encode("Привет мир".encode('utf-8')).decode('ascii')
text2 = base64.b64encode("Второй текст".encode('utf-8')).decode('ascii')

# Отправляем команды (модель загружается только один раз!)
process.stdin.write(f'{text1}|file1.wav\n')
process.stdin.flush()

process.stdin.write(f'{text2}|file2.wav\n')
process.stdin.flush()

# Читаем результаты
# QUEUED:file1.wav
# SUCCESS:D:/output/file1.wav
# QUEUED:file2.wav
# SUCCESS:D:/output/file2.wav

# Завершаем
process.stdin.write('exit\n')
process.stdin.close()
```

**Преимущества потокового режима:**
- ✅ Модель загружается **один раз** и остается в памяти
- ✅ Обработка **очереди задач** в отдельном потоке
- ✅ Быстрая генерация множества файлов без перезапуска процесса
- ✅ Идеально для интеграции в игры и приложения

### 5. Указание выходного файла:
```bash
python main.py "Hello world" -l en -o my_speech.wav
```

### 6. Просмотр доступных моделей:
```bash
python main.py --list-models
```

## Параметры

- `text` - текст для синтеза речи (опционально, если не указан — берётся из stdin)
- `-l, --language` - язык модели (по умолчанию: ru)
- `-o, --output` - имя выходного WAV файла или директория для потокового режима
- `--list-models` - показать доступные модели
- `--base64` - входной текст закодирован в base64
- `--stream` - **потоковый режим**: читать команды из stdin и обрабатывать очередь задач
- `-e, --encoding` - кодировка stdin (utf-8, cp1251, cp866, utf-16-le, utf-16-be, auto — по умолчанию)
- `--debug-stdin` - вывод отладочной информации: длина и hex первых байтов stdin
- `--fail-on-question` - прерывать выполнение, если весь текст деградировал до `?`

## Примеры

### Обычный режим:
```bash
# Русский текст (аргумент)
python main.py "Это тест русской речи" -l ru

# Английский текст (stdin)
echo "This is a test of English speech" | python main.py -l en

# С указанием выходного файла
python main.py "Тестовое сообщение" -l ru -o test.wav

# Большой текст из файла
python main.py -l ru < long_text.txt

# Base64 кодирование
python main.py "0J/RgNC40LLQtdGCINC80LjRgCE=" --base64 -l ru -o hello.wav
```

### Потоковый режим:
```bash
# Запуск с автоматическими именами файлов
python main.py --stream -l ru

# Запуск с указанием директории для файлов
python main.py --stream -l ru -o "D:/audio_output"
```

### Диагностика:
```bash
# Принудительная кодировка cp1251
python main.py -l ru -e cp1251 < text_cp1251.txt

# Диагностика stdin
echo Привет | python main.py -l ru --debug-stdin

# Прервать при потере кириллицы
echo Привет | python main.py -l ru --fail-on-question
```

## Форматы вывода в потоковом режиме

При работе в `--stream` режиме программа выводит следующие сообщения:

- `QUEUED:имя_файла` - задача добавлена в очередь
- `SUCCESS:полный_путь_к_файлу` - файл успешно создан
- `ERROR:описание_ошибки` - произошла ошибка при обработке

## Интеграция в игры

Потоковый режим идеально подходит для интеграции TTS в игры:

1. **Запустите TTS один раз** при старте игры
2. **Отправляйте команды** через stdin по мере необходимости
3. **Получайте результаты** через stdout
4. **Завершайте процесс** командой `exit` при закрытии игры

Модель остается загруженной в памяти, что обеспечивает быструю генерацию без задержек на инициализацию.

## Кодировка и Windows

Если при передаче текста через pipe появляются `???` или весь текст превращается в `??????`:

1. Смените кодовую страницу консоли на UTF-8 (cmd):
```cmd
chcp 65001
```
2. PowerShell 5.x: настройте Unicode ввод/вывод:
```powershell
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```
3. **Рекомендация:** используйте `--base64` флаг для надежной передачи текста с кириллицей

## Сборка в исполняемый файл

Для создания standalone `.exe` файла используйте PyInstaller:

```bash
pyinstaller tts.spec
```

Исполняемый файл будет создан в папке `dist/`.

## Лицензия

См. файл [LICENSE](LICENSE).
