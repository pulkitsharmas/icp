import sys
# Importing all important Classes
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


# Main User Class
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


# Main Category Class
class Category(Base):
    __tablename__ = 'category'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)


# Main Item Class
class Item(Base):
    __tablename__ = 'item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price = Column(String(10), nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    # Serialize

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category.name,
            'owner': self.user.name,
            'email': self.user.email
        }

# Creating Database
engine = create_engine('sqlite:///catalogwithuser.db')
Base.metadata.create_all(engine)
