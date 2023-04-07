from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests, os


# Creating Database
app = Flask(__name__)
app.app_context().push()
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
Bootstrap(app)
db = SQLAlchemy(app)


# API
MOVIE_API_URL = "https://api.themoviedb.org/3"
MOVIE_DB_API_KEY = os.environ.get("TMDB_API_KEY")
TMDB_IMAGE_URL = 'https://image.tmdb.org/t/p/w500'



# Creating Table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(150))
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer, unique=True)
    review = db.Column(db.Text)
    img_url = db.Column(db.String(250), unique=True, nullable=False)

    def __repr__(self):
        return f"{self.title} - {self.rating}"


db.create_all()

# Flask Forms
class RateMovieForm(FlaskForm):
    rating = FloatField(label="Your Rating Out of 10 e.g. 7.5", validators=[DataRequired(), NumberRange(min=1, max=10)])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class FindMovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")

# Routes
@app.route("/")
def home():
    all_movies = db.session.query(Movie).all()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = FindMovieForm()
    if form.validate_on_submit():
        title = form.title.data
        response = requests.get(f'{MOVIE_API_URL}/search/movie', params={"api_key": MOVIE_DB_API_KEY, "query": title})
        data = response.json()['results']
        return render_template('select.html', options=data)

    return render_template("add.html", form=form)


@app.route("/find/<int:id>", methods=['GET'])
def find(id):
    response = requests.get(f"{MOVIE_API_URL}/movie/{id}", params={"api_key": MOVIE_DB_API_KEY})
    data = response.json()
    new_movie = Movie(
        title=data['title'],
        img_url=f"{TMDB_IMAGE_URL}{data['poster_path']}",
        year=data["release_date"].split("-")[0],
        description=data['overview']
    )
    db.session.add(new_movie)
    db.session.commit()
    print(new_movie)
    return redirect(url_for("edit_rating", id=new_movie.id))


@app.route("/edit/<int:id>", methods=['GET', 'POST'])
def edit_rating(id):
    form = RateMovieForm()
    if form.validate_on_submit():
        movie_to_update = Movie.query.get(id)
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
