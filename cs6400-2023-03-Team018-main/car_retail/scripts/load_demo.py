import pandas
import numpy
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    conn = psycopg2.connect(host='gatech-cs6400-18.postgres.database.azure.com',
                            database='car_retail',
                            port='5432',
                            user='cs400Admin@gatech-cs6400-18',
                            password='gatechcs400!',
                            cursor_factory=RealDictCursor)
    return conn


def load_users(): 
    user_data = pandas.read_csv('./demo_data/users.tsv', sep='\t')
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        for index, row in user_data.iterrows():
            sql_insert_user = """
                INSERT INTO buzzcar_user (username, password, first_name, last_name)
                VALUES (%s, %s, %s, %s);
            """
            cur.execute(sql_insert_user, (row['username'], row['password'], row['first_name'], row['last_name']))

            for role in row['roles'].split(','):
                sql_insert_user_role = """
                    INSERT INTO user_role (username, role_desc)
                    VALUES (%s, %s);
                """
                cur.execute(sql_insert_user_role, (row['username'], role))

    except Exception as e:
        print(f"Error inserting buzzcar_user: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return f"Failed to add user. Error: {e}"
    
    conn.commit()
    cur.close()
    conn.close()

def load_customers(): 
    customer_data = pandas.read_csv('./demo_data/customers.tsv', sep='\t')
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        for index, row in customer_data.iterrows():
            sql_insert_customer = """
                INSERT INTO customer (email_address, phone_number, postal_code, state, city, street)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING customer_id;

            """

            email = row['email']
            cur.execute(sql_insert_customer, (None if (type(email) == float and numpy.isnan(email)) else email,
                                               row['phone'], row['postal'], row['state'], row['city'], 
                                               row['street']))
            result = cur.fetchone()
            if result:
                customer_id = result['customer_id']  
            else:
                raise Exception("No customer_id returned after insertion.")
            
            # Check if the customer_id is not NULL
            if customer_id is not None:
                if row['customer_type'] == 'Person':
                    sql_insert_individual = """
                        INSERT INTO individual (driver_license, customer_id, first_name, last_name)
                        VALUES (%s, %s, %s, %s);
                    """

                    cur.execute(sql_insert_individual, (row["driver_lic"], customer_id, row["person_first"], 
                                                        row["person_last"]))

                elif row['customer_type'] == 'Business':
                    sql_insert_business = """
                        INSERT INTO business (tax_id, customer_id, business_name, contact_name, contact_title)
                        VALUES (%s, %s, %s, %s, %s);
                    """

                    contact_name = row['biz_contact_first'] + ' ' + row['biz_contact_last']
                    cur.execute(sql_insert_business, (row["biz_tax_id"], customer_id, row["biz_name"], 
                                                      contact_name, row["biz_contact_title"]))

    except Exception as e:
        print(f"Error inserting customer: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return f"Failed to add customer. Error: {e}"
    
    conn.commit()
    cur.close()
    conn.close()

def load_vendors():
    vendor_data = pandas.read_csv('./demo_data/vendors.tsv', sep='\t')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        for index, row in vendor_data.iterrows():
            sql_insert_vendor = """
                                    INSERT INTO vendor (name, phone_number, postal_code, state, city, street) 
                                    VALUES (%s, %s, %s, %s, %s, %s);
                                """
            cur.execute(sql_insert_vendor, (row['vendor_name'], row['phone'], row['postal_code'], 
                                            row['state'], row['city'], row['street']))

    except Exception as e:
        print(f"Error inserting vendor: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return f"Failed to add vendor. Error: {e}"
    
    conn.commit()
    cur.close()
    conn.close()

def get_customer_id(cust_value):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT customer_id FROM business WHERE tax_id = %s", (cust_value,))
    result = cur.fetchone()

    if result is None:
        cur.execute("SELECT customer_id FROM individual WHERE driver_license = %s", (cust_value,))
        result = cur.fetchone()

    cur.close()
    conn.close()
    return result['customer_id']

def load_vehicles():
    vehicle_data = pandas.read_csv('./demo_data/vehicles.tsv', sep='\t')
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        for index, row in vehicle_data.iterrows():
            sql_insert_vehicle = """
                                INSERT INTO vehicle 
                                        (vin, vehicle_type, manufacturer, model_name, model_year, fuel_type, 
                                        mileage, description, purchase_price, purchase_date, condition, seller,
                                        clerk, buyer, sales_date, salesperson) 
                                        VALUES 
                                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                            """
            seller = get_customer_id(row['purchased_from_customer'])
            sale_date = row['sale_date']
            sold_to_customer = row['sold_to_customer']
            salesperson = row['salesperson']

            if (type(sale_date) == float and numpy.isnan(sale_date)):
                sale_date = None
                sold_to_customer = None
                salesperson = None
            else:
                sold_to_customer = get_customer_id(sold_to_customer)
                
            cur.execute(sql_insert_vehicle, (row['VIN'], row['vehicle_type'], row['manufacturer_name'], 
                                             row['model_name'], row['year'], row['fuel_type'], row['odometer'], 
                                             row['description'], row['price'], row['purchase_date'], row['condition'], 
                                             seller, row['purchase_clerk'], sold_to_customer, sale_date, salesperson))

            for color in row['colors'].split(','):
                sql_insert_vehicle_color = """
                    INSERT INTO vehicle_color (vin, color_name)
                    VALUES (%s, %s);
                """
                cur.execute(sql_insert_vehicle_color, (row['VIN'], color))

    except Exception as e:
        print(f"Error inserting vehicle: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return f"Failed to add vehicle. Error: {e}"
    
    conn.commit()
    cur.close()
    conn.close()

def load_parts():
    part_data = pandas.read_csv('./demo_data/parts.tsv', sep='\t')
    conn = get_db_connection()
    cur = conn.cursor()
    previous_po = ''
    try:
        for index, row in part_data.iterrows():
            sql_insert_purchase_order = """
                INSERT INTO purchase_order (purchase_order_number, vendor, vin) 
                VALUES (%s, %s, %s);
            """

            purchase_order_number = row['VIN'] + '-' + f'{row["order_num"]:02d}'
            if (purchase_order_number != previous_po):
                previous_po = purchase_order_number
                cur.execute(sql_insert_purchase_order, (purchase_order_number, row['vendor_name'], row['VIN']))
            
            sql_insert_part = """
                INSERT INTO part (part_number, purchase_order_number, description, cost, status, quantity) 
                VALUES (%s, %s, %s, %s, %s, %s);
            """

            cur.execute(sql_insert_part, (row['part_number'], purchase_order_number, 
                                          row['description'], row['price'], row['status'], row['qty']))

    except Exception as e:
        print(f"Error inserting part: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return f"Failed to add part. Error: {e}"
    
    conn.commit()
    cur.close()
    conn.close()

load_users()
load_customers()
load_vendors()
load_vehicles()
load_parts()