from flask import Flask, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid
import hashlib
import base64
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@localhost/shortener'
db = SQLAlchemy(app)


class ShortenedURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.String(50), nullable=False)
    bot_id = db.Column(db.String(50), nullable=False)
    original_url = db.Column(db.String(2048), nullable=False)
    short_hash = db.Column(db.String(16), unique=True, nullable=False)
    visits = db.Column(db.Integer, default=0)


db.create_all()


def generate_unique_hash(post_id, bot_id):
    while True:
        raw_data = f"{uuid.uuid4().hex}{post_id}{bot_id}"
        short_hash = base64.urlsafe_b64encode(hashlib.sha256(raw_data.encode()).digest())[:10].decode()
        if not ShortenedURL.query.filter_by(short_hash=short_hash).first():
            return short_hash


@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.json
    urls = data.get("urls", [])
    post_id = data.get("post_id")
    bot_id = data.get("bot_id")

    if not post_id or not bot_id:
        return jsonify({"error": "post_id and bot_id are required"}), 400

    result = []
    for url in urls:
        while True:
            try:
                short_hash = generate_unique_hash(post_id, bot_id)
                new_url = ShortenedURL(original_url=url, short_hash=short_hash, post_id=post_id, bot_id=bot_id)
                db.session.add(new_url)
                db.session.commit()
                break
            except IntegrityError:
                db.session.rollback()
        result.append({"original": url, "short": f"http://localhost:5000/{short_hash}"})

    return jsonify(result)


@app.route('/<short_hash>', methods=['GET'])
def redirect_to_original(short_hash):
    entry = ShortenedURL.query.filter_by(short_hash=short_hash).first()
    if entry:
        entry.visits += 1
        db.session.commit()
        return redirect(entry.original_url)
    return "URL not found", 404


if __name__ == '__main__':
    app.run(debug=True)