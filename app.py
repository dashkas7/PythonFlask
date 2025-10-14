from flask import Flask, render_template, request, redirect, url_for, session
import requests, random
import json, os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key"
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("main.html")

@app.route("/duck/", endpoint="duck")
@login_required
def duck():
    response = requests.get("https://random-d.uk/api/random")
    data = response.json()
    duck_url = data["url"]
    duck_number = random.randint(1, 999)
    return render_template("duck.html", duck_url=duck_url, duck_number=duck_number)

@app.route("/fox/", endpoint="fox")
@app.route("/fox/<int:number>/", endpoint="fox")
@login_required
def fox(number=None):
    if number is None:
        number = 1
    if number < 1 or number > 10:
        return '<h1 style="color:red; text-align:center; font-size:48px">Можно выбрать количество от 1 до 10</h1>'

    response = requests.get("https://randomfox.ca/floof/")
    data = response.json()
    fox_url = data["image"]

    foxs = [fox_url] * number
    return render_template("fox.html", foxs=foxs, number=number)



@app.route("/dogs/")
@login_required
def dogs():
    return render_template("dogs.html")

@app.route("/weather-minsk/", endpoint="weather_minsk")
@login_required
def weather_minsk():
    url = "https://api.open-meteo.com/v1/forecast?latitude=53.9&longitude=27.5667&current_weather=true"
    data = requests.get(url).json()
    weather = data.get("current_weather", {})
    return render_template("weatherminsk.html", temp=weather.get("temperature"), wind=weather.get("windspeed"))

@app.route("/weather/", endpoint="weather_city")
@app.route("/weather/<city>/", endpoint="weather_city")
@login_required
def weather_city(city=None):
    if city is None:
        city = "Gomel"

    geo_url = f"https://nominatim.openstreetmap.org/search?city={city}&format=json&limit=1"
    geo_resp = requests.get(geo_url, headers={"User-Agent": "Mozilla/5.0"}).json()

    if not geo_resp:
        return f"<h1>Город '{city}' не найден</h1>"

    lat = geo_resp[0]["lat"]
    lon = geo_resp[0]["lon"]

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    data = requests.get(url).json()

    weather = data.get("current_weather", {})
    temp = weather.get("temperature", "?")
    wind = weather.get("windspeed", "?")

    return render_template("weathercity.html", temp=temp, wind=wind, city=city.capitalize())


@app.route("/homework/")
@login_required
def homework():
    return render_template("homework.html")

@app.route("/rates/")
@login_required
def rates():
    url = "https://www.nbrb.by/api/exrates/rates?periodicity=0"
    data = requests.get(url).json()
    return render_template("rates.html", rates=data)

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_val = request.form.get("login")
        password = request.form.get("password")
        users = load_users()
        user = users.get(login_val)
        if user and check_password_hash(user["password"], password):
            session["user"] = {"login": login_val, "name": user["name"], "surname": user["surname"]}
            return redirect(url_for("index"))
        return render_template("login.html", error="Неверный логин или пароль")
    return render_template("login.html")

@app.route("/registration/", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        login_val = request.form.get("login")
        password = request.form.get("password")
        users = load_users()
        if login_val in users:
            return render_template("registration.html", error="Логин занят")
        users[login_val] = {
            "name": request.form.get("name"),
            "surname": request.form.get("surname"),
            "password": generate_password_hash(password)
        }
        save_users(users)
        return redirect(url_for("login"))
    return render_template("registration.html")

@app.route("/logout/")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
