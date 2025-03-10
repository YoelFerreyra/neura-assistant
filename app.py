import whisper
import ollama
from flask import Flask, render_template, request, jsonify
from gtts import gTTS
from playsound import playsound
import subprocess

app = Flask(__name__)

model = whisper.load_model("base")

def add_two_numbers(a: int, b: int) -> int:
    result = a + b
    return f'El resultado de {a} + {b} es {result}'

def open_chrome(cmd=None):
    print(f'Se abrió Google Chrome con comando: {cmd}' if cmd else 'Se abrió Google Chrome')
    subprocess.run(["google-chrome"])
    return 'Se abrió Google Chrome correctamente'

def open_vscode(path=None):
    """ Abre Visual Studio Code en la ruta especificada, o en la ruta por defecto si no se especifica ninguna. """
    try:
        if path:
            subprocess.run(["code", path], check=True)
        else:
            subprocess.run(["code"], check=True)
        return "Se abrió Visual Studio Code."
    except Exception as e:
        return "Error al intentar abrir Visual Studio Code"

def get_ollama_response(text):
    messages = [
        {"role": "system", "content": "Eres un asistente con un tono burlón y sarcástico"},
        {"role": "user", "content": text}
    ]

    response = ollama.chat(
        'llama3.1',
        messages=messages,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "add_two_numbers",
                    "description": "Add two numbers",
                    "parameters": {
                        "type": "object",
                        "required": ["a", "b"],
                        "properties": {
                            "a": {"type": "integer", "description": "The first integer number"},
                            "b": {"type": "integer", "description": "The second integer number"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_chrome",
                    "description": "Abre Google Chrome en la computadora.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cmd": {
                                "type": "string",
                                "description": "Comando opcional para abrir Chrome con una URL o argumento específico."
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_vscode",
                    "description": "Abre Visual Studio Code en la computadora.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta opcional de la carpeta o archivo a abrir en VS Code. Si no se proporciona, se abrirá VS Code en la ubicación predeterminada."
                            }
                        }
                    }
                }
            }
        ]
    )

    available_functions = {
        'add_two_numbers': add_two_numbers,
        'open_chrome': open_chrome,
        'open_vscode': open_vscode
    }
    print(response)

    if not response.message.tool_calls:
        return response.message.content

    for tool in response.message.tool_calls or []:
        function_to_call = available_functions.get(tool.function.name)

        if function_to_call:
            return function_to_call(**tool.function.arguments)

    fallback_response = ollama.chat(
        'llama3.1',
        messages=messages
    )

    return fallback_response.message.content

@app.route("/")
def index():
    return render_template("recorder.html")

@app.route("/audio", methods=["POST"])
def audio():
    audio_file = request.files.get("audio")
    
    if not audio_file:
        return jsonify({"error": "No se recibió un archivo de audio"}), 400

    audio_path = "temp_audio.mp3"
    audio_file.save(audio_path)

    result = model.transcribe(audio_path)
    transcription = result["text"]
    print("Transcripción:", transcription)

    response = get_ollama_response(transcription)

    print(response)

    tts = gTTS(response, lang="es", tld="com.mx")
    tts.save("response.mp3")

    playsound("response.mp3")

    if not response:
        return jsonify({"transcription": transcription, "error": "No response from AI"}), 500

    return jsonify({"result": "ok", "text": response}), 200

if __name__ == "__main__":
    app.run(debug=True)
