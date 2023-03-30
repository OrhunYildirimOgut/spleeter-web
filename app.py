from flask import Flask, render_template, request, send_from_directory, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit
import os
from yt_dlp import YoutubeDL
from spleeter.separator import Separator
from pydub import AudioSegment
from pathlib import Path
import shutil

app = Flask(__name__)
app.config['SEPARATED_AUDIO_PATH'] = str(Path("./separated_audio"))
app.config['TEMPLATES_PATH'] = str(Path("./templates"))

app.secret_key = 'very_very_secret_key'

socketio = SocketIO(app)

SEPARATED_AUDIO_PATH = app.config['SEPARATED_AUDIO_PATH']
TEMPLATES_PATH = app.config['TEMPLATES_PATH']

@app.route('/')
def index():
    return render_template('index.html', separated_audio_urls={})

@app.route('/convert', methods=['POST'])
def convert():
    url = request.form['url']
    separation_option = request.form['separation_option']

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(Path(SEPARATED_AUDIO_PATH) / '%(title)s.%(ext)s'),
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_name = ydl.prepare_filename(info)

    input_file = os.path.splitext(file_name)[0] + ".mp3"

    output_path = SEPARATED_AUDIO_PATH

    separate_audio(input_file, output_path, separation_option)

    session['input_file'] = input_file
    session['output_path'] = output_path
    session['url'] = url

    separate_audio(input_file, output_path, separation_option)
    pad_audio_files(output_path)

    return redirect(url_for('results'))


def separate_audio(input_file, output_path, separation_option):
    if separation_option == 'vocal_music':
        model = 'spleeter:2stems'
    elif separation_option == 'vocal_music_bass_drum_piano':
        model = 'spleeter:5stems'
    else:
        raise ValueError('Invalid separation option')

    separator = Separator(model)
    separator.separate_to_file(input_file, output_path, codec='mp3')

    separated_folder = os.path.join(output_path, os.path.splitext(os.path.basename(input_file))[0])
    print(f"Separated folder: {separated_folder}")

    for file in os.listdir(separated_folder):
        if file.endswith(".mp3"):
            src = os.path.join(separated_folder, file)
            dest = os.path.join(output_path, file)
            print(f"Moving file '{src}' to '{dest}'")
            shutil.move(src, dest)

    shutil.rmtree(separated_folder)
    

    print("Output folder contents:", os.listdir(output_path))

def convert_to_mp3(input_file):
    output_file = os.path.splitext(input_file)[0] + ".mp3"
    audio = AudioSegment.from_file(input_file)
    audio.export(output_file, format="mp3")
    return output_file

def get_separated_audio_urls(input_file):
    input_filename = os.path.splitext(os.path.basename(input_file))[0]
    output_folder = SEPARATED_AUDIO_PATH  
    file_urls = {}
    for file in os.listdir(output_folder):
        if file.endswith(".mp3") and file.startswith(input_filename):
            file_url = '/return-separated-file/' + file
            file_urls[file[:-4]] = file_url
    print("File URLs:", file_urls)
    return file_urls

@app.route('/return-separated-file/<filename>')
def return_separated_file(filename):
    directory = SEPARATED_AUDIO_PATH
    return send_from_directory(directory=directory, path=filename, as_attachment=True)

@app.route('/results')
def results():
    if 'input_file' not in session or 'output_path' not in session or 'url' not in session:
        return redirect(url_for('index'))    
    input_file = session['input_file']
    output_path = session['output_path']
    url = session['url']
    files = os.listdir(output_path)
    separated_audio_urls = get_separated_audio_urls(input_file)
    all_files = {os.path.splitext(file)[0]: url_for('return_separated_file', filename=file) for file in files}
    return render_template('results.html', input_file=input_file, files=files, output_path=output_path, separated_audio_urls=separated_audio_urls, all_files=all_files, url=url)

@socketio.on('start_processing')
def handle_start_processing():
    pass

def pad_audio_files(output_path):
    max_length = 0
    audio_files = []

    # Find the maximum length
    for file in os.listdir(output_path):
        if file.endswith(".mp3"):
            file_path = os.path.join(output_path, file)
            audio = AudioSegment.from_file(file_path)
            audio_files.append((file_path, audio))
            if len(audio) > max_length:
                max_length = len(audio)

    # Pad the audio files with silence to match the maximum length
    for file_path, audio in audio_files:
        padding = AudioSegment.silent(duration=max_length - len(audio))
        padded_audio = audio + padding
        padded_audio.export(file_path, format="mp3")

@app.route('/back', methods=['POST'])
def back():

    return redirect(url_for('index'))

if __name__ == '__main__':
    socketio.run(app, debug=True)
