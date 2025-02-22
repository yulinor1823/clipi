import eventlet
eventlet.monkey_patch()  # 🔥 Asegura que se ejecute antes de cualquier otra importación

from flask import Flask, render_template, request, send_file, jsonify
from flask_socketio import SocketIO
import os
import math
import moviepy.editor as mp
import shutil
import zipfile

app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet")

# Crear carpetas necesarias si no existen
os.makedirs('videos', exist_ok=True)
os.makedirs('audios', exist_ok=True)

processing = False  # Estado del procesamiento

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/split", methods=["GET", "POST"])
def split_media():
    global processing
    if request.method == "POST":
        if processing:
            return jsonify({"status": "error", "message": "Ya hay un proceso en ejecución. Espera o detén el proceso actual."})

        processing = True
        socketio.emit("status", {"message": "🚀 Procesando archivos..."})
        try:
            chunk_size = int(request.form.get("chunk_size", 10))
            video_file = request.files.get("video_file")
            audio_file = request.files.get("audio_file")
            file_list = {"videos": [], "audios": []}

            # Procesar video
            if video_file and video_file.filename.strip():
                video_path = "video_temp.mp4"
                video_file.save(video_path)
                video_clip = mp.VideoFileClip(video_path)
                total_duration = video_clip.duration
                num_chunks = math.ceil(total_duration / chunk_size)

                for i in range(num_chunks):
                    start = i * chunk_size
                    end = min(start + chunk_size, total_duration)
                    subclip = video_clip.subclip(start, end)
                    output_path = f"videos/{i+1}.mp4"
                    subclip.write_videofile(output_path, codec="libx264", audio_codec="aac")

                    socketio.emit("progress", {"progress": ((i + 1) / num_chunks) * 100})
                    eventlet.sleep(0)
                    file_list["videos"].append(output_path)

                video_clip.close()
                os.remove(video_path)

            # Procesar audio
            if audio_file and audio_file.filename.strip():
                audio_path = "audio_temp.mp3"
                audio_file.save(audio_path)
                audio_clip = mp.AudioFileClip(audio_path)
                total_duration = audio_clip.duration
                num_chunks = math.ceil(total_duration / chunk_size)

                for i in range(num_chunks):
                    start = i * chunk_size
                    end = min(start + chunk_size, total_duration)
                    subclip = audio_clip.subclip(start, end)
                    output_path = f"audios/{i+1}.mp3"
                    subclip.write_audiofile(output_path, codec="mp3")

                    socketio.emit("progress", {"progress": ((i + 1) / num_chunks) * 100})
                    eventlet.sleep(0)
                    file_list["audios"].append(output_path)

                audio_clip.close()
                os.remove(audio_path)

            processing = False
            socketio.emit("progress", {"progress": 100})
            return render_template("success.html", files=file_list)

        except Exception as e:
            processing = False
            socketio.emit("status", {"message": f"❌ Error: {str(e)}"})
            return jsonify({"status": "error", "message": str(e)})

    return render_template("upload.html")

@app.route("/clear", methods=["POST"])
def clear_files():
    for folder in ["videos", "audios"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
    return jsonify({"status": "cleared"})

@app.route("/download-zip/<folder>")
def download_zip(folder):
    if folder not in ["videos", "audios"]:
        return "Carpeta no válida", 400

    zip_filename = f"{folder}.zip"
    zip_path = f"{zip_filename}"

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            zipf.write(file_path, os.path.basename(file_path))

    return send_file(zip_path, as_attachment=True)

# 🔥 MODIFICACIÓN: Asegurar que Flask corre en el puerto correcto
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000, debug=True)  # 🔥 Cambia a 0.0.0.0 y usa el puerto 10000

































