import sys

sys.path.insert(1, "../backend/")

from flask_cachebuster import CacheBuster
from flask import Flask, redirect, url_for, render_template, request, session
from flask_pymongo import PyMongo, pymongo
from bson.objectid import ObjectId
from datetime import timedelta
import pprint
import json
import os

import uzytkownik as uz
import group

print = pprint.pprint

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/dziennik-dev"
app.secret_key = "pFosAGEabuabfaSDAd"
app.permanent_session_lifetime = timedelta(minutes=15)

config = { 'extensions': ['.js', '.css', '.csv'], 'hash_size': 5 }
cache_buster = CacheBuster(config=config)
cache_buster.init_app(app)

mongo = PyMongo(app)
db = mongo.db

@app.route("/")  # jeśli nie jesteś zalogowany -> przekieruj na stronę logowania, w przeciwnym wypadku -> mainPage
def startPage():
    if "status" in session:
        if session["status"] == "loggedIn":
            return redirect(url_for("main_page"))
        else:
            return redirect(url_for("data_problem"))
    else:
        return redirect(url_for("login_page"))


@app.route("/login", methods=["POST", "GET"])  # prosta stronka z loginem
def login_page():
    if request.method == "POST":
        form_email = request.form["email"]
        form_password = request.form["password"]

        if len(form_email) < 3 or len(form_password) < 3:  # zabezpieczenie przed błędnym wprowadzaniem
            return render_template("loginPage.html")

        # sprawdź tutaj czy takie konto figuruje w bazie danych, jeśli nie - zwróć error
        try:
            uzytkownik = uz.Uzytkownik(db=db, login=form_email)
        except FileNotFoundError:
            return render_template("loginPage.html", wrongPassword=True)

        else:
            rola = uzytkownik.properties["rola"]
            user_id = uzytkownik.get_user_id()
            #return redirect(url_for("mainPage_dev", rola=rola, user_id=user_id))  # DEV

        # dane sesji:
        session.permanent = True
        session["email"] = form_email
        session["status"] = "loggedIn"
        session["rola"] = rola
        session["user_id"] = user_id
        session["imie"] = uzytkownik.properties["imie"]
        session["nazwisko"] = uzytkownik.properties[
            "nazwisko"]  # TODO wymusić na każdym użytkowniku posiadanie imienia i nazwiska w bazie danych
        session["sections"] = []

        # tutaj pobieram dane o liście kategorii, do których dana rola ma dostep

        current_directory = os.path.dirname(__file__)
        temp_path = os.path.join(current_directory, 'static', 'permissions', str(rola) + ".json")

        with open(temp_path) as json_file_1:
            permission_data = json.loads(json_file_1.read())
            for x in permission_data["sections"]:

                inner_file_path = os.path.join(current_directory, x)
                with open(inner_file_path) as json_file_2:

                    temp_data = json.loads(json_file_2.read())
                    session["sections"].append(temp_data)

        return redirect(url_for("main_page"))

    else:
        if "status" in session:
            if session["status"] == "loggedIn":
                return redirect(url_for("main_page"))
            else:
                return redirect(url_for("data_problem"))
        else:
            return render_template("loginPage.html")


@app.route(
    "/main")  # rozumiem to jako pierwsza strona, jaką już zalogowany użytkownik zobaczy, czyli tam gdzie będzie lista funkcji i np. tablica
def main_page():
    if "status" in session:
        return render_template("boardPage.html", session=session)
        # zakładajmy, że każdy użytkownik: admin, nauczyciel, rodzic, uczeń zaczynają od "tablicy powiadomień"
        # a potem dopiero poprzez menu idą do odpowiednich sekcji

    #    if "email" in session:  # tu jest poprawna sesja
    #        email = session["email"]
    #        if "rola" in session:
    #            rola = session["rola"]
    #            if rola == "admin":
    #                return render_template("adminMainPage.html", rola=rola)
    #            else:
    #                return render_template("boardPage.html", email=email)
    #        else:
    #            return render_template("boardPage.html", email=email)
    #    else:
    #        return redirect(url_for("loginPage"))

    else:
        return redirect(url_for("login_page"))


