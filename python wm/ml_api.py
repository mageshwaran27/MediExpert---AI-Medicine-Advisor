from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/classify', methods=['POST'])
def classify():
    data = request.json
    image_path = data.get("image_path")
    labels = ["organic", "plastic", "mixed", "drainage_leak", "burning"]
    result = {
        "suggested_label": random.choice(labels),
        "confidence": round(random.uniform(0.7, 0.99), 2)
    }
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
