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

### Базовое использование:
```bash
python main.py "Привет, мир!" -l ru
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

- `text` - текст для синтеза речи (обязательный)
- `-l, --language` - язык модели (по умолчанию: ru)
- `-o, --output` - имя выходного WAV файла (по умолчанию: output_[язык].wav)
- `--list-models` - показать доступные модели

## Примеры

```bash
# Русский текст
python main.py "Это тест русской речи" -l ru

# Английский текст
python main.py "This is a test of English speech" -l en

# С указанием выходного файла
python main.py "Тестовое сообщение" -l ru -o test.wav
```
