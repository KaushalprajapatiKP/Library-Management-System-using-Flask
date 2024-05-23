#Module Imports
from flask_restful import Api, Resource, reqparse, fields, marshal_with, abort
from models import db, Books, Sections

#Initialization
api = Api()

#book output json format
output_format_book = {
    "id" : fields.Integer, 
    "book_name" : fields.String,
    "author_1" : fields.String,
    "author_2" : fields.String,
    "author_3" : fields.String,
    "section_id" : fields.Integer,
    "content" : fields.String
}

#section output json format
output_format_sections = {
    "id" : fields.Integer, 
    "name" : fields.String,
    "description" : fields.String
}


#book parsers
book_parser =  reqparse.RequestParser()
book_parser.add_argument("book_name", type=str)
book_parser.add_argument("author_1", type=str)
book_parser.add_argument("author_2", type=str)
book_parser.add_argument("author_3", type=str)
book_parser.add_argument("section_id", type=int)
book_parser.add_argument("content", type=str)

#section parsers
section_parser =  reqparse.RequestParser()
section_parser.add_argument("name", type=str)
section_parser.add_argument("description", type=str)

#books api class
class BooksAPI(Resource):
    @marshal_with(output_format_book)
    def get(self, book_id):
        book = Books.query.get(int(book_id))
        if book:
            return book
        abort(404, message="Book Not Found")
    
    @marshal_with(output_format_book)
    def put(self, book_id):
        arguments = book_parser.parse_args()
        book = Books. query.get(int(book_id))
        if book:
            for key, value in arguments.items():
                if value != None:
                    setattr(book, key, value)
            db.session.commit()
            return book, 200
        abort(404, message="Book Not Found")
    
    @marshal_with(output_format_book)
    def post(self):
        arguments = book_parser.parse_args()
        book = Books(**arguments)
        db.session.add(book)
        db.session.commit()
        return book, 201
    
    def delete(self, book_id):
        book = Books.query.get(int(book_id))
        if book:
            db.session.delete(book)
            db.session.commit()
            return "", 204
        abort(404, message="Book Not Found")
    

#sections api class
class SectionAPI(Resource):
    @marshal_with(output_format_sections)
    def get(self, section_id):
        section = Sections.query.get(int(section_id))
        print(section)
        if section:
            return section
        abort(404, message="Section Not Found")
    
    @marshal_with(output_format_sections)
    def put(self, section_id):
        arguments = section_parser.parse_args()
        section = Sections.query.get(int(section_id)) 
        if section:
            for key, value in arguments.items():
                if value != None:
                    setattr(section, key, value)
            db.session.commit()
            return section, 200
        abort(404, message="Section Not Found")
    
    @marshal_with(output_format_sections)
    def post(self):
        arguments = section_parser.parse_args()
        section = Sections(**arguments)
        db.session.add(section)
        db.session.commit()
        return section, 201
    
    def delete(self, section_id):
        section = Sections.query.get(int(section_id))
        if section:
            db.session.delete(section)
            db.session.commit()
            return "", 204
        abort(404, message="Section Not Found")
    
