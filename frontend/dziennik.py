from flask import Flask, redirect, url_for, render_template, request, session

app = Flask(__name__)
app.secret_key = "pFosAGEabuabfaSDA"


@app.route("/")  # jeśli nie jesteś zalogowany -> przekieruj na stronę logowania, w przeciwnym wypadku -> mainPage
def startPage():
    if "status" in session:
        if session["status"] == "loggedIn":
            return redirect(url_for("mainPage"))
        else:
            return redirect(url_for("dataProblem"))
    else:
        return redirect(url_for("loginPage"))



@app.route("/login", methods=["POST", "GET"])  # prosta stronka z loginem
def loginPage():
    if request.method == "POST":
        formEmail = request.form["email"]
        formPassword = request.form["password"]

        if len(formEmail) < 1 or len(formPassword) < 1:  # zabezpieczenie przed błędnym wprowadzaniem
            return render_template("loginPage.html")

        # sprawdź tutaj czy takie konto figuruje w bazie danych, jeśli nie - zwróć error

        # dane sesji:
        session["email"] = formEmail
        session["password"] = formPassword  # to idzie później w kosz, nie chcemy hasła trzymać w sesji, używamy go jedynie do autentykacji na początku
        session["status"] = "loggedIn"

        return redirect(url_for("mainPage"))
    else:
        if "status" in session:
            if session["status"] == "loggedIn":
                return redirect(url_for("mainPage"))
            else:
                return redirect(url_for("dataProblem"))
        else:
            return render_template("loginPage.html")



@app.route("/main")  # rozumiem to jako pierwsza strona, jaką już zalogowany użytkownik zobaczy, czyli tam gdzie będzie lista funkcji i np. tablica
def mainPage():
    if "status" in session:
        if "email" in session:  # tu jest poprawna sesja
            email = session["email"]
            return render_template("boardPage.html", email=email)



        else:
            return redirect(url_for("loginPage"))
    else:
        return redirect(url_for("loginPage"))



@app.route("/logout", methods=["POST", "GET"])
def logoutPage():
    if request.method == "GET":
        try:
            session.clear()
            return render_template("logoutPage.html")
        except:
            return render_template(url_for("dataProblem"))
    else:
        return redirect(url_for("loginPage"))


@app.route("/dataProblem", methods=["POST", "GET"])  # kiedy np. braknie gdzieś twojego maila w sesji, bądź czas sesji się skończy
def dataProblem():
    if request.method == "GET":
        session.clear()
        return render_template("dataProblem.html")
    else:
        return redirect(url_for("loginPage"))



@app.route("/<wrongPageURL>", methods=["POST", "GET"])  # "pretty self explanatory", zastąpienie wadliwego adresu naszą stronką, aby nie było basic error screen'a
def wrongPage(wrongPageURL):
    if request.method == "GET":
        return render_template("wrongPage.html", url=wrongPageURL)
    else:
        return redirect(url_for("startPage"))  # this is for "return home" button



if __name__ == "__main__":
    app.run(debug=True)
