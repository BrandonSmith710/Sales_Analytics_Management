from .models import Order, Item
import datetime as dt
import pandas as pd
from collections import Counter


def create_order():
    order_date = dt.datetime.now()
    # order_date = dt.datetime(year = order_date.year, month = order_date.month, day = order_date.day + 1,
    #                          hour = order_date.hour + 1, minute = order_date.minute + 1, second = order_date.second,
    #                          microsecond = order_date.microsecond + 1)
    return Order(date = order_date)


def create_item(inv_item):
    return Item(product = inv_item.product, cost = inv_item.cost)


def validate_form(form):
    return len(form) > 0


def validate_form_int(form):
    return validate_form(form) and form.isdigit()


def validate_form_float(form):
    if validate_form(form):
        return form.count('.') == 1 and ''.join(form.split('.')).isdigit()
    return False


def validate_forms(**kwargs):
    """Validate form inputs of str, int and float types using
       keyword arguments"""

    for form in kwargs.get('str', []):
        if not validate_form(form):
            return False
    for form in kwargs.get('int', []):
        if not validate_form_int(form):
            return False
    for form in kwargs.get('float', []):
        if not validate_form_float(form):
            return False
    return True


def chi2_df(product_a, product_b):
    """
    Formulate the conditional distribution of orders for hypothesis test
    and place necessary information into a dataframe for use by the scipy
    library

    Parameters: 
        product_a - (str) a name selected from an html dropdown menu of inventory
        product_b - (str) a name selected from an html dropdown menu of inventory
    """

    all_orders = Order.query.all()
    product_a_bool = []
    product_b_bool = []
    for order in all_orders:
        a = False
        b = False
        for item in order.items:
            if item.product == product_a:
                a = True
            if item.product == product_b:
                b = True
            if a and b:
                break
        product_a_bool.append('Yes' if a else 'No')
        product_b_bool.append('Yes' if b else 'No')
    product_a_bool = [1 if x == 'Yes' else 0 for x in product_a_bool]
    product_b_bool = [1 if x == 'Yes' else 0 for x in product_b_bool]
    df = pd.DataFrame({'id': [order.id for order in all_orders],
                       'product_a': product_a_bool,
                       'product_b': product_b_bool})
    return df


def wrangle(all_clients):
    # count states and cities from every order, list latitudes/longitudes
    state_list = []
    city_list = []
    locations = {'latitudes': [], 'longitudes': []}
    for client in all_clients:
        len_co = len(client.orders)
        recent = client.locations[-1]
        locations['latitudes'].extend([recent.lat for i in range(len_co)])
        locations['longitudes'].extend([recent.lon for i in range(len_co)])
        state_list.extend([client.state for i in range(len_co)])
        city_list.extend([client.city for i in range(len_co)])
    
    locations['state_list'] = Counter(state_list).items()
    locations['city_list'] = Counter(city_list).items()
    locations['state_volume'] = [state[1] for state in state_list]
    locations['state_list'] = [state[0] for state in state_list]
    locations['city_volume'] = [city[1] for city in city_list]
    locations['city_list'] = [city[0] for city in city_list]
    locations['past_spendings'] = [client.past_spent() for client in all_clients]

    return locations
