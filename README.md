# TTS with Piper

Text-to-speech program using Piper TTS.

## Features

- 🎯 Speech synthesis in multiple languages (Russian, English, etc.)
- 🚀 **Stream mode** — process multiple tasks without restarting the process
- 🔐 **base64** text encoding support
- 📝 Read text from command line arguments or stdin
- 🔄 Automatic encoding detection
- 📦 Ready for packaging into executable file (PyInstaller)

## Installation

Make sure you have the dependencies installed:
```bash
pip install -r requirements.txt
```

## Models

Place language models in the `models/` folder:
- `ru.onnx` and `ru.onnx.json` for Russian
- `en.onnx` and `en.onnx.json` for English
- etc.

Models can be downloaded from the [official Piper repository](https://github.com/rhasspy/piper/releases).

## Usage

### 1. Basic usage (text from argument):
```bash
python main.py "Hello, world!" -l en
```

### 2. Text with base64 encoding:
```bash
python main.py "SGVsbG8sIHdvcmxkIQ==" --base64 -l en
```

### 3. Reading text from stdin (pipe):
```bash
echo "This is text from pipe" | python main.py -l en
```
or (Windows PowerShell):
```powershell
"This is text from pipe" | python main.py -l en
```
or reading from file:
```bash
type input.txt | python main.py -l en
# or
python main.py -l en < input.txt
```

### 4. 🚀 Stream mode:

**Starting stream mode:**
```bash
python main.py --stream -l en
```

**Command format via stdin:**
```
base64_text|full_path_to_file
```
or simply:
```
base64_text
```
(file will be created automatically with a unique name in the current directory)

**Exit:**
```
exit
```

**Python usage example:**
```python
import subprocess
import base64

# Start process in stream mode
process = subprocess.Popen(
    ['python', 'main.py', '--stream', '-l', 'en'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    encoding='utf-8'
)

# Encode text to base64
text1 = base64.b64encode("Hello world".encode('utf-8')).decode('ascii')
text2 = base64.b64encode("Second text".encode('utf-8')).decode('ascii')

# Send commands with FULL file paths (model loads only once!)
process.stdin.write(f'{text1}|D:/output/file1.wav\n')
process.stdin.flush()

process.stdin.write(f'{text2}|C:/temp/audio/file2.wav\n')
process.stdin.flush()

# Or with relative paths
text3 = base64.b64encode("Third text".encode('utf-8')).decode('ascii')
process.stdin.write(f'{text3}|subfolder/file3.wav\n')
process.stdin.flush()

# Read results
# QUEUED:D:/output/file1.wav
# SUCCESS:D:\output\file1.wav
# QUEUED:C:/temp/audio/file2.wav
# SUCCESS:C:\temp\audio\file2.wav
# QUEUED:subfolder/file3.wav
# SUCCESS:D:\projects\python\tts\subfolder\file3.wav

# Exit
process.stdin.write('exit\n')
process.stdin.close()
```

**Stream mode advantages:**
- ✅ Model loads **once** and stays in memory
- ✅ **Task queue** processing in a separate thread
- ✅ Fast generation of multiple files without process restart
- ✅ **Complete freedom in choosing directories** — each file can be saved anywhere
- ✅ Automatic directory creation if they don't exist
- ✅ Perfect for game and application integration

### 5. Specifying output file:
```bash
python main.py "Hello world" -l en -o my_speech.wav
```

### 6. List available models:
```bash
python main.py --list-models
```

## Parameters

- `text` - text for speech synthesis (optional, if not specified — read from stdin)
- `-l, --language` - model language (default: ru)
- `-o, --output` - output WAV file name
- `--list-models` - show available models
- `--base64` - input text is base64 encoded
- `--stream` - **stream mode**: read commands from stdin and process task queue
- `-e, --encoding` - stdin encoding (utf-8, cp1251, cp866, utf-16-le, utf-16-be, auto — default)
- `--debug-stdin` - output debug information: length and hex of first stdin bytes
- `--fail-on-question` - abort execution if all text degraded to `?`

## Examples

### Normal mode:
```bash
# English text (argument)
python main.py "This is a speech test" -l en

# Russian text (stdin)
echo "Это тест русской речи" | python main.py -l ru

# With output file
python main.py "Test message" -l en -o test.wav

# Large text from file
python main.py -l en < long_text.txt

# Base64 encoding
python main.py "SGVsbG8sIHdvcmxkIQ==" --base64 -l en -o hello.wav
```

### Stream mode:
```bash
# Start with automatic file names
python main.py --stream -l en
```

### Diagnostics:
```bash
# Force cp1251 encoding
python main.py -l ru -e cp1251 < text_cp1251.txt

# Debug stdin
echo Hello | python main.py -l en --debug-stdin

# Abort on text loss
echo Test | python main.py -l en --fail-on-question
```

## Stream mode output formats

In `--stream` mode, the program outputs the following messages:

- `QUEUED:filename` - task added to queue
- `SUCCESS:full_path_to_file` - file successfully created
- `ERROR:error_description` - error occurred during processing

## Game Integration

Stream mode is perfect for TTS integration in games:

1. **Start TTS once** when the game starts
2. **Send commands** via stdin as needed
3. **Receive results** via stdout
4. **Exit process** with `exit` command when closing the game

The model stays loaded in memory, ensuring fast generation without initialization delays.

## Encoding and Windows

If text passed through pipe shows `???` or all text turns into `??????`:

1. Change console code page to UTF-8 (cmd):
```cmd
chcp 65001
```
2. PowerShell 5.x: configure Unicode input/output:
```powershell
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```
3. **Recommendation:** use `--base64` flag for reliable text transfer with Cyrillic characters

## Building executable file

To create a standalone `.exe` file, use PyInstaller:

```bash
pyinstaller tts.spec
```

The executable will be created in the `dist/` folder.

## License

See [LICENSE](LICENSE) file.
