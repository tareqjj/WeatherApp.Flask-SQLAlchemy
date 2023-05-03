from flask import Flask, render_template, request, redirect, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
import datetime
import requests
import sys

app = Flask(__name__)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///weatherApp.db"
app.config["SECRET_KEY"] = "So-Seckrekt"
db.init_app(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)


with app.app_context():
    db.create_all()


def get_weather_api(city_name):
    api_key = "6bc14013749d2f5bcb707a41db60eb24"
    get_weather = requests.get("https://api.openweathermap.org/data/2.5/weather",
                               params={"q": city_name, "units": "metric", "appid": api_key}).json()
    if get_weather["cod"] == 200:
        weather_info = {"name": get_weather["name"], "temp": int(get_weather["main"]["temp"]),
                        "weather": get_weather["weather"][0]["description"].title(),
                        "timezone": get_weather["timezone"]}
        if db.session.execute(db.select(City.name).filter_by(name=city_name)).scalar() is None:
            db.session.add(City(name=city_name))
            db.session.commit()
        city_id = db.session.execute(db.select(City.id).filter_by(name=city_name)).scalar()
        weather_info["city_id"] = city_id
        return weather_info
    else:
        flash("The city doesn't exist!")
        return redirect("/")


def get_cities_data():
    cities_name = db.session.execute(db.select(City.name)).scalars()
    cities_weather_list = []
    for city_name in cities_name:
        city_weather = get_weather_api(city_name)
        local_time_hour = (datetime.datetime.utcnow() + datetime.timedelta(seconds=city_weather["timezone"])).hour
        if local_time_hour in range(6, 12) or local_time_hour in range(17, 20):
            card_img = "evening-morning"
        elif local_time_hour in range(12, 17):
            card_img = "day"
        else:
            card_img = "night"
        city_weather["card_img"] = card_img
        cities_weather_list.append(city_weather)
    return cities_weather_list


@app.route("/", methods=["GET", "POST"])
def index():
    cities_list = get_cities_data()
    if request.method == "GET":
        return render_template("index.html", cities_list=cities_list)
    if request.method == "POST":
        city_name = request.form["city_name"]
        if db.session.execute(db.select(City.name).filter_by(name=city_name)).scalar() is not None:
            flash("The city has already been added to the list!")
            return redirect("/")
        get_weather_api(city_name)
        return redirect("/")


@app.route("/delete/<city_id>", methods=["POST"])
def delete(city_id):
    get_city = db.get_or_404(City, city_id)
    db.session.delete(get_city)
    db.session.commit()
    return redirect("/")


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
