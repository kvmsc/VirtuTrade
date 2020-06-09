from flask import request, render_template, redirect, url_for, flash
from werkzeug.urls import url_parse
from flask_login import login_user, login_required, current_user, logout_user
from app import app, db
from app.models import User, Transaction
from app.forms import LoginForm, RegistrationForm, QuoteForm, BuyForm, SellForm
from helper import get_quote, get_quote_latest

@app.route('/')
@login_required
def index():
    current_stocks = db.session.query(Transaction.ticker, Transaction.name, 
                                        db.func.sum(Transaction.qty)).filter(
                                        Transaction.user_id==current_user.id).group_by(
                                        Transaction.ticker).having(
                                        db.func.sum(Transaction.qty)>0).all()
    shares = []
    total_value = current_user.balance/100
    for stock in current_stocks:
        latest_price = int(get_quote(stock[0])['latestPrice']*100)
        total_value += (latest_price*stock[2])/100
        shares.append((stock[0],stock[1],stock[2],latest_price))

    return render_template('index.html', title='Portfolio', shares=shares, total_value=total_value)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid E-Mail/Password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        #Adding New User to db
        newUser = User(email=form.email.data)
        newUser.set_password(form.password.data)
        newUser.balance = 1000000
        db.session.add(newUser)
        db.session.commit()

        flash('Account created! Login to continue.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


    return "rached register by GET"

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/quote', methods=['GET','POST'])
@login_required
def quote():
    form = QuoteForm()
    if form.validate_on_submit():
        price = get_quote(form.ticker.data)['latestPrice']
        if not price:
            flash('Invalid Ticker. Please try again.')
            return redirect(url_for('quote'))
        return render_template('quote.html',ticker=form.ticker.data.upper(), price=price, title='Quote')
    return render_template('quote.html', form=form, title='Quote')

@app.route('/buy', methods=['GET','POST'])
@login_required
def buy():
    form = BuyForm()
    if form.validate_on_submit():
        ticker = form.ticker.data
        qty = form.qty.data
        quote = get_quote(ticker)

        if not quote:
            flash('Invalid Ticker')
            return redirect(url_for('buy'))

        if not current_user.buy_stock(quote,qty):
            flash('Insufficient Funds')
            return redirect(url_for('buy'))
        
        flash('Bought!')
        return redirect(url_for('index'))
    
    return render_template('buy.html', form=form, title='Buy')

@app.route('/sell', methods=['GET','POST'])
@login_required
def sell():
    stock_list = db.session.query(Transaction.ticker,Transaction.name).filter(
                                    Transaction.user_id==current_user.id).group_by(Transaction.ticker).having(
                                    db.func.sum(Transaction.qty) > 0).all()
    form = SellForm()
    form.ticker.choices = stock_list
    if form.validate_on_submit():
        ticker = form.ticker.data
        qty = form.qty.data
        quote = get_quote(ticker)
        if not current_user.sell_stock(quote,qty):
            flash("Try selling lower.")
            return redirect(url_for('sell'))
        flash('Sold.')
        return redirect(url_for('index'))
    
    
    return render_template('sell.html',form=form, title='Sell')

@app.route('/history')
@login_required
def history():
    transactions = current_user.transactions.order_by(Transaction.timestamp.desc()).all()
    return render_template('history.html', transactions=transactions, title='History')
    