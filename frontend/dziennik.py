from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route("/")                     # jeśli nie jesteś zalogowany -> przekieruj na stronę logowania, w przeciwnym wypadku -> mainPage
def startPage():
    #if loggedIn:
    #    go to mainPage()
    #else:
        return redirect(url_for("loginPage"))

@app.route("/login")                # prosta stronka z loginem
def loginPage():
    return "<h1>Tekst do testu</h1>"


#@app.route("/<name>")              # rozumiem to jako pierwsza strona, jaką już zalogowany użytkownik zobaczy, czyli tam gdzie będzie lista funkcji i np. tablica
def mainPage(name):
    return f"Hello {name}"


@app.route("/<wrongPageURL>")       # "pretty self explanatory", zastąpienie wadliwego adresu naszą stronką, aby nie było basic error screen'a
def wrongPage(wrongPageURL):
    return f"Sorry, the URL you provided: <h3>{wrongPageURL}</h3> is not valid, and thus I can't redirect you anywhere."



if __name__ == "__main__":
    app.run()

