from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models

class Author(db.Model):
    __tablename__ = 'authors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    phone_number = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'Author(id={self.id}, name={self.name})'

    @validates('name')
    def validate_name(self, key, name):
        if not name:
            raise ValueError("Name field is required.")
        author = Author.query.filter_by(name=name).first()
        if author is not None:
            raise ValueError("Name must be unique.")
        return name

    @validates('phone_number')
    def validate_phone_number(self, key, phone_number):
        if phone_number and (len(phone_number) != 10 or not phone_number.isdigit()):
            raise ValueError("Phone number must be 10 digits.")
        return phone_number

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.String)
    category = db.Column(db.String)
    summary = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'Post(id={self.id}, title={self.title})'

    @validates('title')
    def validate_title(self, key, title):
        if not title:
            raise ValueError("Title field is required.")
        clickbait = ["Won't Believe", "Secret", "Top", "Guess"]
        if not any(substring in title for substring in clickbait):
            raise ValueError("Title must contain clickbait phrases.")
        return title

    @validates('content')
    def validate_content(self, key, content):
        if content and len(content) < 250:
            raise ValueError("Post content must be at least 250 characters long.")
        return content

    @validates('summary')
    def validate_summary(self, key, summary):
        if summary and len(summary) > 250:
            raise ValueError("Post summary must be at most 250 characters long.")
        return summary

    @validates('category')
    def validate_category(self, key, category):
        if category not in ['Fiction', 'Non-Fiction']:
            raise ValueError("Category must be 'Fiction' or 'Non-Fiction'.")
        return category

# Routes

@app.route('/authors', methods=['GET'])
def get_authors():
    authors = Author.query.all()
    return jsonify([author.__dict__ for author in authors])

@app.route('/authors', methods=['POST'])
def create_author():
    data = request.get_json()
    new_author = Author(name=data['name'], phone_number=data.get('phone_number'))
    db.session.add(new_author)
    db.session.commit()
    return jsonify(new_author.__dict__), 201

@app.route('/posts', methods=['GET'])
def get_posts():
    posts = Post.query.all()
    return jsonify([post.__dict__ for post in posts])

@app.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    new_post = Post(
        title=data['title'],
        content=data.get('content'),
        category=data.get('category'),
        summary=data.get('summary')
    )
    db.session.add(new_post)
    db.session.commit()
    return jsonify(new_post.__dict__), 201

@app.route('/posts/<int:id>', methods=['GET'])
def get_post(id):
    post = Post.query.get(id)
    if not post:
        return make_response(jsonify({'error': 'Post not found'}), 404)
    return jsonify(post.__dict__)

@app.route('/posts/<int:id>', methods=['PATCH'])
def update_post(id):
    post = Post.query.get(id)
    if not post:
        return make_response(jsonify({'error': 'Post not found'}), 404)
    
    data = request.get_json()
    for key, value in data.items():
        setattr(post, key, value)
    
    db.session.commit()
    return jsonify(post.__dict__)

@app.route('/posts/<int:id>', methods=['DELETE'])
def delete_post(id):
    post = Post.query.get(id)
    if not post:
        return make_response('', 204)
    
    db.session.delete(post)
    db.session.commit()
    return make_response('', 204)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)