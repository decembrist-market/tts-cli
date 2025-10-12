#!/usr/bin/env python3
import subprocess
import base64
import time
import os

print("=== Тест потокового режима с разными директориями ===\n")

# Запускаем процесс БЕЗ указания директории
process = subprocess.Popen(
    ['python', 'main.py', '--stream', '-l', 'ru'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    bufsize=1
)

print("Процесс TTS запущен в потоковом режиме...")
time.sleep(2)

# Тестовые тексты с разными путями
test_cases = [
    ("Файл в директории D", "D:/projects/python/tts/test_d.wav"),
    ("Файл в поддиректории", "test_subfolder/test_sub.wav"),
    ("Файл в C:/temp", "C:/temp/tts_test/test_c.wav"),
    ("Автоматическое имя", None),
]

try:
    # Отправляем команды
    for i, (text, path) in enumerate(test_cases, 1):
        text_b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')

        if path:
            command = f"{text_b64}|{path}\n"
            print(f"\n[Команда {i}] {text}")
            print(f"  Путь: {path}")
        else:
            command = f"{text_b64}\n"
            print(f"\n[Команда {i}] {text}")
            print(f"  Путь: (автоматический)")

        process.stdin.write(command)
        process.stdin.flush()
        time.sleep(0.3)

    print("\n\nОжидаю завершения обработки...")
    time.sleep(8)

    # Завершаем
    print("Отправляю команду 'exit'...\n")
    process.stdin.write("exit\n")
    process.stdin.flush()
    process.stdin.close()

    # Читаем вывод
    stdout, stderr = process.communicate(timeout=10)

    print("=== Вывод от TTS ===")
    if stdout:
        for line in stdout.split('\n'):
            if line.strip():
                print(line)

    if stderr:
        print("\n=== Stderr ===")
        print(stderr)

    print(f"\nКод завершения: {process.returncode}")

    # Проверяем созданные файлы
    print("\n=== Проверка созданных файлов ===")

    check_paths = [
        "D:/projects/python/tts/test_d.wav",
        "D:/projects/python/tts/test_subfolder/test_sub.wav",
        "C:/temp/tts_test/test_c.wav",
    ]

    for path in check_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  ✓ {path} ({size:,} байт)")
        else:
            print(f"  ✗ {path} - НЕ СОЗДАН")

    # Проверяем автоматически созданные файлы
    print("\n  Автоматически созданные файлы:")
    for file in os.listdir('.'):
        if file.startswith('output_') and file.endswith('.wav'):
            size = os.path.getsize(file)
            print(f"  ✓ {file} ({size:,} байт)")

except subprocess.TimeoutExpired:
    print("\n⚠ Тайм-аут!")
    process.kill()
    stdout, stderr = process.communicate()
    print(stdout)

except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    process.kill()

print("\n=== Тест завершен ===")

