from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime as dt
from geopy import geocoders

DB = SQLAlchemy()


class Client(DB.Model):
    id = DB.Column(DB.Integer, primary_key = True, autoincrement = True)
    name = DB.Column(DB.String(20), nullable = False)
    age = DB.Column(DB.Integer, nullable = False)
    state = DB.Column(DB.String(20), nullable = False)
    city = DB.Column(DB.String(40), nullable = False)

                                                                            
    def add_order(self, order):
        self.orders.append(order)

    def add_to_order(self, item):
        self.orders[-1].items.append(item)
    
    def remove_order(self, ):
        return self.orders.pop()
    
    def add_payment(self, pm):
        self.payment_methods.append(pm)
    
    def add_location(self, location):
        self.locations.append(location)

    def remove_payment(self):
        return self.payment_methods.pop()
    
    def past_spent(self):
        return sum(order.sum() for order in self.orders)


class PaymentMethod(DB.Model):
    id = DB.Column(DB.Integer, primary_key = True, autoincrement = True)
    client_id = DB.Column(DB.Integer, DB.ForeignKey('client.id'))
    client = DB.relationship('Client', backref=DB.backref('payment_methods'),
                             lazy = True)
    card_num = DB.Column(DB.BigInteger, nullable = False)

    def __str__(self):
        return str(self.card_num)


class Order(DB.Model):
    id = DB.Column(DB.Integer, primary_key = True, autoincrement = True)
    date = DB.Column(DB.DateTime, nullable = False)
    client_id = DB.Column(DB.Integer, DB.ForeignKey('client.id'))
    client = DB.relationship('Client', backref=DB.backref('orders'),
                             lazy = True)

    def add_item(self, item):
        self.items.append(item)
    
    def sum(self):
        return sum(item.cost for item in self.items)
    
    def day_of_week(self):
        return self.date.weekday()
    
    def __str__(self):
        return str(self.id)


class Item(DB.Model):
    id = DB.Column(DB.Integer, primary_key = True, autoincrement = True)
    order_id = DB.Column(DB.Integer, DB.ForeignKey('order.id'))
    order = DB.relationship('Order', backref = DB.backref('items'),
                            lazy = True)
    product = DB.Column(DB.String(80), nullable = False)
    cost = DB.Column(DB.BigInteger, nullable = False)

class InventoryItem(DB.Model):
    id = DB.Column(DB.Integer, primary_key = True, autoincrement = True)
    product = DB.Column(DB.String(80), nullable = False)
    cost = DB.Column(DB.BigInteger, nullable = False)
    stock = DB.Column(DB.BigInteger, nullable = False)


class Location(DB.Model):
    id = DB.Column(DB.Integer, primary_key = True, autoincrement = True)
    city_and_state = DB.Column(DB.String(80), nullable = False)
    lat = DB.Column(DB.Float, nullable = True)
    lon = DB.Column(DB.Float, nullable = True)
    date = DB.Column(DB.DateTime)
    client_id = DB.Column(DB.Integer, DB.ForeignKey('client.id'))
    client = DB.relationship('Client', backref=DB.backref('locations'),
                          lazy = True)

    def update_coordinates(self):
        """
        Parameters:
            city_and_state: str, verified city and state separated by space
        """
        
        gn = geocoders.Nominatim(user_agent = "my_app")
        try:
            location = gn.geocode(self.city_and_state).raw
        except AttributeError:
            return 0
        except Exception('Service timed out'):
            print('!!!')
        lat = location['lat']
        lon = location['lon']
        self.lat = float(lat)
        self.lon = float(lon)
        return 1

    def get_coordinates(self):
        return self.lat, self.lon
    
    def __str__(self):
        return str(self.lat, self.lon)
    



