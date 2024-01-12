from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from .database import get_colors, get_vehicle_types, get_manufacturers, get_fuel_types, get_vehicle_count, get_vehicles, get_vehicle, get_vehicle_inventory_clerk, get_current_part_status, update_part_status_db, get_customer_data, record_sale
from .database import get_db_connection, get_db_vendors, get_sellers, vin_exists, vendor_exists, get_max_order_number, get_vehicle_count_pending, get_vehicle_manager, is_vehicle_sellable
from .auth import is_manager, is_inventory_clerk, is_salesperson, get_loggedin_user
import re
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/', methods = ['GET'])
def home():
    if is_manager():
        sold_filter = ['sold','unsold','all']
        return render_template('base_search.html', 
                            privileged_user = 'True',
                            colors = get_colors(),
                            vehicle_types = get_vehicle_types(),
                            manufacturers = get_manufacturers(),
                            fuel_types = get_fuel_types(),
                            available_vehicles = get_vehicle_count(),
                            pending_vehicles = get_vehicle_count_pending(),
                            sold_filter = sold_filter)
    
    elif is_inventory_clerk():
        return render_template('base_search.html', 
                            privileged_user = 'True',
                            colors = get_colors(),
                            vehicle_types = get_vehicle_types(),
                            manufacturers = get_manufacturers(),
                            fuel_types = get_fuel_types(),
                            available_vehicles = get_vehicle_count(),
                            pending_vehicles = get_vehicle_count_pending())
    
    elif is_salesperson():
        return render_template('base_search.html', 
                            privileged_user = 'True',
                            colors = get_colors(),
                            vehicle_types = get_vehicle_types(),
                            manufacturers = get_manufacturers(),
                            fuel_types = get_fuel_types(),
                            available_vehicles = get_vehicle_count())
    
    else:
        return render_template('base_search.html', 
                            colors = get_colors(),
                            vehicle_types = get_vehicle_types(),
                            manufacturers = get_manufacturers(),
                            fuel_types = get_fuel_types(),
                            available_vehicles=get_vehicle_count())

def build_where_clause(params):
    conditions = []
    if params.get('VehicleType'):
        var = params.get('VehicleType')
        conditions.append(f"v.Vehicle_Type = '{var}'")

    if params.get('FuelType'):
        var = params.get('FuelType')
        conditions.append(f"v.Fuel_Type = '{var}'")

    if params.get('Manufacturer'):
        var = params.get('Manufacturer')
        conditions.append(f"v.Manufacturer = '{var}'")

    if params.get('ModelYear'):
        var = params.get('ModelYear')
        conditions.append(f"v.Model_Year = {var}")

    if params.get('Color'):
        var = params.get('Color')
        conditions.append(f"vc.Color_Name = '{var}'")

    if params.get('Vin'):
        var = params.get('Vin')
        conditions.append(f"v.Vin = '{var}'")

    if params.get('Keyword'):
        var = params.get('Keyword').lower()
        numbers = [int(match) for match in re.findall(r'\d+', var)]
        model_years_str = ",".join(map(str, numbers))
        if numbers:
            conditions.append(f'''(LOWER(v.Description) LIKE '%{var}%' OR
                           LOWER(v.Model_Name) LIKE '%{var}%' OR 
                           LOWER(v.Manufacturer) LIKE '%{var}%' OR 
                           v.Model_Year IN ({model_years_str}))''')
        else:
            conditions.append(f'''(LOWER(v.Description) LIKE '%{var}%' OR
                           LOWER(v.Model_Name) LIKE '%{var}%' OR 
                           LOWER(v.Manufacturer) LIKE '%{var}%')
                           ''')

    if conditions:
        return "WHERE " + " AND ".join(conditions)
    else:
        return "WHERE 1=1"

@main.route('/', methods = ['POST'])
def vehicle_search(): 
    data = request.form
    status = data.get('SoldStatus')
    # owners
    if is_inventory_clerk() and is_manager() and is_salesperson():
        search_results = get_vehicles(build_where_clause(data), status, True)
    elif is_inventory_clerk():
        search_results = get_vehicles(build_where_clause(data), 'all', True)
    elif is_manager():
        search_results = get_vehicles(build_where_clause(data), status, True)
    else: # public user & salesperson
        search_results = get_vehicles(build_where_clause(data), 'unsold', False)
    
    if search_results:
        return render_template('search_results.html',
                            search_results = search_results)
    else:
        return render_template('no_results.html')

