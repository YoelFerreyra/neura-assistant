import whisper
import ollama
from flask import Flask, render_template, request, jsonify
from gtts import gTTS
from playsound import playsound
import json
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

import subprocess

def open_vscode(path=None):
    """ Abre Visual Studio Code en la ruta especificada, o en la ruta por defecto si no se especifica ninguna. """
    try:
        if path:
            subprocess.run(["code", path], check=True)
        else:
            subprocess.run(["code"], check=True)
        print("Se abrió Visual Studio Code.")
        return "Se abrió Visual Studio Code."
    except Exception as e:
        print(f"Error al intentar abrir Visual Studio Code: {e}")
        return "Error al intentar abrir Visual Studio Code"


def get_ollama_response(text):

    messages = [{'role': 'user', 'content': text}]

    response = ollama.chat(
    'llama3.1',
    messages=messages,
    tools=[add_two_numbers, open_chrome, open_vscode])

    available_functions = {
    'add_two_numbers': add_two_numbers,
    'open_chrome': open_chrome,
    'open_vscode': open_vscode
    }
    print(response)

    # Si no hay llamadas a funciones, devolver el contenido del mensaje directamente
    if not response.message.tool_calls:
        return response.message.content  # Devuelve el contenido del mensaje directamente

    for tool in response.message.tool_calls or []:
        function_to_call = available_functions.get(tool.function.name)
    if function_to_call:
        response = function_to_call(**tool.function.arguments)
        print(response)
        return response
    else:
        return 'No se encontro la funcion'


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