@app.route("/addUsers", methods=["POST", "GET"])
def tworz_uzytkownika_page():
    if "status" in session:
        if session["status"] == "loggedIn":
            temp_sections = session["sections"]
            flag_is_allowed = False
            for temp_section in temp_sections:
                if temp_section["name"] == "addUsersPage":
                    flag_is_allowed = True
                    break
            if flag_is_allowed:
                if request.method == "POST":
                    how_many_new_users = int(request.form["hidden"])

                    classFlag = False
                    peopleFlag = True

                    for iterator in range(how_many_new_users + 1):
                        temp_imie       = request.form["imie_"      + str(iterator)]
                        temp_nazwisko   = request.form["nazwisko_"  + str(iterator)]
                        temp_email      = request.form["email_"     + str(iterator)]
                        temp_password   = request.form["password_"  + str(iterator)]
                        temp_rola       = request.form["rola_"      + str(iterator)]
                        temp_telefon    = request.form["telefon_"   + str(iterator)]
                        temp_adres      = request.form["adres_"     + str(iterator)]

                        temp_properties = {
                            "imie": temp_imie,
                            "nazwisko": temp_nazwisko,
                            "email": temp_email,
                            "password": temp_password,
                            "rola": temp_rola,
                            "telefon": temp_telefon,
                            "adres": temp_adres,
                            "login": temp_email,            # TODO usunąć LOGIN, nie potrzebujemy go, korzystamy jedynie z adresu email
                        }

                        nowy_uzytkownik = uz.Uzytkownik(properties=temp_properties, db=db)

                        if request.form["operacja"]=="klasa":
                            group_name = request.form["group_name"]
                            student_id = nowy_uzytkownik.get_user_id()
                            if(group.add_student(db=db, group_name=group_name, student_id=student_id)):
                                classFlag = True
                    popups = []
                    if classFlag:
                        popups.append("Dodano użytkowników do tej klasy.")
                    if peopleFlag:
                        popups.append("Poprawnie dodano {} nowych użytkowników.".format(how_many_new_users+1))

                    group_names = group.get_all_group_names(db=db)
                    return render_template("tworzUzytkownika.html", groupNames=group_names,  popups=popups) #"Nowy uzytkownik o danych {} został utworzony".format(nowy_uzytkownik.properties)
                else:
                    group_names = group.get_all_group_names(db=db)
                    return render_template("tworzUzytkownika.html", groupNames=group_names)

    return redirect(url_for("data_problem"))


@app.route("/addClass", methods=["POST", "GET"])
def add_class_page():
    if "status" in session:
        if session["status"] == "loggedIn":
            temp_sections = session["sections"]
            flag_is_allowed = False
            for temp_section in temp_sections:
                if temp_section["name"] == "addClassPage":
                    flag_is_allowed = True
                    break
            if flag_is_allowed:
                if request.method == "POST":
                    operation = request.form["operacja"]
                    if operation == "create":
                        properties = {
                            "nazwa" : request.form["class_name"],
                            "rok-rozpoczecia": request.form["first_year"],
                            "uczniowie": []
                        }
                        group.add_group(db=db, properties=properties)
                        popup = "Poprawnie dodano grupę"
                    elif operation == "add_students":
                        how_many_new_users = int(request.form["hidden"])
                        group_name = request.form["group_name"]
                        for iterator in range(how_many_new_users + 1):
                            # print(request.form["email_" + str(iterator)])
                            student = uz.Uzytkownik(db=db, login=request.form["email_" + str(iterator)])
                            student_id = student.properties["_id"]
                            group.add_student(db=db, group_name=group_name, student_id=student_id)
                            popup = "Poprawnie dodano uczniów do grupy"
                    elif operation == "remove_students":
                        how_many_new_users = int(request.form["hidden"])
                        group_name = request.form["group_name"]
                        for iterator in range(how_many_new_users + 1):
                            # print(request.form["email_" + str(iterator)])
                            student = uz.Uzytkownik(db=db, login=request.form["email_" + str(iterator)])
                            student_id = student.properties["_id"]
                            group.remove_student(db=db, group_name=group_name, student_id=student_id)
                            popup = "Poprawnie usunięto uczniów z grupy"
                    list_of_students = uz.Uzytkownik.get_all_users(db=db)
                    group_names = group.get_all_group_names(db=db)
                    return render_template("addClass.html", listOfStudents=list_of_students, groupNames=group_names, popups=[popup])
                else:
                    list_of_students = uz.Uzytkownik.get_all_users(db=db)
                    group_names = group.get_all_group_names(db=db)
                    return render_template("addClass.html", listOfStudents=list_of_students, groupNames=group_names)

    return redirect(url_for("data_problem"))