@main.route('/vehicle_detail/<vin>', methods = ['GET'])
def vehicle_detail(vin):
    # owner
    if is_manager():
        details, part_dict, status = get_vehicle_manager(vin)

        vin = details['vin']
        vehicle_type = details['vehicle_type']
        fuel_type = details['fuel_type']
        model_year = details['model_year']
        manufacturer = details['manufacturer']
        model_name = details['model_name']
        mileage = details['mileage']
        colors = details['colors']
        sales_price = details['sales_price']
        description = details['description']
        original_purchase_price = details['original_purchase_price']
        total_parts_cost = details['total_parts_cost']

        # Part order
        if len(part_dict) <= 1 and part_dict[0]['part_number'] is None:
            part_dict = None

        # Seller Info
        seller_email = details['seller_email']
        seller_phone = details['seller_phone']
        seller_address = details['seller_address']
        seller_name = details['seller_name']

        # Inventory Clerk
        inventory_clerk_name = details['inventory_clerk_name']
        purchase_date = details['purchase_date']
        is_sales_person_role = is_salesperson()
        is_inventory_clerk_role = is_inventory_clerk()
        sellable = is_vehicle_sellable(vin)

        if 'buyer_email' in details:
            # Buyer Info
            buyer_email = details['buyer_email']
            buyer_phone = details['buyer_phone']
            buyer_address = details['buyer_address']
            buyer_name = details['buyer_name']
            
            # Salesperson
            sales_date = details['sales_date']
            salesperson_name = details['salesperson_name']

            return render_template('vehicle_detail.html', 
                                vin = vin,
                                vehicle_type = vehicle_type,
                                fuel_type = fuel_type, 
                                model_year = model_year, 
                                manufacturer = manufacturer, 
                                model_name = model_name, 
                                mileage = mileage,
                                colors = colors, 
                                sales_price = sales_price,
                                description = description,
                                original_purchase_price =original_purchase_price,
                                total_parts_cost = total_parts_cost,
                                part_dict = part_dict,
                                seller_email = seller_email,
                                seller_phone = seller_phone,
                                seller_address = seller_address,
                                seller_name = seller_name,
                                # Inventory Clerk
                                inventory_clerk_name = inventory_clerk_name,
                                purchase_date = purchase_date,
                                # Buyer Info
                                buyer_email = buyer_email,
                                buyer_phone = buyer_phone,
                                buyer_address = buyer_address,
                                buyer_name = buyer_name,
                                # Salesperson
                                sales_date = sales_date,
                                salesperson_name = salesperson_name,
                                is_sales_person_role = is_sales_person_role if status == 'unsold' else None,
                                is_inventory_clerk_role = is_inventory_clerk_role,
                                sellable = sellable,
                                status = status)
        else:
            return render_template('vehicle_detail.html', 
                                vin = vin,
                                vehicle_type = vehicle_type,
                                fuel_type = fuel_type, 
                                model_year = model_year, 
                                manufacturer = manufacturer, 
                                model_name = model_name, 
                                mileage = mileage,
                                colors = colors, 
                                sales_price = sales_price,
                                description = description,
                                original_purchase_price =original_purchase_price,
                                total_parts_cost = total_parts_cost,
                                part_dict = part_dict,
                                seller_email = seller_email,
                                seller_phone = seller_phone,
                                seller_address = seller_address,
                                seller_name = seller_name,
                                # Inventory Clerk
                                inventory_clerk_name = inventory_clerk_name,
                                purchase_date = purchase_date,
                                is_sales_person_role = is_sales_person_role if status == 'unsold' else None,
                                is_inventory_clerk_role = is_inventory_clerk_role,
                                sellable = sellable,
                                status = status)
    
    elif is_inventory_clerk():
        details, part_dict, status = get_vehicle_inventory_clerk(vin)

        vin = details['vin']
        vehicle_type = details['vehicle_type']
        fuel_type = details['fuel_type']
        model_year = details['model_year']
        manufacturer = details['manufacturer']
        model_name = details['model_name']
        mileage = details['mileage']
        colors = details['colors']
        sales_price = details['sales_price']
        description = details['description']
        original_purchase_price = details['original_purchase_price']
        total_parts_cost = details['total_parts_cost']

        # Part order
        if len(part_dict) <= 1 and part_dict[0]['part_number'] is None:
            part_dict = None
        return render_template('vehicle_detail.html', 
                                vin = vin,
                                vehicle_type = vehicle_type,
                                fuel_type = fuel_type, 
                                model_year = model_year, 
                                manufacturer = manufacturer, 
                                model_name = model_name, 
                                mileage = mileage,
                                colors = colors, 
                                sales_price = sales_price,
                                description = description,
                                original_purchase_price = original_purchase_price,
                                total_parts_cost = total_parts_cost,
                                part_dict = part_dict,
                                is_inventory_clerk_role = True,
                                status = status)
        
    # elif is_salesperson(): # same as public user in terms of vehicle detail page except with sell car button
    else:
        details = get_vehicle(vin)

        vin = details['vin']
        vehicle_type = details['vehicle_type']
        fuel_type = details['fuel_type']
        model_year = details['model_year']
        manufacturer = details['manufacturer']
        model_name = details['model_name']
        mileage = details['mileage']
        colors = details['colors']
        sales_price = details['sales_price']
        description = details['description']
        is_sales_person_role = is_salesperson()
        sellable = False
        if is_sales_person_role:
            sellable = is_vehicle_sellable(vin)

        return render_template('vehicle_detail.html', 
                                vin = vin,
                                vehicle_type = vehicle_type,
                                fuel_type = fuel_type, 
                                model_year = model_year, 
                                manufacturer = manufacturer, 
                                model_name = model_name, 
                                mileage = mileage,
                                colors = colors, 
                                sales_price = sales_price,
                                description = description,
                                is_sales_person_role = is_sales_person_role,
                                sellable = sellable,
                                is_inventory_clerk_role = False)


