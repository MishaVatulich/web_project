import flask
from data import db_session
from data.books import Books
from flask import jsonify

blueprint = flask.Blueprint('books_api', __name__,
                            template_folder='templates')


@blueprint.route('/api/books')
def get_books():
    session = db_session.create_session()
    books = session.query(Books).all()
    return jsonify(
        {
            'books':
                [item.to_dict(only=('id', 'title', 'cost', 'genre', 'amount', 'created_date', 'user.email',
                                    'user.name', 'user.created_date'))
                 for item in books]
        }
    )


@blueprint.route('/api/books/<int:book_id>',  methods=['GET'])
def get_one_book(book_id):
    session = db_session.create_session()
    book = session.query(Books).get(book_id)
    if not book:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'book': book.to_dict(only=('id', 'title', 'cost', 'genre', 'amount', 'created_date', 'user.email',
                                       'user.name', 'user.created_date'))
        }
    )
