import os
from flask import Flask, jsonify
import requests
import redis
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
CACHE_TIME = os.getenv('REDIS_CACHE_TIME')
PORT = os.getenv('SERVER_PORT')

r = redis.Redis(host='redis', port=6379, db=0)

app = Flask(__name__)

headers = {
    'X-Api-Key': API_KEY
}

def get_definition(word):
    cache_key = f"definition:{word}"
    cached_result = r.get(cache_key)
    if cached_result:
        return {
            "source": "redis",
            "word": word,
            "definition": cached_result.decode('utf-8')
        }
    else:
        url = f"https://api.api-ninjas.com/v1/dictionary?word={word}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            definition = data.get('definition')
            if definition:
                r.setex(cache_key, CACHE_TIME, definition)
                return {
                    "source": "api-ninjas",
                    "word": word,
                    "definition": definition
                }
    return None

@app.route('/define/<word>', methods=['GET'])
def define_word_route(word):
    result = get_definition(word)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "Definition not found"}), 404

@app.route('/random-word', methods=['GET'])
def random_word():
    max_retries = 5
    for _ in range(max_retries):
        url = "https://api.api-ninjas.com/v1/randomword"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            word = response.json()['word']
            result = get_definition(word[0])
            if result:
                return jsonify(result)
    return jsonify({"error": "Could not find a word with definition"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)