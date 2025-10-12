#!/usr/bin/env python3
import subprocess
import base64
import time

print("=== Тест потокового режима с base64 ===\n")

# Тестовые тексты
test_texts = [
    "Проверка первого текста",
    "Второй текст на русском языке",
    "Третий тест с цифрами 123 и символами!"
]

# Кодируем тексты в base64
print("Кодирую тексты в base64:")
for i, text in enumerate(test_texts, 1):
    b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')
    print(f"{i}. '{text}'")
    print(f"   base64: {b64}\n")

# Запускаем процесс в потоковом режиме
print("Запускаю TTS в потоковом режиме...\n")
process = subprocess.Popen(
    ['python', 'main.py', '--stream', '-l', 'ru', '-o', 'D:/projects/python/tts'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    bufsize=1
)

time.sleep(2)

try:
    # Отправляем команды
    for i, text in enumerate(test_texts, 1):
        text_b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')
        filename = f"base64_test{i}.wav"
        command = f"{text_b64}|{filename}\n"

        print(f"[Отправляю {i}] {text} -> {filename}")
        print(f"  base64: {text_b64}")

        process.stdin.write(command)
        process.stdin.flush()
        time.sleep(0.3)

    print("\nОжидаю обработки всех задач...")
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
        # Пытаемся вывести как есть
        for line in stdout.split('\n'):
            if line.strip():
                print(line)

    if stderr:
        print("\n=== Ошибки ===")
        print(stderr)

    print(f"\nКод завершения: {process.returncode}")

    # Проверяем созданные файлы
    import os
    print("\n=== Созданные файлы ===")
    found_files = False
    for file in os.listdir('D:/projects/python/tts'):
        if file.startswith('base64_test') and file.endswith('.wav'):
            file_path = os.path.join('D:/projects/python/tts', file)
            size = os.path.getsize(file_path)
            print(f"  ✓ {file} ({size:,} байт)")
            found_files = True

    if not found_files:
        print("  ⚠ Файлы не найдены!")

    print("\n=== Тест завершен успешно ===")

except subprocess.TimeoutExpired:
    print("\n⚠ Тайм-аут! Завершаю процесс...")
    process.kill()
    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)

except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    process.kill()

