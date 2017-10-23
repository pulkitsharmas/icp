from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item
app = Flask(__name__)

from flask import session as login_session
import random, string



engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()


@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state
	return login_session['state']

@app.route('/')
@app.route('/items')
def itemCatalog():
	items = session.query(Item).all();
	return render_template("listall.html", items=items);
@app.route('/items/<int:item_id>')
def singleItem(item_id):
	return "details of a single item"

@app.route('/items/new', methods=['GET','POST'])
def newItem():
	if request.method == 'POST':
		cat = session.query(Category).filter_by(name=request.form['category']).one()

		item = Item(name=request.form['name'],description=request.form['description'],price=request.form['price'],category_id=cat.id)
		session.add(item)
		session.commit()
		return redirect(url_for('itemCatalog'))
	return render_template("newitem.html")

@app.route('/items/<int:item_id>/edit', methods=['GET','POST'])
def editItem(item_id):
	item = session.query(Item).filter_by(id=item_id).one()
	if request.method == 'POST':
		item.name = request.form['name']
		item.price = request.form['price']
		item.description = request.form['description']
		cat = session.query(Category).filter_by(name=request.form['category']).one()
		item.category = cat
		session.add(item)
		session.commit();
		return redirect(url_for('itemCatalog'))
	return render_template("edititem.html",item=item)

@app.route('/items/<int:item_id>/delete', methods=['GET','POST'])
def deleteItem(item_id):
	item = session.query(Item).filter_by(id=item_id).one()
	if request.method == 'POST':
		session.delete(item)
		session.commit()
		return redirect(url_for('itemCatalog'))

	return render_template("deleteItem.html")

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5000)