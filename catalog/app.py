from flask import session as login_session
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import make_response
from oauth2client.client import FlowExchangeError, flow_from_clientsecrets
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup_with_user import Base, Category, Item, User
import random
import string
import httplib2
import json
import requests
app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']

engine = create_engine('sqlite:///catalogwithuser.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Login Route
@app.route('/login')
def getState():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return state


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Function to connect to google."""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
            "Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return redirect(url_for('itemCatalog'))


@app.route('/gdisconnect')
def gdisconnect():
    """Revoking acess from the user."""
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2' \
          '/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('itemCatalog'))
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/items.json')
def itemsJson():
    """Return serialized json data of all items."""
    if 'username' not in login_session:
        state = getState()
        items = session.query(Item).all()
        return render_template("listall.html", items=items,
                               STATE=state, login=login_session,
                               snack="Not logged in")
    else:
        items = session.query(Item).all()
        return jsonify(Items=[i.serialize for i in items])


@app.route('/items/<int:item_id>/json')
def itemJson(item_id):
    """Return serialized json data of a single item"""
    if 'username' not in login_session:
        state = getState()
        items = session.query(Item).all()
        return render_template("listall.html", items=items,
                               STATE=state, login=login_session,
                               snack="Not logged in")
    else:
        item = session.query(Item).filter_by(id=item_id).one()
        return jsonify(Item=item.serialize)


@app.route('/')
@app.route('/items')
def itemCatalog():
    """Listing all the items in the catalog."""
    state = getState()
    items = session.query(Item).all()
    return render_template("listall.html",
                           items=items, STATE=state, login=login_session)


@app.route('/items/new', methods=['GET', 'POST'])
def newItem():
    """Function to create a new item."""
    # Checking if a user is logged in or not
    if 'username' not in login_session:
        state = getState()
        items = session.query(Item).all()
        return render_template("listall.html", items=items,
                               STATE=state,
                               login=login_session, snack="Not logged in")
    else:
        if request.method == 'POST':
            print "here at post"
            cat = session.query(Category).filter_by(
                name=request.form['category']).one()
            item = Item(name=request.form['name'], description=request.form[
                        'description'], price=request.form['price'],
                        category_id=cat.id,
                        user_id=login_session['user_id'])
            session.add(item)
            session.commit()
            state = getState()
            items = session.query(Item).all()
            return render_template("listall.html", items=items,
                                   STATE=state, login=login_session)
        return render_template("newitem.html", login=login_session)


@app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    """Function to edit a item using the item id."""
    # Checking if user is logged in or not.
    if 'username' not in login_session:
        state = getState()
        items = session.query(Item).all()
        return render_template("listall.html", items=items, STATE=state,
                               login=login_session, snack="Not logged in")
    else:
        item = session.query(Item).filter_by(id=item_id).one()
        # Checking if the user is actual owner of item.
        if login_session['user_id'] != item.user_id:
            state = getState()
            items = session.query(Item).all()
            return render_template("listall.html", items=items, STATE=state,
                                   login=login_session,
                                   snack="You can edit your own items only.")
        else:
            if request.method == 'POST':
                item.name = request.form['name']
                item.price = request.form['price']
                item.description = request.form['description']
                cat = session.query(Category).filter_by(
                    name=request.form['category']).one()
                item.category = cat
                session.add(item)
                session.commit()
                return redirect(url_for('itemCatalog'))
            return render_template("edititem.html", item=item,
                                   login=login_session)


@app.route('/items/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    """Function to delete an item using item id."""
    # Checking if a user is logged in or not.
    if 'username' not in login_session:
        state = getState()
        items = session.query(Item).all()
        return render_template("listall.html",
                               items=items, STATE=state, login=login_session,
                               snack="Not logged in")
    else:
        item = session.query(Item).filter_by(id=item_id).one()
        # Checking if user is owner of item or not.
        if login_session['user_id'] != item.user_id:
            state = getState()
            items = session.query(Item).all()
            return render_template("listall.html", items=items, STATE=state,
                                   login=login_session,
                                   snack="You can delete your own items only.")
        else:
            if request.method == 'POST':
                session.delete(item)
                session.commit()
                return redirect(url_for('itemCatalog'))

            return render_template("deleteItem.html", login=login_session)


# Getting user id.
def getUserId(email):
    try:
        user = session.query(User).filter_by(
            email=login_session['email']).one()
        return user.id
    except:
        return None


# Getting user information.
def getUser(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Creating user.
def createUser(login_session):
    newuser = User(name=login_session['username'],
                   email=login_session['email'])
    session.add(newuser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Entry point for a server.
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