@app.route("/editTimetable", methods=["POST", "GET"])
def edit_timetable_page():
    if "status" in session:
        if session["status"] == "loggedIn":
            temp_sections = session["sections"]
            flag_is_allowed = False
            for temp_section in temp_sections:
                if temp_section["name"] == "editTimetablePage":
                    flag_is_allowed = True
                    break
            if flag_is_allowed:
                if request.method == "POST":
                    operation = request.form["operacja"]
                    if operation == "create":
                        properties = {
                            "nazwa" : request.form["class_name"],
                            "rok-rozpoczecia": request.form["first_year"],
                            "uczniowie": []
                        }
                        group.add_group(db=db, properties=properties)
                        popup = "Poprawnie dodano grupę"
                    elif operation == "add_students":
                        how_many_new_users = int(request.form["hidden"])
                        group_name = request.form["group_name"]
                        for iterator in range(how_many_new_users + 1):
                            # print(request.form["email_" + str(iterator)])
                            student = uz.Uzytkownik(db=db, login=request.form["email_" + str(iterator)])
                            student_id = student.properties["_id"]
                            group.add_student(db=db, group_name=group_name, student_id=student_id)
                            popup = "Poprawnie dodano uczniów do grupy"
                    elif operation == "remove_students":
                        how_many_new_users = int(request.form["hidden"])
                        group_name = request.form["group_name"]
                        for iterator in range(how_many_new_users + 1):
                            # print(request.form["email_" + str(iterator)])
                            student = uz.Uzytkownik(db=db, login=request.form["email_" + str(iterator)])
                            student_id = student.properties["_id"]
                            group.remove_student(db=db, group_name=group_name, student_id=student_id)
                            popup = "Poprawnie usunięto uczniów z grupy"
                    list_of_students = uz.Uzytkownik.get_all_users(db=db)
                    group_names = group.get_all_group_names(db=db)
                    return render_template("editTimetable.html", listOfStudents=list_of_students, groupNames=group_names, popups=[popup])
                else:
                    chosen_group_name = request.args.get("group_name")
                    chosen_teacher = request.args.get("teacher")
                    chosen_classroom = request.args.get("classroom")
                    teachers = uz.Uzytkownik.get_all_teachers(db)
                    teacher_names = set()
                    for teacher in teachers:
                        print(teacher)
                        teacher_names.add(teacher["imie"] + " " + teacher["nazwisko"])
                    group_names = group.get_all_group_names(db=db)
                    # dev
                    group_timetable = {"monday": {}, "tuesday": {}, "wednesday": {}, "thursday": {}, "friday": {}}
                    teacher_timetable = {"monday": {}, "tuesday": {}, "wednesday": {}, "thursday": {}, "friday": {}}
                    classroom_timetable = {"monday": {}, "tuesday": {}, "wednesday": {}, "thursday": {}, "friday": {}}
                    return render_template("editTimetable.html",
                                           groupNames=group_names,
                                           teacherNames=teacher_names,
                                           chosenGroupName=chosen_group_name,
                                           chosenTeacher=chosen_teacher,
                                           chosenClassroom=chosen_classroom,
                                           groupTimetable=group_timetable,
                                           teacherTimetable=teacher_timetable,
                                           classroomTimetable=classroom_timetable,
                                           )

    return redirect(url_for("data_problem"))


@app.route("/logout", methods=["POST", "GET"])
def logout_page():
    if request.method == "GET":
        try:
            session.clear()
            return render_template("logoutPage.html")
        except:
            return render_template(url_for("data_problem"))
    else:
        return redirect(url_for("login_page"))


@app.route("/dataProblem", methods=["POST", "GET"])  # kiedy np. czas sesji się skończy
def data_problem():
    if request.method == "GET":
        session.clear()
        return render_template("dataProblem.html")
    else:
        return redirect(url_for("login_page"))


@app.route("/<wrongPageURL>", methods=["POST", "GET"])  # "pretty self explanatory"
def wrong_page(wrongPageURL):
    if request.method == "GET":
        return render_template("wrongPage.html", url=wrongPageURL)
    else:
        return redirect(url_for("startPage"))  # this is for "return home" button


if __name__ == "__main__":
    uz1 = uz.Uzytkownik()
    uz1.properties = {"sdfsdf": "sdsdfb", "sdfbsd": "sdifbdsiuf"}

    #db.uzytkownicy.drop()

    print("DEBUG: dziennik - główny moduł")
    if db.uzytkownicy.find_one({"login": "admin"}) is None:
        admin_user_0 = {"login": "admin",
                        "haslo": "admin",
                        "imie": "Administrator",
                        "nazwisko": "",
                        "email": "admin@mail.to",
                        "telefon": "",
                        "rola": "admin"
                        }
        db.uzytkownicy.insert_one(admin_user_0)
    db.uzytkownicy.create_index([('login', pymongo.ASCENDING)], unique=True)
    db.uzytkownicy.create_index([('email', pymongo.ASCENDING)], unique=True)
    app.run(debug=True)
