#!/usr/bin/env python3
import subprocess
import base64
import time
import os

# Получаем директорию проекта (где находится этот скрипт)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

print("=" * 70)
print("=== PERFORMANCE TEST: TTS Stream Mode ===")
print("=" * 70)
print(f"Project directory: {PROJECT_DIR}\n")

# Запускаем процесс
start_init = time.time()
process = subprocess.Popen(
    ['python', 'main.py', '--stream', '-l', 'ru'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    bufsize=1,
    cwd=PROJECT_DIR  # Запускаем в директории проекта
)

print("Starting TTS process in stream mode...")
time.sleep(2)
init_time = time.time() - start_init
print(f"✓ Initialization completed: {init_time:.2f}s\n")

# ДЛИННЫЕ тестовые тексты для реалистичной проверки
test_cases = [
    (
        "Добро пожаловать в систему синтеза речи на основе нейронных сетей. "
        "Этот текст предназначен для тестирования производительности алгоритма генерации аудио файлов. "
        "Система использует современные технологии машинного обучения для создания естественно звучащей речи. "
        "Нейронные сети обучены на больших массивах данных, что позволяет достичь высокого качества синтеза. "
        "Интонация, ритм и произношение максимально приближены к человеческой речи. "
        "Система поддерживает множество языков и диалектов, обеспечивая гибкость использования. "
        "Производительность является ключевым параметром для практического применения технологии. "
        "Мы тестируем скорость обработки текста различной длины и сложности. "
        "Результаты помогут оптимизировать систему для работы на устройствах с ограниченными ресурсами.",
        os.path.join(PROJECT_DIR, "perf_test1.wav")
    ),
    (
        "Второй тестовый фрагмент содержит еще более длинный текст для проверки скорости обработки больших объемов данных. "
        "Мы измеряем время выполнения каждой операции, чтобы понять узкие места в производительности системы. "
        "Это позволяет оптимизировать алгоритмы и улучшить общую эффективность приложения для конечных пользователей. "
        "Синтез речи является вычислительно интенсивной задачей, требующей значительных ресурсов процессора. "
        "Оптимизация кода и использование эффективных алгоритмов критически важны для достижения приемлемой скорости. "
        "Мы анализируем различные метрики производительности: время инициализации, скорость обработки символов, "
        "задержки при переключении между задачами, использование оперативной памяти и нагрузку на процессор. "
        "Каждая из этих метрик дает важную информацию о поведении системы в различных сценариях использования. "
        "Особое внимание уделяется стабильности работы при длительной непрерывной работе и обработке множества запросов подряд. "
        "Результаты тестирования помогут определить оптимальные параметры конфигурации для различных типов устройств.",
        os.path.join(PROJECT_DIR, "test_subfolder", "perf_test2.wav")
    ),
    (
        "Третий тест проверяет возможность сохранения файлов в произвольных директориях на различных дисках системы. "
        "Система автоматически создает необходимые папки, если они отсутствуют в файловой системе компьютера. "
        "Это важная функция для интеграции в игровые движки и другие приложения, требующие гибкой работы с файлами. "
        "Производительность должна оставаться стабильной независимо от выбранного пути сохранения результатов работы. "
        "Файловые операции могут стать узким местом при работе с медленными накопителями или сетевыми дисками. "
        "Поэтому важно измерить влияние дисковых операций на общую производительность системы синтеза речи. "
        "При работе с большим количеством файлов важна эффективная организация файловой структуры и кэширования. "
        "Мы тестируем создание файлов в различных локациях: локальных SSD дисках, обычных жестких дисках, "
        "временных директориях системы и пользовательских папках с различными правами доступа. "
        "Каждый сценарий имеет свои особенности и может влиять на итоговую производительность приложения. "
        "Результаты помогут выработать рекомендации по оптимальной организации хранения сгенерированных аудио файлов.",
        os.path.join(PROJECT_DIR, "temp_test", "perf_test3.wav")
    ),
    (
        "Четвертый тестовый случай использует автоматическую генерацию имени файла с уникальной временной меткой. "
        "Это удобно для быстрого создания множества аудио файлов без необходимости придумывать уникальные имена. "
        "Система гарантирует уникальность имен файлов благодаря использованию миллисекундных временных меток в названии. "
        "Автоматическое именование упрощает интеграцию системы в различные приложения и сервисы, "
        "где требуется массовая генерация голосовых сообщений без ручного управления названиями файлов. "
        "При этом сохраняется возможность последующей организации файлов по различным критериям: "
        "времени создания, размеру, содержанию или другим метаданным, которые можно извлечь из системы. "
        "Для больших проектов с тысячами голосовых файлов такая автоматизация становится критически важной, "
        "позволяя сосредоточиться на контенте, а не на технических деталях управления файлами. "
        "Мы также измеряем накладные расходы на генерацию уникальных имен и их влияние на общую производительность.",
        None
    ),
]

# Статистика
command_timings = []
total_chars = 0
queue_start_time = time.time()

try:
    print("=" * 70)
    print("SENDING COMMANDS TO QUEUE")
    print("=" * 70)

    # Отправляем все команды
    for i, (text, path) in enumerate(test_cases, 1):
        text_b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')
        total_chars += len(text)

        if path:
            command = f"{text_b64}|{path}\n"
            print(f"\n[Command {i}]")
            print(f"  Text length: {len(text)} characters")
            print(f"  Output path: {path}")
        else:
            command = f"{text_b64}\n"
            print(f"\n[Command {i}]")
            print(f"  Text length: {len(text)} characters")
            print(f"  Output path: (auto-generated)")

        # Замеряем время добавления в очередь
        cmd_start = time.time()
        process.stdin.write(command)
        process.stdin.flush()
        cmd_time = time.time() - cmd_start

        command_timings.append({
            'index': i,
            'chars': len(text),
            'queue_time_ms': cmd_time * 1000,
            'queued_at': time.time()
        })

        print(f"  Queue time: {cmd_time*1000:.3f}ms")
        time.sleep(0.05)

    queue_total_time = time.time() - queue_start_time

    print(f"\n{'=' * 70}")
    print(f"All {len(test_cases)} commands queued in {queue_total_time:.3f}s")
    print(f"Total text: {total_chars} characters")
    print("=" * 70)
    print("\nWaiting for processing to complete...")
    print("(This may take a while for long texts)\n")

    # Даем время на обработку (больше для длинных текстов)
    processing_start = time.time()
    time.sleep(15)

    # Отправляем команду выхода
    print("Sending 'exit' command...")
    exit_start = time.time()
    process.stdin.write("exit\n")
    process.stdin.flush()
    process.stdin.close()

    # Читаем весь вывод
    stdout, stderr = process.communicate(timeout=20)
    exit_time = time.time() - exit_start
    total_time = time.time() - start_init
    processing_time = total_time - init_time

    print(f"Exit completed in {exit_time:.2f}s\n")

    # Парсим вывод для извлечения SUCCESS сообщений
    success_times = []
    if stdout:
        for line in stdout.split('\n'):
            if 'SUCCESS:' in line:
                success_times.append(time.time())

    print("=" * 70)
    print("=== TTS PROCESS OUTPUT ===")
    print("=" * 70)
    if stdout:
        # Показываем только важные строки
        for line in stdout.split('\n'):
            line_stripped = line.strip()
            if any(keyword in line_stripped for keyword in ['QUEUED:', 'SUCCESS:', 'ERROR:', '===', 'Model']):
                print(line)

    if stderr and stderr.strip():
        print("\n=== STDERR ===")
        print(stderr)

    # ДЕТАЛЬНАЯ СТАТИСТИКА ПРОИЗВОДИТЕЛЬНОСТИ
    print(f"\n{'=' * 70}")
    print("=== PERFORMANCE STATISTICS ===")
    print("=" * 70)
    print(f"\n┌─ TIMING BREAKDOWN")
    print(f"│  Initialization time:     {init_time:.3f}s")
    print(f"│  Queue setup time:        {queue_total_time:.3f}s")
    print(f"│  Processing time:         {processing_time:.3f}s")
    print(f"│  Total execution time:    {total_time:.3f}s")
    print(f"└─")

    print(f"\n┌─ THROUGHPUT METRICS")
    print(f"│  Total characters:        {total_chars}")
    print(f"│  Overall speed:           {total_chars / total_time:.1f} chars/sec")
    print(f"│  Processing speed:        {total_chars / processing_time:.1f} chars/sec (excl. init)")
    print(f"│  Time per character:      {(processing_time / total_chars) * 1000:.3f}ms")
    print(f"│  Commands processed:      {len(test_cases)}")
    print(f"│  Avg time per command:    {processing_time / len(test_cases):.3f}s")
    print(f"└─")

    # Проверяем созданные файлы
    print(f"\n{'=' * 70}")
    print("=== FILE VERIFICATION ===")
    print("=" * 70)

    check_paths = [
        os.path.join(PROJECT_DIR, "perf_test1.wav"),
        os.path.join(PROJECT_DIR, "test_subfolder", "perf_test2.wav"),
        os.path.join(PROJECT_DIR, "temp_test", "perf_test3.wav"),
    ]

    total_size = 0
    files_created = 0
    file_stats = []

    for path in check_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            total_size += size
            files_created += 1
            file_stats.append({'path': path, 'size': size})
            print(f"\n✓ {os.path.basename(path)}")
            print(f"  Location: {os.path.dirname(path)}")
            print(f"  Size: {size:,} bytes ({size/1024:.1f} KB)")
        else:
            print(f"\n✗ {path} - NOT CREATED")

    # Автоматически созданные файлы
    print(f"\n{'─' * 70}")
    print("Auto-generated files:")
    for file in os.listdir('.'):
        if file.startswith('output_') and file.endswith('.wav'):
            stat = os.stat(file)
            size = stat.st_size
            # Проверяем что файл создан недавно (последние 30 секунд)
            if time.time() - stat.st_mtime < 30:
                total_size += size
                files_created += 1
                file_stats.append({'path': file, 'size': size})
                print(f"\n✓ {file}")
                print(f"  Size: {size:,} bytes ({size/1024:.1f} KB)")

    # ИТОГОВАЯ СВОДКА
    print(f"\n{'=' * 70}")
    print("=== SUMMARY ===")
    print("=" * 70)
    print(f"\n┌─ FILES")
    print(f"│  Created successfully:    {files_created}/{len(test_cases)}")
    print(f"│  Total audio size:        {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    if files_created > 0:
        print(f"│  Average file size:       {total_size/files_created:,.0f} bytes ({total_size/files_created/1024:.1f} KB)")
    print(f"└─")

    print(f"\n┌─ EFFICIENCY")
    if files_created > 0:
        print(f"│  Bytes per second:        {total_size / processing_time:,.0f} B/s ({total_size/processing_time/1024:.1f} KB/s)")
        print(f"│  Audio per character:     {total_size / total_chars:.1f} bytes/char")
    print(f"│  Success rate:            {(files_created/len(test_cases))*100:.0f}%")
    print(f"│  Exit code:               {process.returncode}")
    print(f"└─")

    # РЕКОМЕНДАЦИИ
    print(f"\n{'=' * 70}")
    print("=== PERFORMANCE ASSESSMENT ===")
    print("=" * 70)
    chars_per_sec = total_chars / processing_time
    if chars_per_sec > 500:
        rating = "EXCELLENT ⭐⭐⭐⭐⭐"
    elif chars_per_sec > 300:
        rating = "GOOD ⭐⭐⭐⭐"
    elif chars_per_sec > 150:
        rating = "ACCEPTABLE ⭐⭐⭐"
    elif chars_per_sec > 75:
        rating = "SLOW ⭐⭐"
    else:
        rating = "VERY SLOW ⭐"

    print(f"\nProcessing speed: {chars_per_sec:.1f} chars/sec - {rating}")
    print(f"\nThis test processed {total_chars} characters in {processing_time:.2f}s")
    print(f"Model initialization took {init_time:.2f}s (one-time cost)")

    print(f"\n{'=' * 70}")

except subprocess.TimeoutExpired:
    print("\n⚠ TIMEOUT! Process took too long to complete.")
    process.kill()
    stdout, stderr = process.communicate()
    if stdout:
        print("\nPartial output:")
        print(stdout[-500:])  # Last 500 chars

except KeyboardInterrupt:
    print("\n⚠ Test interrupted by user!")
    process.kill()

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    process.kill()

print("\n" + "=" * 70)
print("=== TEST COMPLETED ===")
print("=" * 70)
