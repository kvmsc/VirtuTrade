from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login
from helper import get_quote

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    balance = db.Column(db.Integer)
    transactions = db.relationship('Transaction', backref='buyer', lazy='dynamic')
    
    def __repr__(self):
        return '<User {}>'.format(self.email)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash,password)
    
    def buy_stock(self, quote, qty):
        ticker = quote['symbol']
        name = quote['companyName']
        price = float(quote['latestPrice'])
        txnAmount = price * 100 * qty
        if txnAmount > self.balance:
            return False
        
        #Add it in transactions
        newTxn = Transaction(ticker=ticker,name=name, qty=qty, price=txnAmount)
        self.balance -= txnAmount
        self.transactions.append(newTxn)
        db.session.commit()

        return True

    def sell_stock(self, quote, qty):
        ticker = quote['symbol']
        name = quote['companyName']
        price = float(quote['latestPrice'])
        txnAmount = price * 100 * qty

        qtyAvailable = db.session.query(db.func.sum(Transaction.qty)).filter(
                                        Transaction.user_id==self.id).filter(
                                        Transaction.ticker==ticker).first()[0]
        
        if qty > qtyAvailable:
            return False

        newTxn = Transaction(ticker=ticker, name=name, qty=-qty, price=txnAmount)
        self.balance += txnAmount
        self.transactions.append(newTxn)
        db.session.commit()

        return True


class Transaction(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ticker = db.Column(db.String(15),index=True)
    name = db.Column(db.String(30))
    qty = db.Column(db.Integer)
    price = db.Column(db.Integer)
    timestamp = db.Column(db.Integer, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Txn {}>'.format(self.id) 
    

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
