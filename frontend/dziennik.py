from flask import Flask

app = Flask(__name__)


@app.route("/login")
def loginPage():
    return "<h1>Tekst do testu</h1>"







if __name__ == "__main__":
    app.run()

