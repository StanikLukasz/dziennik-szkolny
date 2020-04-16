from flask import Flask, redirect, url_for, render_template, request

app = Flask(__name__)


@app.route("/")  # jeśli nie jesteś zalogowany -> przekieruj na stronę logowania, w przeciwnym wypadku -> mainPage
def startPage():
    # if loggedIn:
    #    go to mainPage()
    # else:
    return redirect(url_for("loginPage"))



@app.route("/login", methods=["POST", "GET"])  # prosta stronka z loginem
def loginPage():
    if request.method == "POST":
        formEmail = request.form["email"]
        formPassword = request.form["password"]

        # sprawdź tutaj czy takie konto figuruje w bazie danych, jeśli nie - zwróć error
        return redirect(url_for("mainPage", name=formEmail, password=formPassword))
    else:
        return render_template("loginPage.html")



@app.route("/main-<name>-<password>")  # rozumiem to jako pierwsza strona, jaką już zalogowany użytkownik zobaczy, czyli tam gdzie będzie lista funkcji i np. tablica
def mainPage(name, password):
    return f"Hello {name}. I know your password. Shhh... It's {password}, am I right mate?"


@app.route("/<wrongPageURL>")  # "pretty self explanatory", zastąpienie wadliwego adresu naszą stronką, aby nie było basic error screen'a
def wrongPage(wrongPageURL):
    return f"Sorry, the URL you provided: <h3>{wrongPageURL}</h3> is not valid, and thus I can't redirect you anywhere."


if __name__ == "__main__":
    app.run(debug=True)
