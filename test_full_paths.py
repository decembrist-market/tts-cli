#!/usr/bin/env python3
import subprocess
import base64
import time
import os

print("=== Performance Test: Stream Mode with Different Directories ===\n")

# Запускаем процесс БЕЗ указания директории
start_init = time.time()
process = subprocess.Popen(
    ['python', 'main.py', '--stream', '-l', 'ru'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    bufsize=1
)

print("TTS process started in stream mode...")
time.sleep(2)
init_time = time.time() - start_init
print(f"Initialization time: {init_time:.2f}s\n")

# Тестовые тексты с разными путями (более длинные для реалистичного теста)
test_cases = [
    (
        "Добро пожаловать в систему синтеза речи. Этот текст предназначен для тестирования производительности "
        "алгоритма генерации аудио файлов на основе текстовых данных. Система использует нейронные сети "
        "для создания естественно звучащей речи с правильной интонацией и произношением.",
        "D:/projects/python/tts/test_d.wav"
    ),
    (
        "Второй тестовый фрагмент содержит более длинный текст для проверки скорости обработки больших объемов данных. "
        "Мы измеряем время выполнения каждой операции, чтобы понять узкие места в производительности системы. "
        "Это позволяет оптимизировать алгоритмы и улучшить общую эффективность приложения для конечных пользователей.",
        "test_subfolder/test_sub.wav"
    ),
    (
        "Третий тест проверяет возможность сохранения файлов в произвольных директориях на различных дисках. "
        "Система автоматически создает необходимые папки, если они отсутствуют в файловой системе. "
        "Это важная функция для интеграции в игровые движки и другие приложения, требующие гибкой работы с файлами. "
        "Производительность должна оставаться стабильной независимо от выбранного пути сохранения результатов.",
        "C:/temp/tts_test/test_c.wav"
    ),
    (
        "Четвертый тестовый случай использует автоматическую генерацию имени файла с временной меткой. "
        "Это удобно для быстрого создания множества аудио файлов без необходимости придумывать уникальные имена. "
        "Система гарантирует уникальность имен файлов благодаря использованию миллисекундных временных меток в названии.",
        None
    ),
]

# Статистика
timings = []
total_chars = 0

try:
    # Отправляем команды
    for i, (text, path) in enumerate(test_cases, 1):
        text_b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')
        total_chars += len(text)

        if path:
            command = f"{text_b64}|{path}\n"
            print(f"[Command {i}] Length: {len(text)} chars")
            print(f"  Path: {path}")
        else:
            command = f"{text_b64}\n"
            print(f"[Command {i}] Length: {len(text)} chars")
            print(f"  Path: (automatic)")

        # Замеряем время отправки команды
        cmd_start = time.time()
        process.stdin.write(command)
        process.stdin.flush()
        cmd_time = time.time() - cmd_start
        print(f"  Queue time: {cmd_time*1000:.2f}ms")

        timings.append({
            'command': i,
            'chars': len(text),
            'queue_time': cmd_time,
            'start': time.time()
        })

        time.sleep(0.1)

    print(f"\n{'='*60}")
    print("Waiting for all tasks to complete...")
    print(f"{'='*60}\n")

    # Засекаем общее время обработки
    processing_start = time.time()
    time.sleep(10)  # Даем время на обработку

    # Завершаем
    print("Sending 'exit' command...\n")
    process.stdin.write("exit\n")
    process.stdin.flush()
    process.stdin.close()

    # Читаем вывод
    stdout, stderr = process.communicate(timeout=15)
    total_time = time.time() - start_init

    print(f"{'='*60}")
    print("=== TTS OUTPUT ===")
    print(f"{'='*60}")
    if stdout:
        for line in stdout.split('\n'):
            if line.strip():
                print(line)

    if stderr:
        print("\n=== STDERR ===")
        print(stderr)

    print(f"\n{'='*60}")
    print("=== PERFORMANCE STATISTICS ===")
    print(f"{'='*60}")
    print(f"Exit code: {process.returncode}")
    print(f"Total execution time: {total_time:.2f}s")
    print(f"Total characters processed: {total_chars}")
    print(f"Average speed: {total_chars / total_time:.1f} chars/sec")

    # Проверяем созданные файлы
    print(f"\n{'='*60}")
    print("=== FILE VERIFICATION ===")
    print(f"{'='*60}")

    check_paths = [
        "D:/projects/python/tts/test_d.wav",
        "D:/projects/python/tts/test_subfolder/test_sub.wav",
        "C:/temp/tts_test/test_c.wav",
    ]

    total_size = 0
    files_created = 0

    for path in check_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            total_size += size
            files_created += 1
            # Время создания файла
            creation_time = os.path.getctime(path)
            print(f"  ✓ {path}")
            print(f"    Size: {size:,} bytes ({size/1024:.1f} KB)")
        else:
            print(f"  ✗ {path} - NOT CREATED")

    # Проверяем автоматически созданные файлы
    print("\n  Auto-generated files:")
    for file in os.listdir('.'):
        if file.startswith('output_') and file.endswith('.wav'):
            size = os.path.getsize(file)
            total_size += size
            files_created += 1
            print(f"  ✓ {file}")
            print(f"    Size: {size:,} bytes ({size/1024:.1f} KB)")

    print(f"\n{'='*60}")
    print("=== SUMMARY ===")
    print(f"{'='*60}")
    print(f"Files created: {files_created}")
    print(f"Total audio size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    print(f"Average file size: {total_size/files_created:,.0f} bytes ({total_size/files_created/1024:.1f} KB)")
    print(f"Processing efficiency: {total_chars/(total_time-init_time):.1f} chars/sec (excluding init)")

    # Оценка времени на один символ
    time_per_char = (total_time - init_time) / total_chars
    print(f"Time per character: {time_per_char*1000:.2f}ms")

    print(f"\n{'='*60}")

except subprocess.TimeoutExpired:
    print("\n⚠ TIMEOUT!")
    process.kill()
    stdout, stderr = process.communicate()
    print(stdout)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    process.kill()

print("\n=== TEST COMPLETED ===")
