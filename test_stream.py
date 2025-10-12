#!/usr/bin/env python3
import subprocess
import base64
import time

print("=== Тест потокового режима TTS ===\n")

# Запускаем процесс в потоковом режиме
process = subprocess.Popen(
    ['python', 'main.py', '--stream', '-l', 'ru', '-o', 'D:/projects/python/tts'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    bufsize=1
)

print("Процесс TTS запущен...")
time.sleep(2)

# Тестовые тексты
test_texts = [
    ("Привет, это первый тест!", "test1.wav"),
    ("Второе предложение для проверки очереди", "test2.wav"),
    ("Третий текст без указания пути", None)
]

try:
    # Отправляем команды
    for i, (text, filename) in enumerate(test_texts, 1):
        # Кодируем текст в base64
        text_b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')

        # Формируем команду
        if filename:
            command = f"{text_b64}|{filename}\n"
            print(f"\n[Команда {i}] Отправляю: {text} -> {filename}")
        else:
            command = f"{text_b64}\n"
            print(f"\n[Команда {i}] Отправляю: {text} (автоматическое имя)")

        # Отправляем команду
        process.stdin.write(command)
        process.stdin.flush()

        # Ждем ответы
        time.sleep(0.5)

    print("\n\nОжидаю обработки задач (5 секунд)...")
    time.sleep(5)

    # Отправляем команду завершения
    print("\nОтправляю команду 'exit'...")
    process.stdin.write("exit\n")
    process.stdin.flush()
    process.stdin.close()

    # Читаем все выходные данные
    print("\n=== Вывод от TTS процесса ===")
    stdout, stderr = process.communicate(timeout=10)

    if stdout:
        print(stdout)

    if stderr:
        print("\n=== Ошибки ===")
        print(stderr)

    print(f"\nКод завершения: {process.returncode}")

    # Проверяем созданные файлы
    import os
    print("\n=== Созданные файлы ===")
    for file in os.listdir('D:/projects/python/tts'):
        if file.startswith('test') and file.endswith('.wav'):
            file_path = os.path.join('D:/projects/python/tts', file)
            size = os.path.getsize(file_path)
            print(f"  ✓ {file} ({size} байт)")

except subprocess.TimeoutExpired:
    print("\nТайм-аут! Принудительно завершаю процесс...")
    process.kill()
    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)

except Exception as e:
    print(f"\nОшибка: {e}")
    process.kill()

print("\n=== Тест завершен ===")

