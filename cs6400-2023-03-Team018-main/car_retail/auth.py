from flask import Blueprint, render_template, redirect, url_for, request, session
from .database import check_login, get_roles

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_login(username,password):
            session['username'] = username
            roles = get_roles(username)
            if 'Manager' in roles:
                session['is_manager'] = True
            if 'Inventory Clerk' in roles:
                session['is_inventory_clerk'] = True
            if 'Salesperson' in roles:
                session['is_salesperson'] = True
            if 'Owner' in roles:
                session['is_manager'] = True
                session['is_inventory_clerk'] = True
                session['is_salesperson'] = True
            
            return redirect(url_for('main.home'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@auth.route('/logout')
def logout():
    if session.get('username'):
        session.pop('username', None)
        session.pop('is_manager', False)
        session.pop('is_inventory_clerk', False)
        session.pop('is_salesperson', False)
        return redirect(url_for('main.home'))
    else:
        return redirect(url_for('auth.login'))

def is_manager():
    if 'is_manager' in session:
        return session['is_manager']
    return False

def is_inventory_clerk():
    if 'is_inventory_clerk' in session:
        return session['is_inventory_clerk']
    return False

def is_salesperson():
    if 'is_salesperson' in session:
        return session['is_salesperson']
    return False

def get_loggedin_user():
    if 'username' in session:
        return session['username']
    return ''

