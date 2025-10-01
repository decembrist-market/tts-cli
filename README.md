# TTS с Piper

Программа для преобразования текста в речь с использованием Piper TTS.

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

### Базовое использование (аргумент командной строки):
```bash
python main.py "Привет, мир!" -l ru
```

### Чтение текста из stdin (pipe):
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

### Указание выходного файла:
```bash
python main.py "Hello world" -l en -o my_speech.wav
```

### Просмотр доступных моделей:
```bash
python main.py --list-models
```

## Параметры

- `text` - текст для синтеза речи (опционально, если не указан — берётся из stdin)
- `-l, --language` - язык модели (по умолчанию: ru)
- `-o, --output` - имя выходного WAV файла (по умолчанию: output_[язык].wav)
- `--list-models` - показать доступные модели
- `-e, --encoding` - кодировка stdin (utf-8, cp1251, cp866, utf-16-le, utf-16-be, auto — по умолчанию)
- `--debug-stdin` - вывод отладочной информации: длина и hex первых байтов stdin
- `--fail-on-question` - прерывать выполнение, если весь текст деградировал до `?`

## Примеры

```bash
# Русский текст (аргумент)
python main.py "Это тест русской речи" -l ru

# Английский текст (stdin)
echo "This is a test of English speech" | python main.py -l en

# С указанием выходного файла
python main.py "Тестовое сообщение" -l ru -o test.wav

# Большой текст из файла
python main.py -l ru < long_text.txt

# Принудительная кодировка cp1251
python main.py -l ru -e cp1251 < text_cp1251.txt

# Диагностика stdin
echo Привет | python main.py -l ru --debug-stdin

# Прервать при потере кириллицы
echo Привет | python main.py -l ru --fail-on-question
```

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
3. Проверьте echo:
```cmd
echo Привет
```
Если уже тут вопросительные знаки — проблема вне скрипта.
4. Используйте аргумент вместо pipe:
```cmd
python main.py "Привет мир" -l ru
```
5. Используйте файл UTF-8:
```cmd
echo Привет мир > text.txt
python main.py -l ru < text.txt
```
6. Для PowerShell 7 (pwsh) обычно достаточно:
```powershell
"Привет мир" | python .\main.py -l ru
```
7. Запустите с `--debug-stdin` чтобы увидеть hex. Если там `3f3f3f...` — символы потеряны ДО Python.
8. Попробуйте другой терминал (Windows Terminal) и шрифт (Cascadia Mono / Lucida Console).

## Причины появления `?`
- Консоль не может представить Unicode и заменяет на `?`.
- Неправильная кодировка пайпа в старых версиях PowerShell.
- Фильтр или внешняя команда уже выдала `?`.

## Что делать если hex = 3f3f3f...
- Только смена окружения или метода ввода (аргумент/файл/новый терминал) восстановит корректный текст.
- Можно прервать выполнение автоматически: `--fail-on-question`.

## Советы
- Для стабильного UTF-8: включите в региональных настройках Windows опцию «Бета: Использовать Юникод (UTF-8) для поддержки языка».
- Проверяйте реальные байты: `--debug-stdin`.
- Не полагайтесь на `echo` в старом PowerShell — используйте файл или аргумент.

## План улучшений (возможные будущие фичи)
- Потоковый синтез (chunked)
- SSML / паузы
- Разбиение длинного текста по предложениям
- Параллельная пакетная обработка
