from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Assistant Intelligent RH"

if __name__ == "__main__":
    app.run(debug=True)