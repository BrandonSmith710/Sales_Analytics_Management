from flask import Flask, request, redirect, render_template, url_for
from .models import DB, Client, PaymentMethod, Order, InventoryItem, Location
from .functions import *
from collections import Counter
import pandas as pd
from scipy.stats import chi2_contingency
from geopy import geocoders

def create_app():

    APP = Flask(__name__)
    APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mycrm.sqlite3'
    APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    DB.init_app(APP)

    options = {
        1: 'add_client',
        2: 'update_payment',
        3: 'place_order',
        4: 'update_inventory',
        5: 'update_location',
        6: 'statistical_test',
        7: 'show_orders',
        8: 'delete_inventory',
        9: 'delete_client',
        10: 'show_inventory',
        11: 'show_client',
        12: 'refresh'
    }


    @APP.route('/', methods=['GET', 'POST'])
    def home():
        """
        List all pages in the CRM using the options dictionary.
        """

        if request.method == 'POST':
            option = request.form.get('page')
            return redirect(url_for(options[int(option)]))
        return render_template('home.html', options = options)


    @APP.route('/add_client', methods=['GET', 'POST'])
    def add_client():
        """
        Prompt administrator for necessary credentials and location(payment
        method is optional before placing first order). Add a location to
        each client's locations list as list as they are created.
        """

        if request.method == 'POST':
            if 'home' in request.form:
                return render_template('home.html', options = options)
            client_name = request.form.get('client_name')
            age = request.form.get('age')
            payment_method = request.form.get('payment_method')
            state = request.form.get('state')
            city = request.form.get('city')
            if not validate_forms(**{'int': [age, (payment_method or '1')],
                                     'str': [client_name, city, state]}):
                return render_template('add_client.html')
            client_name = client_name[:20]
            # check for location using either city + state or state + city
            exst_loc = Location.query.filter(Location.city_and_state == \
                                             city + ' ' + state).first()
            if exst_loc is None:
                exst_loc_2 = Location.query.filter(Location.city_and_state == \
                                                   state + ' ' + city).first()
                if exst_loc_2 is None:
                    new_loc = Location(city_and_state = city + ' ' + state,
                                       date = dt.datetime.now())
                    res = new_loc.update_coordinates()
                    if not res:
                        return render_template('add_client.html')
                else:
                    new_loc = exst_loc   
            else:
                new_loc = exst_loc
            if Client.query.filter(Client.name == client_name).first() is None:
                new_client = Client(name = client_name, age = int(age),
                                    state = state, city = city)
                new_client.add_location(new_loc)
                DB.session.add(new_client)
                DB.session.add(new_loc)
                if payment_method:
                    payment_method = int(payment_method)
                    if PaymentMethod.query.filter(PaymentMethod.card_num == \
                                    payment_method).first() is None:
                        card = PaymentMethod(card_num = int(payment_method))
                        new_client.add_payment(card)
                DB.session.commit()

                return render_template('home.html', options = options)
            else:
                return render_template('add_client.html',
                            msg = 'Profile already exists.')
        return render_template('add_client.html')


    @APP.route('/delete_client', methods = ['GET', 'POST'])
    def delete_client():
        """
        Prompt administrator for client information to be removed from
        database.
        """

        if request.method == 'POST':
            if 'home' in request.form:
                return render_template('home.html', options = options)
            client_name = request.form.get('client_name')
            if not validate_forms(**{'str': [client_name]}):
                return render_template('delete_client.html')
            client_2_del = Client.query.filter(Client.name == client_name) \
                .first()
            if client_2_del is not None:
                for order in client_2_del.orders:
                    for item in order.items:
                        DB.session.delete(item)
                    DB.session.delete(order)
                for location in client_2_del.locations:
                    DB.session.delete(location)
                for payment_method in client_2_del.payment_methods:
                    DB.session.delete(payment_method)
                DB.session.delete(client_2_del)
                DB.session.commit()
                return render_template('home.html', options = options)
            return render_template('delete_client.html',
                         msg = 'Profile does not exist.')
        return render_template('delete_client.html')


    @APP.route('/update_inventory', methods = ['GET', 'POST'])
    def update_inventory():
        """
        Prompt administrator for a new product name, cost, and stock, or an
        existing product name to alter the cost and/or stock of; Existing cost
        and stock attributes remain unchanged unless specified.
        """
    
        if request.method == 'POST':
            if 'home' in request.form:
                return render_template('home.html', options = options)
            product = request.form.get('product')
            cost = request.form.get('cost')
            stock = request.form.get('stock')
            if not validate_forms(**{'str': [product]}):
                return redirect(url_for('update_inventory'))
            if InventoryItem.query.filter(InventoryItem.product == product) \
                .first() is None:
                try:
                    item = InventoryItem(product = product,
                                        cost = int(cost), stock = int(stock))
                except:
                    return redirect(url_for('update_inventory'))
                DB.session.add(item)
            else:
                item = InventoryItem.query.filter(InventoryItem.product == \
                                                  product).first()
                if len(product) > 0:
                    item.product = product
                try:
                    if len(cost) > 0:
                        item.cost = int(cost)
                    if len(stock) > 0:
                        item.stock = int(stock)
                except:
                    return redirect(url_for('update_inventory'))
            DB.session.commit()
            return redirect(url_for('show_inventory'))
        return render_template('update_inventory.html')
    

    @APP.route('/delete_inventory', methods = ['GET', 'POST'])
    def delete_inventory():
        """
        Prompt administrator for inventory item information to be removed
        from database.
        """

        if request.method == 'POST':
            if 'home' in request.form:
                return render_template('home.html', options = options)
            product = request.form.get('product')
            if not validate_forms(**{'str': [product]}):
                return redirect(url_for('delete_inventory'))
            inv_2_del = InventoryItem.query.filter(InventoryItem.product == \
                                                   product).first()
            if inv_2_del is not None:
                DB.session.delete(inv_2_del)
                DB.session.commit()
                return render_template('home.html',
                                       options = options)
        return render_template('delete_inventory.html')
    

    @APP.route('/place_order', methods = ['GET', 'POST'])
    def place_order():
        """
        Page one of two-page checkout; Prompt administrator for client name
        and existing payment method where valid input will route the
        administrator to build and finalize their order.
        """

        if request.method == 'POST':
            if 'home' in request.form:
                return render_template('home.html', options = options)
            if 'show_orders' in request.form:
                return redirect('show_orders')
            client_name = request.form.get('client_name')
            payment_method = request.form.get('payment_method')
            if not validate_forms(**{'int': [payment_method],
                                     'str': [client_name]}):
                return redirect(url_for('place_order'))
            try:
                client = Client.query.filter(Client.name == client_name).first()
                payment_method = PaymentMethod.query.filter(
                    PaymentMethod.card_num == int(payment_method)).first()
                for pm in client.payment_methods:
                    if payment_method.card_num == pm.card_num:
                        break
                else:
                    return render_template('place_order.html')
            except:
                return render_template('place_order.html')
            APP.config['client_id'] = client.id
            order = create_order()
            client.add_order(order)
            DB.session.add(order)
            DB.session.commit()
            return render_template('place_order_final.html',
                            inventory = InventoryItem.query.all())
        return render_template('place_order.html')
    

    @APP.route('/place_order_final', methods = ['GET', 'POST'])
    def place_order_final():
        """
        Page two of two-page checkout; Prompt administrator for inventory item
        selection, a decision whether or not to proceed with the current order,
        and choice to add more items to the cart before checkout. Also display
        the shopping cart at the bottom of the screen.
        """
        
        if request.method == 'POST':
            product = request.form.get('product')
            quantity = request.form.get('quantity')
            finish = request.form.get('finish')
            client_id = APP.config['client_id']
            cancel = request.form.get('cancel')
            client = Client.query.get(client_id)
            if cancel == 'Cancel Order':
                cancelled_order = client.remove_order()
                for item in cancelled_order.items:
                    DB.session.delete(item)
                DB.session.delete(cancelled_order)
                DB.session.commit()
                APP.config['client_id'] = ''
                return redirect(url_for('place_order'))
            quantity = int(quantity)
            if quantity == 0:
                if finish == 'Yes':
                    if len(client.orders[-1].items) <= 0:
                        empty_order = client.remove_order()
                        DB.session.delete(empty_order)
                        DB.session.commit()
                    APP.config['client_id'] = ''
                    return render_template('home.html', options = options)
                item_count = Counter(i.product for i in client.orders[-1].items)
                shopping_cart = list(zip(item_count.keys(),
                                         item_count.values()))
                return render_template('place_order_final.html',
                                       inventory = InventoryItem.query.all(),
                                       shopping_cart = shopping_cart,
                                       cost = client.orders[-1].sum())
            else:
                inv_item = InventoryItem.query.filter(InventoryItem.product == \
                                                      product).first()
                if inv_item.stock < quantity:
                    item_count = Counter(i.product for i in client.orders[-1] \
                                         .items)
                    shopping_cart = list(zip(item_count.keys(),
                                             item_count.values()))
                    return render_template('place_order_final.html',
                        inventory = InventoryItem.query.all(),
                        shopping_cart = shopping_cart,
                        msg = f'{inv_item.stock} {inv_item.product} in stock.')
                for i in range(quantity):
                    item = create_item(inv_item = inv_item)
                    client.add_to_order(item)
                    inv_item.stock -= 1
                    DB.session.add(item)
                DB.session.commit()
                if finish == 'Yes':
                    APP.config['client_id'] = ''
                    return render_template('home.html', options = options)      
                item_count = Counter(i.product for i in client.orders[-1].items)
                shopping_cart = list(zip(item_count.keys(), item_count.values()))
                return render_template('place_order_final.html',
                                        inventory = InventoryItem.query.all(),
                                        shopping_cart = shopping_cart,
                                        cost = client.orders[-1].sum())
        return render_template('place_order_final.html',
                               inventory = InventoryItem.query.all())
    

    @APP.route('/update_location', methods = ['POST', 'GET'])
    def update_location():
        """
        Prompt administrator for client information as well as an updated
        city and state.
        """

        if request.method == 'POST':
            client_name = request.form.get('client_name')
            state = request.form.get('state')
            city = request.form.get('city')
            if not validate_forms(**{'str': [client_name, state, city]}):
                return render_template('update_location.html')
            state = state.lower()
            city = city.lower()
            client = Client.query.filter(Client.name == client_name).first()
            if client is None:
                return render_template('update_location.html')
            loc = Location.query.filter(Location.city_and_state == \
                                        city + ' ' + state).first()
            if loc is None:
                loc_2 = Location.query.filter(Location.city_and_state == \
                                              state + ' ' + city).first()
                if loc_2 is None:
                    loc = Location(city_and_state = city + ' ' + state)
                    loc.update_coordinates()
                client.add_location(loc)
                DB.session.add(loc)
            else:
                res = loc.update_coordinates()
                if res > 0:
                    client.add_location(loc)
                    DB.session.add(loc)
            DB.session.commit()
            return render_template('home.html', options = options)
        return render_template('update_location.html')
    

    @APP.route('/update_payment', methods = ['GET', 'POST'])
    def update_payment():
        """
        Prompt administrator for client information and an updated
        payment method.
        """

        if request.method == 'POST':
            if 'home' in request.form:
                return render_template('home.html', options = options)
            client_name = request.form.get('client_name')
            payment_method = request.form.get('payment_method')
            if not validate_forms(**{
                'int': [payment_method],
                'str': [client_name]
                }):
                return redirect(url_for('update_payment'))
            payment_method = int(payment_method)
            try:         
                client = Client.query.filter(Client.name == client_name) \
                                            .first()
                existing_card = PaymentMethod.query.filter(
                                PaymentMethod.card_num == payment_method) \
                                .first()
                if client is None:
                    raise Exception
                if existing_card is not None:
                    raise Exception
            except Exception:
                return render_template('update_payment.html',
                                        answer = 'Please enter a new payment \
                                             method for an existing profile.')
            new_payment = PaymentMethod(card_num = payment_method)
            try:
                former_payment = client.remove_payment()
            except IndexError:
                pass
            else:
                DB.session.delete(former_payment)
            client.add_payment(new_payment)
            DB.session.add(new_payment)
            DB.session.commit()
            return render_template('home.html', options = options)
        return render_template('update_payment.html')
    

    @APP.route('/show_inventory', methods = ['GET', 'POST'])
    def show_inventory():
        """
        Display an HTML table with all of the stocked items,
        and buttons linking to other routes.
        """
        
        inventory = InventoryItem.query.all()
        if request.method == 'POST':
            if 'home' in request.form:
                return render_template('home.html', options = options)
            if 'update' in request.form:
                return render_template('update_inventory.html')
        return render_template('show_inventory.html',inventory = inventory)


    @APP.route('/show_orders', methods = ['GET', 'POST'])
    def show_orders():
        """
        A real time business intelligence dashboard that allows the
        administrator to access sales data directly through a lengthwise
        scrollable HTMl table, as well as visualizations of data filtered by
        time and location, clickable buttons to access other routes,
        including statistical hypothesis testing for products instantiated
        by the database(can be altered to find correlations per other
        variables).
        """

        all_orders = Order.query.all()
        all_clients = Client.query.all()
        client_list = [client.name for client in all_clients]
        # count states and cities from every order, list latitudes/longitudes
        state_list = []
        city_list = []
        latitudes = []
        longitudes = []
        for client in all_clients:
            len_co = len(client.orders)
            if len_co > 0:
                locs = client.locations
                i = 0
                loc = locs[i]
                for order in client.orders:
                    while order.date.date() > loc.date.date():
                        i += 1
                    locsp = loc.city_and_state.split()
                    latitudes.append(loc.lat)
                    longitudes.append(loc.lon)
                    city_list.append(' '.join(locsp[:-1]))
                    state_list.append(locsp[-1])
                i = 0
        state_list = Counter(state_list).items()
        city_list = Counter(city_list).items()
        state_volume = [state[1] for state in state_list]
        state_list = [state[0] for state in state_list]
        city_volume = [city[1] for city in city_list]
        city_list = [city[0] for city in city_list]
        past_spendings = [client.past_spent() for client in all_clients]
        # sort clients according to number of interactions with online store
        top_5_clients = sorted(client_list, key = lambda x: client_list.count(x),
                               reverse = True)[:5]
        # sort clients again by total spendings
        top_5_clients = sorted(
            top_5_clients,
            key = lambda x: sum([order.sum() for order in \
            Client.query.filter(Client.name == x).first().orders]),
            reverse = True
        )
        order_list = [
                [
            ['client_id', order.client_id],
            ['name', order.client.name],
            ['age', order.client.age],
            ['order_id', order.id],
            ['cost', order.sum()],
            ['item_count', len(order.items)],
            ['date', order.date]
            ] for order in all_orders
        ]
        item_list = []
        # filter time data to last month and week
        dt_now = dt.datetime.now()
        month_window = lambda x: dt_now.year == x.year and dt_now.month == \
                                x.month
        week_window = lambda x: dt_now.year == x.year and (dt_now - x).days \
                                <= 7
        last_week = filter(lambda o: week_window(o.date), all_orders)
        hour_list = [order.date.hour for order in last_week]
        days_1_7 = [
            order.day_of_week() for order in filter(
            lambda o: month_window(o.date), all_orders)
        ]
        days_of_week = sorted(set(days_1_7))
        day_counts = [days_1_7.count(i) if i in days_of_week else 0 for i in \
                      range(7)]
        days_of_week = list(range(7))
        hour_counter = Counter([order.date.hour for order in all_orders]) \
                            .items()
        hour_list = [hour[0] for hour in hour_counter]
        hour_counts = [hour[1] for hour in hour_counter]
        for order in all_orders:
            item_counter = Counter([item.product for item in order.items]) \
                                .items()
            for value in item_counter:
                item_list.extend([value[0]] * int(value[1]))
        # change times to standard
        for i in range(len(hour_list)):
            tmp = hour_list[i]
            if tmp >= 13:
                tmp = str(tmp % 12) + 'pm'
            elif tmp == 0:
                tmp = '12am'
            else:
                if tmp == 12:
                    tmp = '12pm'
                else:
                    tmp = str(tmp) + 'am'
            hour_list[i] = tmp
        # count and sort ordered items from time specified
        item_counts = Counter(item_list).items()
        sorted_counts = sorted(item_counts, key = lambda x: x[1],
                               reverse = True)[:5]
        # abbreviate names of products exceeding in length
        title = ', '.join(item[0] for item in sorted_counts)
        # if len
        top_5_products = ', '.join(item[0][:11] + '.' if len(item[0]) > 10 else \
                                   item[0] for item in sorted_counts)
        top_5_quantities = [count[1] for count in sorted_counts]
        if request.method == 'POST':
            if 'hypothesis_test' in request.form:
                return redirect(url_for('statistical_test'))
            if 'show_client' in request.form:
                return redirect(url_for('show_client'))
            if 'place_order' in request.form:
                return redirect(url_for('place_order'))
            return render_template('home.html', options = options)
        return render_template('show_orders.html',
                               top_5_clients = top_5_clients,
                               top_5_products = top_5_products,
                               top_5_quantities = top_5_quantities,
                               order_list = order_list,
                               time_list = hour_list,
                               time_counts = hour_counts,
                               days_of_week = days_1_7,
                               day_counts = day_counts,
                               state_list = state_list,
                               state_volume = state_volume,
                               city_list = city_list,
                               city_volume = city_volume,
                               latitudes = latitudes,
                               longitudes = longitudes,
                               # past_spendings is unused
                               past_spendings = past_spendings)


    @APP.route('/show_client', methods = ['GET', 'POST'])
    def show_client():
        """
        Prompt administrator for client information and redirect
        with corresponding redirect arguments.
        """

        if request.method == 'POST':
            if 'home' in request.form:
                return render_template('home.html', options = options)
            if 'show_orders' in request.form:
                return redirect(url_for('show_orders'))
            client_name = request.form.get('client_name')
            if not validate_forms(**{'str': [client_name]}):
                return render_template('show_client.html')
            client = Client.query.filter(Client.name == client_name) \
                                        .first()
            if client is None:
                return render_template('show_client.html')
            return redirect(url_for('show_client_res',
                                    client_name = client_name))
        return render_template('show_client.html')


    @APP.route('/show_client_res/<client_name>', methods = ['GET', 'POST'])
    def show_client_res(client_name):
        """
        Retrieve url arguments and query database using client name,
        then display an HTML document with client order, and location
        information. Also display a plotly.js bubble map with all of
        the client's locations marked.
        """

        if request.method == 'POST':
            if 'home' in request.form:
                return render_template('home.html', options = options)
            if 'view_again' in request.form:
                return render_template('show_client.html')
            if 'show_orders' in request.form:
                return redirect(url_for('show_orders'))
        client = Client.query.filter(Client.name == client_name).first()
        client_state = client.state
        client_city = client.city
        try:
            payment_method = client.payment_methods[0]
        except:
            payment_method = 123456
        locs = client.locations
        latitudes = [location.lat for location in locs]
        longitudes = [location.lon for location in locs]
        city_volume = [latitudes.count(item) for item in latitudes]
        return render_template('show_client_res.html',
                                    client_name = client_name,
                                    client_state = client_state,
                                    client_city = client_city,
                                    payment_method = payment_method,
                                    lat = locs[-1].lat,
                                    lon = locs[-1].lon,
                                    latitudes = latitudes,
                                    longitudes = longitudes,
                                    city_volume = city_volume,
                                    action = '/show_client_res/{}' \
                                        .format(client_name))
    

    @APP.route('/statistical_test', methods = ['GET', 'POST'])
    def statistical_test():
        """
        Prompt administrator for two product names, then conduct
        a chi-squared test to determine if the two are correlated
        in sales. Route to a results page with testing information
        as url arguments.
        """

        if request.method == 'POST':
            if 'home' in request.form:
                return render_template('home.html',
                                       options = options)
            if 'show_orders' in request.form:
                return redirect(url_for('show_orders'))
            product_a = request.form.get('product_a')
            product_b = request.form.get('product_b')
            sign_lvl = request.form.get('sign_lvl')
            kwargs = {
                'str': [product_a, product_b],
                'float': [sign_lvl]
            }
            if not validate_forms(**kwargs):
                return render_template('statistical_test.html',
                                item_list = InventoryItem.query.all())
            df = chi2_df(product_a = product_a, product_b = product_b)
            g, p, dof, expctd = chi2_contingency(pd.crosstab(
                index = df['product_a'],
                columns = df['product_b']
            ))
            return redirect(url_for('statistical_test_res'),
                            p_val = p,
                            product_a = product_a,
                            product_b = product_b,
                            sign_lvl = sign_lvl)
        return render_template('statistical_test.html',
                               item_list = InventoryItem.query.all())


    @APP.route('/statistical_test_res/<p_val>/<product_a>/<product_b> \
               /<sign_lvl>', methods = ['GET', 'POST'])
    def statistical_test_res(p_val, product_a, product_b, sign_lvl):
        """
        Retrieve testing information from url, display the results
        and buttons linking back to test beginning or BI dashboard.
        """

        null_hypoth = 'There is no statistical relationship between sales \
                      of \'{}\' and \'{}\'.'.format(product_a, product_b)
        res = ['no statistical relationship',
               'a statistical relationship'][p_val <= sign_lvl]
        res += ' between sales of \'{}\' and \'{}\'.'.format(product_a,
                                                             product_b)
        if request.method == 'POST':
            if 'test' in request.form:
                return render_template('statistical_test.html',
                                       item_list = InventoryItem.query.all())
            return render_template('home.html', options = options)
        return render_template('statistical_test_res.html', res = res,
                               p_val = p_val, null_hypoth = null_hypoth,
                               sign_lvl = sign_lvl)


    @APP.route('/create_clients', methods = ['GET', 'POST'])
    def create_clients():
        """
        Create placeholder clients with locations and payment methods
        for purposes of filling out data visualizations. App database
        must hold at least one product--specifically one ordered by
        an existing client, in order to display visualizations.
        """

        cities = ['Agoura Hills  California', 'Houston  Texas',
                  'Detroit  Michigan', 'Chicago  Illinois',
                  'Des Moines  Iowa']
        for name in ['Brandon', 'John', 'Sam', 'George']:
            for i in range(1, 6):
                loc = cities[i - 1].split('  ')
                client = Client(name = name + ' ' + str(i), age = i,
                                city = loc[0], state = loc[1])
                DB.session.add(client)
                payment_method = PaymentMethod(
                    card_num = str(ord(name[0])) + (str(i) * 5))
                client.add_payment(payment_method)
                DB.session.add(payment_method)
                city = cities[i - 1]
                exst_loc = Location.query.filter(
                    Location.city_and_state == city).first()
                now = dt.datetime.now()
                if exst_loc is None:
                    new_loc = Location(city_and_state = city,
                                       date = now)
                    res = new_loc.update_coordinates()
                    if res > 0:
                        client.add_location(new_loc)
                        DB.session.add(new_loc)
                        DB.session.commit()
                else:
                    lat, lon = exst_loc.lat, exst_loc.lon
                    new_loc = Location(city_and_state = city,
                                       lat = lat, lon = lon,
                                       date = now)
                    client.add_location(new_loc)
                    DB.session.add(new_loc)
                    DB.session.commit()
        return 'True'


    @APP.route('/refresh')
    def refresh():        
        DB.drop_all()
        DB.create_all()
        return 'Data has been refreshed.'

    return APP
