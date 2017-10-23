from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

category1 = Category(name = "Clothing")
session.add(category1)
session.commit()

item1 = Item(name="Shirt", description="Another cotton shirt",
	price="100", category=category1)
session.add(item1)
session.commit()

item2 = Item(name="Trouser", description="Another cotton trouser",
	price="80", category=category1)
session.add(item2)
session.commit()

category2 = Category(name = "Footwear")
session.add(category2)
session.commit()

item3 = Item(name="Oxfords", description="Tan oxford shoes",
	price="150", category=category2)
session.add(item3)
session.commit()

item4 = Item(name="Slippers", description="Another classic slippers",
	price="50", category=category2)
session.add(item4)
session.commit()

category3 = Category(name = "Accessories")
session.add(category3)
session.commit()

item5 = Item(name="Sunglasses", description="Another sunglasses",
	price="100", category=category3)
session.add(item5)
session.commit()

item6 = Item(name="Tie", description="Another silk tie",
	price="100", category=category3)
session.add(item6)
session.commit()
