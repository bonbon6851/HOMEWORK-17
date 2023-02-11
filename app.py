import sqlalchemy
from flask import Flask, request, jsonify
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
app.url_map.strict_slashes = False
db = SQLAlchemy(app)

api = Api(app)

movie_ns = api.namespace('movies')


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Integer)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class MovieSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Int()
    genre_id = fields.Int()
    director_id = fields.Int()


movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)


@movie_ns.route('/')
class MoviesView(Resource):
    def get(self):
        """
        Метод для обработки GET запроса для возвращения данных всех фильмов или с определенным фильтром
        """
        # обработка запроса по поиску фильмов по режиссеру
        did = request.args.get('director_id')
        if did:
            movies = db.session.query(Movie).filter(Movie.director_id == did).all()
            if movies:
                return movies_schema.dump(movies), 200
            return "Фильмы такого режиссера не найдены"

        # обработка запроса по поиску фильмов по жанру
        gid = request.args.get('genre_id')
        if gid:
            movies = db.session.query(Movie).filter(Movie.genre_id == gid).all()
            if movies:
                return movies_schema.dump(movies), 200
            return "Фильмы такого жанра не найдены"

        # возвращаем всех пользователей при обращении к адресу '/movies'
        movies = db.session.query(Movie).all()
        if movies:
            return movies_schema.dump(movies), 200
        return "Фильм не найден"

    def post(self):
        movie = request.json
        # Обработка исключения при попытке добавления записи с не уникальным primary key
        try:
            db.session.add(Movie(**movie))
            db.session.commit()
            return 'Фильм добавлен', 201
        except sqlalchemy.exc.IntegrityError as error:
            return f'{error}'


@movie_ns.route('/<int:mid>')
class MovieView(Resource):
    def get(self, mid):
        """
        Метод для обработки GET запроса для возвращения данных конкретного фильма
        """
        movie = db.session.query(Movie).get(mid)
        if movie:
            return movie_schema.dump(movie), 200
        return "Фильм не найден", 404

    def put(self, mid):
        """
        Метод для обработки PUT запроса на обновления данных фильма
        """
        movie = db.session.query(Movie).get(mid)
        if movie:
            try:
                db.session.query(Movie).filter(Movie.id == mid).update(request.json)
                db.session.commit()
                return 200
                # Обработка исключения при попытке обновления записи с не уникальным primary key
            except sqlalchemy.exc.IntegrityError as error:
                return f'{error}'
                # Обработка исключения при попытке обновления записи с не несоответствующими столбцами
            except sqlalchemy.exc.InvalidRequestError as error:
                return f'{error}'
        return f"Фильм с id {mid} не найден"

    def delete(self, mid):
        """
        Метод для обработки DELETE запроса для удаления конкретного фильма
        """
        movie = db.session.query(Movie).get(mid)
        if movie:
            db.session.delete(movie)
            db.session.commit()
            return 200
        return f"Фильм с id {mid} не найден", 404


@app.errorhandler(404)
def error_404(error):
    """
    Вьюшка для обработки не найденной страницы
    """
    return f"Страница не найдена. Ошибка: {error}", 404


@app.errorhandler(400)
def error_400(error):
    """
    Вьюшка для обработки при не корректном json запросе
    """
    return f"Возможно, проблема в json запросе. Ошибка: {error}", 400


if __name__ == '__main__':
    app.run()
