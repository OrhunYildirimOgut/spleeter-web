from flask import Flask, render_template, request, send_from_directory, jsonify, redirect, url_for, session
import os
from yt_dlp import YoutubeDL
from spleeter.separator import Separator
from pydub import AudioSegment

app = Flask(__name__)
app.secret_key = 'very_very_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

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
        'outtmpl': os.path.abspath('downloads/%(title)s.%(ext)s'),
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_name = ydl.prepare_filename(info)

    input_file = os.path.splitext(file_name)[0] + ".mp3"
    output_path = 'separated_audio'

    separate_audio(input_file, output_path, separation_option)
    
    # Add these lines to set values in the session
    session['input_file'] = input_file
    session['output_path'] = output_path

    return redirect(url_for('results'))

def separate_audio(input_file, output_path, separation_option):
    if separation_option == 'vocal_music':
        model = 'spleeter:2stems'
    elif separation_option == 'vocal_music_bass_drum':
        model = 'spleeter:4stems'
    elif separation_option == 'vocal_music_bass_drum_piano':
        model = 'spleeter:5stems'
    else:
        raise ValueError('Invalid separation option')

    separator = Separator(model)
    separator.separate_to_file(input_file, output_path)

def convert_to_mp3(input_file):
    output_file = os.path.splitext(input_file)[0] + ".mp3"
    audio = AudioSegment.from_file(input_file)
    audio.export(output_file, format="mp3")
    return output_file

def get_separated_audio_urls(input_file, output_path):
    input_filename = os.path.splitext(os.path.basename(input_file))[0]
    output_folder = os.path.join(output_path, input_filename)
    file_urls = {}
    for file in os.listdir(output_folder):
        if file.endswith(".mp3"):
            file_path = os.path.join(output_folder, file).replace("\\", "/")  # Replace backslashes with forward slashes
            file_url = '/return-separated-file/' + file_path
            file_urls[file[:-4]] = file_url
    return file_urls		

@app.route('/return-separated-file/<path:subpath>')
def return_separated_file(subpath):
    directory, filename = os.path.split(subpath)
    return send_from_directory(directory=directory, filename=filename, as_attachment=True)

@app.route('/results', methods=['GET'])
def results():
    if 'input_file' not in session or 'output_path' not in session:
        return redirect(url_for('index'))
    
    input_file = session['input_file']
    output_path = session['output_path']
    files = os.listdir(output_path)

    separated_audio_urls = get_separated_audio_urls(input_file, output_path)

    return render_template('results.html', input_file=input_file, files=files, output_path=output_path, separated_audio_urls=separated_audio_urls)
if __name__ == '__main__':
    app.run(debug=True)
