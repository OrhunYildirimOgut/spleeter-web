# spleeter-web

The purpose of this application is to divide the entered song link into parts according to the selected option (vocals, drums, etc.) and then offer the opportunity to download

In building the music separation web app, I used Flask, a lightweight Python web framework, to handle the server-side logic and rendering. Spleeter, an open-source deep learning library by Deezer, was used to separate the audio components. Youtube-dl, a command-line program, enabled me to download videos and extract audio from YouTube. The app's construction process involved setting up a Flask application, integrating the Youtube-dl library to fetch audio, and using Spleeter to separate the audio into different stems.

I am still developing this app. I fix certain bugs and add new features. I will connect to a domain in google cloud using virtual machine soon. Now the application can download the song and divide it into parts according to the desired.