#usage example /part-status-update?part-number=XYZ123&purchase-order-number=VIN000000000000017-01
@main.route('/part-status-update', methods = ['GET'])
def part_status_update():
    part_number = request.args.get('part-number')
    po_number = request.args.get('purchase-order-number')
    current_status = get_current_part_status(part_number, po_number)

    return render_template('part_status_update.html', part_number = part_number, po_number = po_number, current_status = current_status)

@main.route('/update-part-status', methods = ['POST'])
def update_part_status():
    status = request.form['part_status']
    part_number = request.form['part_number']
    po_number = request.form['po_number']
    update_part_status_db(part_number, po_number, status)
    vin = po_number.split('-')

    return render_template('update_part_status.html', part_number = part_number, po_number = po_number, vin = vin[0])

#usage example /sales-order-form?vin=VIN000000000000011
@main.route('/sales-order-form', methods = ['GET'])
def sales_order_form():
    session['original_page'] = 'sales_order_form'
    vin = request.args.get('vin')

    return render_template('sales_order_form.html', vin = vin)

@main.route('/get-sales-order-customer-data', methods = ['GET'])
def get_sales_order_customer_data():
    customer_exist = True
    identifier = request.args.get('identifier')
    
    customer_data = get_customer_data(identifier)
    
    if customer_data == None:
        customer_exist = False

    return jsonify({ 'customer_exist': customer_exist, 'customer_data': customer_data })

@main.route('/record-sales', methods = ['POST'])
def record_sales():
    date = request.form['datepicker']
    vin = request.form['vin']
    logged_in_user = get_loggedin_user()
    buyer = request.form['customer_id']
    record_sale(date, logged_in_user, vin, buyer)

    return render_template('record_sale_confirm.html')

