from flask import Flask, request, jsonify
import os
import tempfile
import subprocess

app = Flask(__name__)
storage_bucket = os.environ.get("STORAGE_BUCKET", "my-spleeter-files")

@app.route("/separate", methods=["POST"])
def separate():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "File not provided"}), 400

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = os.path.join(tmp_dir, "input.mp3")
        file.save(input_path)

        output_path = os.path.join(tmp_dir, "output")
        os.makedirs(output_path)

        result = subprocess.run(["spleeter", "separate", "-i", input_path, "-o", output_path], capture_output=True)

        if result.returncode != 0:
            return jsonify({"error": "Spleeter failed to separate tracks"}), 500

        # TODO: Save the output files to Google Cloud Storage and return the URLs.

    return jsonify({"success": True}))