from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from textblob import TextBlob
from googleapiclient.discovery import build
import os

# Replace with your actual API key
YOUTUBE_API_KEY = "AIzaSyCbrA2Bo8uQTpUzhUI42Drh8nvz0fr6YH0"

app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("text", "")
    sentiment = analyze_sentiment(text)
    return jsonify({"sentiment": sentiment})

@app.route("/analyze_youtube", methods=["POST"])
def analyze_youtube():
    data = request.get_json()
    url = data.get("url", "")

    if not url or "v=" not in url:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    video_id = url.split("v=")[-1].split("&")[0]

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=50,
            textFormat="plainText"
        ).execute()

        comments = []
        counts = {"Positive": 0, "Negative": 0, "Neutral": 0}

        for item in response.get("items", []):
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            sentiment = analyze_sentiment(text)
            counts[sentiment] += 1
            comments.append({"text": text, "sentiment": sentiment})

        total = sum(counts.values())
        percentages = {
            "Positive": round((counts["Positive"] / total) * 100, 2) if total else 0,
            "Negative": round((counts["Negative"] / total) * 100, 2) if total else 0,
            "Neutral": round((counts["Neutral"] / total) * 100, 2) if total else 0,
        }

        return jsonify({"comments": comments, "percentages": percentages})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/upload_file", methods=["POST"])
def upload_file():
    file = request.files["file"]
    content = file.read().decode("utf-8").splitlines()

    comments = []
    for line in content:
        sentiment = analyze_sentiment(line)
        comments.append({"text": line, "sentiment": sentiment})

    return jsonify({"comments": comments})

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

if __name__ == "__main__":
    app.run(debug=True)