@main.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        # Get common customer data from the form
        email_address = request.form['email_address']
        phone_number = request.form['phone_number']
        postal_code = request.form['postal_code']
        state = request.form['stateDropdown']
        city = request.form['city']
        street = request.form['street']

        # Check if any required field is empty
        if not email_address or not phone_number or not postal_code or not state or not city or not street:
            return "Failed to add customer. Please fill in all required fields."

        conn = get_db_connection()
        cursor = conn.cursor()

        sql_insert_customer = """
            INSERT INTO public.customer (email_address, phone_number, postal_code, state, city, street)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING customer_id;
        """
        try:
            cursor.execute(sql_insert_customer, (email_address, phone_number, postal_code, state, city, street))
            result = cursor.fetchone()
            if result:
                customer_id = result['customer_id']  
            else:
                raise Exception("No customer_id returned after insertion.")
        except Exception as e:
            print(f"Error inserting customer: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            return f"Failed to add customer. Error: {e}"

        # Check if the customer_id is not NULL
        if customer_id is not None:
            # Check if the customer is an individual or a business
            customer_type = request.form.get('customer_type')
            if customer_type == 'individual':
                driver_license = request.form['driver_license']
                first_name = request.form['first_name']
                last_name = request.form['last_name']

                # Insert data into the individual table
                sql_insert_individual = """
                    INSERT INTO public.individual (driver_license, customer_id, first_name, last_name)
                    VALUES (%s, %s, %s, %s);
                """

                cursor.execute(sql_insert_individual, (driver_license, customer_id, first_name, last_name))

            elif customer_type == 'business':
                tax_id = request.form['tax_id']
                business_name = request.form['business_name']
                contact_name = request.form['contact_name']
                contact_title = request.form['contact_title']

                # Insert data into the business table
                sql_insert_business = """
                    INSERT INTO public.business (tax_id, customer_id, business_name, contact_name, contact_title)
                    VALUES (%s, %s, %s, %s, %s);
                """

                cursor.execute(sql_insert_business, (tax_id, customer_id, business_name, contact_name, contact_title))

            # Commit changes to the database
            conn.commit()
            original_page = request.form.get('original_page', '/')

            # Define a mapping between original_page values and corresponding routes
            page_mapping = {
                'add_vehicle': 'main.add_vehicle',
                'sales_order_form': 'main.sales_order_form',
                # Add more mappings as needed
            }

            # Use the mapping to get the route and redirect
            target_route = page_mapping.get(original_page, 'main.index')

            # Redirect to the original page
            return redirect(url_for(target_route))
            
    return render_template('add_customer.html')
    
# Route for adding a vendor
@main.route('/add_vendor', methods=['GET', 'POST'])
def add_vendor():
    if request.method == 'GET':
        vendor = request.args.get('vendor')
        vendor_name = request.args.get('name', default='', type=str)
        return render_template('add_vendor.html', vendor=vendor, vendor_name=vendor_name)
        
    elif request.method == 'POST':
        name = request.form['vendor_name']
        # Collect vendor details from the form
        phone_number = request.form['phone_number']
        postal_code = request.form['postal_code']
        state = request.form['stateDropdown']
        city = request.form['city']
        street = request.form['street']
        
        if vendor_exists(name):
            return redirect(url_for('main.add_part_order'))
        else:
            # Insert a new vendor
            conn = get_db_connection()
            cursor = conn.cursor()
            sql_insert_vendor = """
            INSERT INTO public.vendor (name, phone_number, postal_code, state, city, street) 
            VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql_insert_vendor, (name, phone_number, postal_code, state, city, street))
            conn.commit()
            return redirect(url_for('main.add_part_order',vendor_name=name))
    return render_template('add_customer.html')


# Route to fetch vendors dynamically
@main.route('/get_vendors', methods=['GET'])
def get_vendors():
    vendor_name_filter = request.args.get('vendor_name_filter', default=None, type=str)
    return jsonify(get_db_vendors())

# Generate a purchase order number
@main.route('/generate_purchase_order', methods=['GET', 'POST'])
def generate_purchase_order(vin):
    max_order_number = get_max_order_number(vin)
    if max_order_number is not None:
        new_order_number = f"{vin}-{max_order_number + 1:02d}"
    else:
        new_order_number = f"{vin}-01"
    # conn.close()
    return new_order_number

# Route for adding a part order
@main.route('/add_part_order', methods=['GET', 'POST'])
def add_part_order():
    if request.method == 'GET':
        return render_template('add_part_order.html', vendors=get_db_vendors())
    elif request.method == 'POST':
        # Collect part order details from the form
        vin = request.form['vin']
        vendor = request.form['vendor']   
        if not vin_exists(vin):
            return "VIN does not exist in the Vehicle database."
   
        if vendor_exists(vendor) is None:
            # If the vendor is not found, redirect to the "Add Vendor" form
            return redirect(url_for('main.add_vendor', vendor=vendor)) 
        # Generate a new purchase order number
        part_order_number = generate_purchase_order(vin)
        if part_order_number is None:
            return "Error: Purchase Order Number is NULL"

        conn = get_db_connection()  
        cursor = conn.cursor()
        cursor.execute("INSERT INTO purchase_order (purchase_order_number, vendor, vin) VALUES (%s, %s, %s) RETURNING purchase_order_number;", (part_order_number, vendor, vin))
        new_purchase_order = cursor.fetchone()
        
        part_count = int(request.form['part_count'])
        for i in range(1,part_count+1):
            if ('part_status' + str(i)) in request.form:
                part_status = request.form['part_status' + str(i)]
                part_description = request.form['part_description' + str(i)]
                part_number = request.form['part_number' + str(i)]
                part_cost = request.form['part_cost' + str(i)]
                quantity = request.form['quantity' + str(i)] 

                # Insert into public.part table
                cursor.execute("INSERT INTO part (part_number, purchase_order_number, description, cost, status, quantity) VALUES (%s, %s, %s, %s, %s, %s);", (part_number, new_purchase_order['purchase_order_number'], part_description, part_cost, part_status, quantity))

        conn.commit()
        conn.close()
        # Redirect to confirmation page
        return redirect(url_for('main.confirmation', new_purchase_order=part_order_number, vendor=vendor))

# Route for displaying confirmation
@main.route('/confirmation')
def confirmation():
    new_purchase_order = request.args.get('new_purchase_order')  # Retrieve the purchase order details
    vin = new_purchase_order.split('-') # Retrieve VIN from purchase order
    vendor = request.args.get('vendor')  # Retrieve the vendor details
    return render_template('confirmation.html', part_order_number=new_purchase_order, vendor=vendor, vin=vin[0])

@main.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    session['original_page'] = 'add_vehicle'

    if request.method == 'GET':
        vehicle_types = get_vehicle_types()  # Fetch vehicle types from the database
        manufacturers = get_manufacturers()  # Fetch manufacturers from the database
        colors = get_colors()  # Fetch colors from the database    
        return render_template('add_vehicle.html', vehicle_types=vehicle_types, 
                               manufacturers=manufacturers, 
                               colors=colors
                               )

    elif request.method == 'POST':
        try:
            # print("Form Data:", request.form)
            seller_id = request.form['seller'] # get customer id from drivers license or tax id
           # seller = dict(get_customer_data(seller_id))['customer_id']
            seller_data = get_customer_data(seller_id)

            if seller_data is None:
                # Redirect to the add_customer route if seller_id doesn't exist
                return redirect(url_for('main.add_customer'))

            else:        
                conn = get_db_connection()
                cursor = conn.cursor()
                vin = request.form['vin']
                vehicle_type = request.form['vehicle_type']  
                manufacturer = request.form['manufacturer']  
                model_name = request.form['model_name']
                model_year = request.form['model_year']
                fuel_type = request.form['fuel_type']  
                colors_selected = request.form.getlist('color') 
                mileage = request.form['mileage']
                description = request.form['description']
                purchase_price = request.form['purchase_price']  
                purchase_date = request.form['purchase_date']  
                condition = request.form['condition']  
                clerk_id = get_loggedin_user()
                seller = dict(seller_data)['customer_id']
                if vin_exists(vin):
                    return "Vehicle already exists. Please go back and try again."
                    
                else:
                    # Insert a new vehicle
                    sql_insert_vehicle = """
                            INSERT INTO public.vehicle 
                            (vin, vehicle_type, manufacturer, model_name, model_year, 
                            fuel_type, mileage, description, purchase_price, purchase_date, 
                            condition, clerk, seller) 
                            VALUES 
                            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"""
                    cursor.execute(sql_insert_vehicle, (vin, vehicle_type, manufacturer, model_name, model_year, 
                                                        fuel_type, mileage, description, purchase_price, purchase_date, 
                                                        condition, clerk_id, seller))
                    conn.commit()

                    # Insert the colors for the vehicle
                    for color in colors_selected:
                        cursor.execute("INSERT INTO public.vehicle_color (vin, color_name) VALUES (%s, %s)", (vin, color))
                        conn.commit()
                
                    return redirect(url_for('main.vehicle_detail',vin=vin)) # take to detail page

        except Exception as e:
            
            return "Error processing request. Please check the server logs for more details.", 500

