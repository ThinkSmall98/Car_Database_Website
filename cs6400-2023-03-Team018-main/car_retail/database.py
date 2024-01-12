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

def get_colors():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT color_name FROM color;')
    colors = cur.fetchall()
    colors = [row['color_name'] for row in colors]
    cur.close()
    conn.close()
    return colors

def get_vehicle_types():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT vehicle_type_name FROM vehicle_type;')
    vehicle_types = cur.fetchall()
    vehicle_types = [row['vehicle_type_name'] for row in vehicle_types]
    cur.close()
    conn.close()
    return vehicle_types

def get_manufacturers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT manufacturer_name FROM manufacturer;')
    manufacturers = cur.fetchall()
    manufacturers = [row['manufacturer_name'] for row in manufacturers]
    cur.close()
    conn.close()
    return manufacturers

def get_fuel_types():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT e.enumlabel
                     FROM pg_enum e
                     JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = 'fuel_type'
                ''')
    fuel_types = cur.fetchall()
    fuel_types = [row['enumlabel'] for row in fuel_types]
    cur.close()
    conn.close()
    return fuel_types

def get_vehicle_count():
    conn = get_db_connection()
    cur = conn.cursor()
    query = (f'''
        SELECT COUNT(v.VIN)
                FROM VEHICLE v
            WHERE v.Sales_Date IS NULL
            AND NOT EXISTS (
                SELECT 1
                FROM PART p
                JOIN PURCHASE_ORDER po ON p.Purchase_Order_Number = po.Purchase_Order_Number
                WHERE v.VIN = po.VIN
                    AND p.Status != 'installed')
        ''')
    cur.execute(query)
    car_count = cur.fetchall()
    available_vehicles = car_count[0]['count']
    cur.close()
    conn.close()
    return available_vehicles

def get_vehicle_count_pending():
    conn = get_db_connection()
    cur = conn.cursor()
    query = (f'''
        SELECT COUNT(v.VIN)
                FROM VEHICLE v
            WHERE v.Sales_Date IS NULL
            AND EXISTS (
                SELECT 1
                FROM PART p
                JOIN PURCHASE_ORDER po ON p.Purchase_Order_Number = po.Purchase_Order_Number
                WHERE v.VIN = po.VIN
                    AND p.Status != 'installed')
        ''')
    cur.execute(query)
    car_count = cur.fetchall()
    available_vehicles = car_count[0]['count']
    cur.close()
    conn.close()
    return available_vehicles

def is_vehicle_sellable(vin):
    conn = get_db_connection()
    cur = conn.cursor()
    query = (f'''
        SELECT COUNT(v.VIN)
                FROM VEHICLE v
            WHERE v.Sales_Date IS NULL
            AND v.VIN = '{vin}'
            AND EXISTS (
                SELECT 1
                FROM PART p
                JOIN PURCHASE_ORDER po ON p.Purchase_Order_Number = po.Purchase_Order_Number
                WHERE v.VIN = po.VIN
                    AND p.Status != 'installed')
        ''')
    cur.execute(query)
    car_count = cur.fetchall()
    sellable = True if car_count[0]['count'] == 0 else False
    cur.close()
    conn.close()
    return sellable

def get_vehicles(where_clause = None, status = 'unsold', keep_pending = False):
        conn = get_db_connection()
        cur = conn.cursor()
        if status == 'unsold':
            if not keep_pending:
                query = f'''
                    SELECT v.VIN, v.Vehicle_Type, v.Fuel_Type, v.Model_Year, 
                        v.Manufacturer, v.Model_Name, v.Mileage, 
                        STRING_AGG(DISTINCT VC.Color_Name, ',') AS Colors, 
                        (v.Purchase_Price * 1.25) + (COALESCE(SUM(p.Cost*p.Quantity), CAST(0 as money)) * 1.10) AS Sales_Price,
                        v.Description
                        FROM VEHICLE v  
                        JOIN VEHICLE_COLOR vc ON v.VIN = vc.VIN 
                        LEFT JOIN PURCHASE_ORDER po ON v.VIN = po.VIN  
                        LEFT JOIN PART p ON p.Purchase_Order_Number = po.Purchase_Order_Number  
                    {where_clause}
                    AND v.Sales_Date is NULL
                    AND NOT EXISTS (
                        SELECT 1
                        FROM PART p
                        JOIN PURCHASE_ORDER po ON p.Purchase_Order_Number = po.Purchase_Order_Number
                        WHERE v.VIN = po.VIN
                            AND p.Status != 'installed'
                    )
                    GROUP BY v.VIN
                    ORDER BY v.VIN ASC;
                    '''
            else:
                query = f'''
                    SELECT v.VIN, v.Vehicle_Type, v.Fuel_Type, v.Model_Year, 
                        v.Manufacturer, v.Model_Name, v.Mileage, 
                        STRING_AGG(DISTINCT VC.Color_Name, ',') AS Colors, 
                        (v.Purchase_Price * 1.25) + (COALESCE(SUM(p.Cost*p.Quantity), CAST(0 as money)) * 1.10) AS Sales_Price,
                        v.Description
                        FROM VEHICLE v  
                        JOIN VEHICLE_COLOR vc ON v.VIN = vc.VIN 
                        LEFT JOIN PURCHASE_ORDER po ON v.VIN = po.VIN  
                        LEFT JOIN PART p ON p.Purchase_Order_Number = po.Purchase_Order_Number  
                    {where_clause}
                    AND v.Sales_Date is NULL
                    GROUP BY v.VIN
                    ORDER BY v.VIN ASC;
                    '''
        elif status == 'sold':
            query = f'''
                SELECT v.VIN, v.Vehicle_Type, v.Fuel_Type, v.Model_Year, 
                    v.Manufacturer, v.Model_Name, v.Mileage, 
                    STRING_AGG(DISTINCT VC.Color_Name, ',') AS Colors, 
                    (v.Purchase_Price * 1.25) + (COALESCE(SUM(p.Cost*p.Quantity), CAST(0 as money)) * 1.10) AS Sales_Price,
                    v.Description
                    FROM VEHICLE v  
                    JOIN VEHICLE_COLOR vc ON v.VIN = vc.VIN 
                    LEFT JOIN PURCHASE_ORDER po ON v.VIN = po.VIN  
                    LEFT JOIN PART p ON p.Purchase_Order_Number = po.Purchase_Order_Number  
                {where_clause}
                AND v.Sales_Date IS NOT NULL
                GROUP BY v.VIN
                ORDER BY v.VIN ASC;
                '''
        else: # all
            query = f'''
                SELECT v.VIN, v.Vehicle_Type, v.Fuel_Type, v.Model_Year, 
                    v.Manufacturer, v.Model_Name, v.Mileage, 
                    STRING_AGG(DISTINCT VC.Color_Name, ',') AS Colors, 
                    (v.Purchase_Price * 1.25) + (COALESCE(SUM(p.Cost*p.Quantity), CAST(0 as money)) * 1.10) AS Sales_Price,
                    v.Description
                    FROM VEHICLE v  
                    JOIN VEHICLE_COLOR vc ON v.VIN = vc.VIN 
                    LEFT JOIN PURCHASE_ORDER po ON v.VIN = po.VIN  
                    LEFT JOIN PART p ON p.Purchase_Order_Number = po.Purchase_Order_Number  
                {where_clause}
                GROUP BY v.VIN
                ORDER BY v.VIN ASC;
                '''
        cur.execute(query)
        results = cur.fetchall()
        cur.close()
        conn.close()
        search_results = [dict(row) for row in results]
        return search_results

def get_vehicle(vin=None):
    conn = get_db_connection()
    cur = conn.cursor()
    query = f'''
                SELECT v.VIN, v.Vehicle_Type, v.Fuel_Type, v.Model_Year, 
                    v.Manufacturer, v.Model_Name, v.Mileage, 
                    STRING_AGG(DISTINCT VC.Color_Name, ',') AS Colors, 
                    (v.Purchase_Price * 1.25) + (COALESCE(SUM(p.Cost*p.Quantity), CAST(0 as money)) * 1.10) AS Sales_Price,
                    v.Description
                    FROM VEHICLE v  
                    JOIN VEHICLE_COLOR vc ON v.VIN = vc.VIN 
                    LEFT JOIN PURCHASE_ORDER po ON v.VIN = po.VIN  
                    LEFT JOIN PART p ON p.Purchase_Order_Number = po.Purchase_Order_Number  
                WHERE v.VIN = '{vin}'
                GROUP BY v.VIN;
        '''
    cur.execute(query)
    output = cur.fetchall()
    details  = dict(output[0])
    cur.close()
    conn.close()
    return details
    
def get_vehicle_inventory_clerk(vin=None):
    conn = get_db_connection()
    cur = conn.cursor()
    query = f''' 
                WITH PartCosts AS ( 
                    SELECT V.VIN, SUM(P.Cost*P.Quantity) AS Total_Parts_Cost 
                    FROM VEHICLE AS V 
                    JOIN PURCHASE_ORDER AS PO ON PO.VIN = V.VIN 
                    JOIN PART AS P ON P.Purchase_Order_Number = PO.Purchase_Order_Number  
                    GROUP BY V.VIN 
                ) 
                SELECT V.VIN, V.vehicle_type, V.Model_Year, V.Manufacturer, V.Model_Name, v.Description,
                            V.Fuel_Type, STRING_AGG(DISTINCT VC.Color_Name, ',') AS Colors,  V.Mileage,  
                            (V.Purchase_Price * 1.25) + (COALESCE(SUM(p.Cost*p.Quantity), CAST(0 as money)) * 1.10) AS Sales_Price, 
                            V.Purchase_Price AS Original_Purchase_Price,  
                            COALESCE(PC.Total_Parts_Cost, CAST(0 As money)) AS Total_Parts_Cost
                FROM VEHICLE AS V 
                JOIN VEHICLE_COLOR AS VC ON V.VIN = VC.VIN 
                LEFT JOIN PartCosts AS PC ON V.VIN = PC.VIN 
                LEFT JOIN PURCHASE_ORDER AS PO ON V.VIN = PO.VIN 
                LEFT JOIN PART AS P ON PO.Purchase_Order_Number = P.Purchase_Order_Number 
                WHERE v.VIN = '{vin}'
                GROUP BY V.VIN, PC.Total_Parts_Cost; 
                '''
    query2 = f'''
                SELECT P.Part_Number, P.Description AS Part_Description, PO.Vendor, P.Cost AS Part_Cost, 
                        PO.Purchase_Order_Number AS Part_Purchase_Order, P.Status AS Part_Status, P.Quantity 
                FROM VEHICLE AS V
                LEFT JOIN PURCHASE_ORDER AS PO ON V.VIN = PO.VIN 
                LEFT JOIN PART AS P ON PO.Purchase_Order_Number = P.Purchase_Order_Number 
                WHERE v.VIN = '{vin}'
                ORDER BY PO.Purchase_Order_Number, P.Part_Number;
            '''
    cur.execute(query)
    output = cur.fetchall()
    details  = dict(output[0])

    cur.execute(query2)
    output = cur.fetchall()
    
    parts_details  = [dict(dictionary) for dictionary in output]

    check_query = f''' SELECT Sales_Date FROM Vehicle AS V WHERE v.VIN = '{vin}';'''
    cur.execute(check_query)
    output = cur.fetchall()
    sales_date  = dict(output[0])['sales_date']
    status = 'sold' if sales_date else 'unsold'

    cur.close()
    conn.close()
    return details, parts_details, status

def get_vehicle_manager(vin=None):
    conn = get_db_connection()
    cur = conn.cursor()

    check_query = f''' SELECT Sales_Date FROM Vehicle AS V WHERE v.VIN = '{vin}';'''
    cur.execute(check_query)
    output = cur.fetchall()
    sales_date  = dict(output[0])['sales_date']
    status = 'sold' if sales_date else 'unsold'
    if status == 'sold':
        query = f''' 
            WITH PartCosts AS ( 
                SELECT V.VIN, SUM(P.Cost*P.Quantity) AS Total_Parts_Cost 
                FROM VEHICLE AS V 
                JOIN PURCHASE_ORDER AS PO ON PO.VIN = V.VIN 
                JOIN PART AS P ON P.Purchase_Order_Number = PO.Purchase_Order_Number  
                GROUP BY V.VIN 
            ),
            CombinedCustomers AS (
                SELECT
                    C.Customer_ID,
                    C.Email_Address,
                    C.Phone_Number,
                    CONCAT(C.Street, ' ', C.City, ', ', C.State, ' ', C.Postal_Code) AS Address,
                    CONCAT(I.First_Name, ' ', I.Last_Name) AS Name
                FROM
                    CUSTOMER C
                JOIN
                    INDIVIDUAL I ON C.Customer_ID = I.Customer_ID

                UNION

                SELECT
                    C.Customer_ID,
                    C.Email_Address,
                    C.Phone_Number,
                    CONCAT(C.Street, ' ', C.City, ' ', C.State, ' ', C.Postal_Code) AS Address,
                    CONCAT(B.Contact_Title, ' ', B.Contact_Name, ' working at ', B.Business_Name) AS Name
                FROM
                    CUSTOMER C
                JOIN
                    BUSINESS B ON C.Customer_ID = B.Customer_ID
            )
            SELECT V.VIN, V.vehicle_type, V.Model_Year, V.Manufacturer, V.Model_Name, v.Description,
                V.Fuel_Type, STRING_AGG(DISTINCT VC.Color_Name, ',') AS Colors, V.Mileage,  
                (V.Purchase_Price * 1.25) + (COALESCE(SUM(p.Cost*p.Quantity), CAST(0 as money)) * 1.10) AS Sales_Price, 
                V.Purchase_Price AS Original_Purchase_Price, V.Purchase_Date,
                COALESCE(PC.Total_Parts_Cost, CAST(0 As money)) AS Total_Parts_Cost,
                -- Info about seller
                V.Seller AS Seller_ID, S.Email_Address AS Seller_Email, S.Phone_Number AS Seller_Phone, 
                S.Address AS Seller_Address, S.Name AS Seller_Name,
                -- Inventory Clerk
                CONCAT(C1.First_Name, ' ', C1.Last_Name) AS Inventory_Clerk_Name,
                -- Buyer
                V.Buyer AS Buyer_ID, B.Email_Address AS Buyer_Email, B.Phone_Number AS Buyer_Phone, 
                B.Address AS Buyer_Address, B.Name AS Buyer_Name,
                -- Salesperson
                V.Sales_Date, CONCAT(S1.First_Name, ' ', S1.Last_Name) AS Salesperson_Name

            FROM VEHICLE AS V 
            JOIN VEHICLE_COLOR AS VC ON V.VIN = VC.VIN 
            LEFT JOIN PartCosts AS PC ON V.VIN = PC.VIN 
            LEFT JOIN PURCHASE_ORDER AS PO ON V.VIN = PO.VIN 
            LEFT JOIN PART AS P ON PO.Purchase_Order_Number = P.Purchase_Order_Number
            LEFT JOIN CombinedCustomers AS S ON V.Seller = S.Customer_ID
            LEFT JOIN CombinedCustomers AS B ON V.Buyer = B.Customer_ID
            LEFT JOIN BuzzCar_User AS C1 ON V.Clerk = C1.username
            LEFT JOIN BuzzCar_User AS S1 ON V.Salesperson = S1.username 
            WHERE v.VIN = '{vin}'
            GROUP BY V.VIN, PC.Total_Parts_Cost, S.Email_Address, S.Phone_Number, S.Address, S.Name,
                        C1.First_Name, C1.Last_Name,
                        B.Email_Address, B.Phone_Number, 
                        B.Address, B.Name, S1.First_Name, S1.Last_Name; 
            '''
    else:
        query = f''' 
            WITH PartCosts AS ( 
                SELECT V.VIN, SUM(P.Cost*P.Quantity) AS Total_Parts_Cost 
                FROM VEHICLE AS V 
                JOIN PURCHASE_ORDER AS PO ON PO.VIN = V.VIN 
                JOIN PART AS P ON P.Purchase_Order_Number = PO.Purchase_Order_Number  
                GROUP BY V.VIN 
            ),
            CombinedCustomers AS (
                SELECT
                    C.Customer_ID,
                    C.Email_Address,
                    C.Phone_Number,
                    CONCAT(C.Street, ' ', C.City, ', ', C.State, ' ', C.Postal_Code) AS Address,
                    CONCAT(I.First_Name, ' ', I.Last_Name) AS Name
                FROM
                    CUSTOMER C
                JOIN
                    INDIVIDUAL I ON C.Customer_ID = I.Customer_ID

                UNION

                SELECT
                    C.Customer_ID,
                    C.Email_Address,
                    C.Phone_Number,
                    CONCAT(C.Street, ' ', C.City, ' ', C.State, ' ', C.Postal_Code) AS Address,
                    CONCAT(B.Contact_Title, ' ', B.Contact_Name, ' working at ', B.Business_Name) AS Name
                FROM
                    CUSTOMER C
                JOIN
                    BUSINESS B ON C.Customer_ID = B.Customer_ID
            )
            SELECT V.VIN, V.vehicle_type, V.Model_Year, V.Manufacturer, V.Model_Name, v.Description,
                V.Fuel_Type, STRING_AGG(DISTINCT VC.Color_Name, ',') AS Colors, V.Mileage,  
                (V.Purchase_Price * 1.25) + (COALESCE(SUM(p.Cost*p.Quantity), CAST(0 as money)) * 1.10) AS Sales_Price, 
                V.Purchase_Price AS Original_Purchase_Price, V.Purchase_Date,
                COALESCE(PC.Total_Parts_Cost, CAST(0 As money)) AS Total_Parts_Cost,
                -- Info about seller, inventory clerk
                V.Seller AS Seller_ID, S.Email_Address AS Seller_Email, S.Phone_Number AS Seller_Phone, 
                S.Address AS Seller_Address, S.Name AS Seller_Name, CONCAT(C1.First_Name, ' ', C1.Last_Name) AS Inventory_Clerk_Name
            FROM VEHICLE AS V 
            JOIN VEHICLE_COLOR AS VC ON V.VIN = VC.VIN  
            LEFT JOIN PartCosts AS PC ON V.VIN = PC.VIN 
            LEFT JOIN PURCHASE_ORDER AS PO ON V.VIN = PO.VIN 
            LEFT JOIN PART AS P ON PO.Purchase_Order_Number = P.Purchase_Order_Number
            LEFT JOIN CombinedCustomers AS S ON V.Seller = S.Customer_ID
            LEFT JOIN BuzzCar_User AS C1 ON V.Clerk = C1.username
            WHERE v.VIN = '{vin}'
            GROUP BY V.VIN, PC.Total_Parts_Cost, S.Email_Address, S.Phone_Number, S.Address, S.Name,
                        C1.First_Name, C1.Last_Name;
            '''
    query2 = f'''
            SELECT P.Part_Number, P.Description AS Part_Description, PO.Vendor, P.Cost AS Part_Cost, 
                    PO.Purchase_Order_Number AS Part_Purchase_Order, P.Status AS Part_Status, P.Quantity
            FROM VEHICLE AS V
            LEFT JOIN PURCHASE_ORDER AS PO ON V.VIN = PO.VIN 
            LEFT JOIN PART AS P ON PO.Purchase_Order_Number = P.Purchase_Order_Number 
            WHERE v.VIN = '{vin}'
            ORDER BY PO.Purchase_Order_Number, P.Part_Number;
            '''
    cur.execute(query)
    output = cur.fetchall()
    details  = dict(output[0])
    cur.execute(query2)
    output = cur.fetchall()
    parts_details  = [dict(dictionary) for dictionary in output]
    cur.close()
    conn.close()
    return details, parts_details, status

def check_login(username=None,password=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT UserName FROM BuzzCar_User WHERE Username = '" + username + "' AND Password = '" + password + "';")
    username = cur.fetchone()
    cur.close()
    conn.close()
    return username

def get_roles(username=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT Role_Desc FROM User_Role WHERE Username = '" + username + "';")
    roles = [r['role_desc'] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return roles

def get_part_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT v.name, SUM(p.quantity) AS number_of_parts, SUM(p.quantity*p.cost) AS total_cost ' +
                'FROM Part p ' +
                'JOIN Purchase_Order po ON p.purchase_order_number = po.purchase_order_number ' +
                'JOIN Vendor v ON po.vendor = v.name ' +
                'GROUP BY v.name ' +
                'ORDER BY v.name;')
    parts = cur.fetchall()
    cur.close()
    conn.close()
    return parts

def get_monthly_sales():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'''
                WITH Vehicle_Parts AS (
                        SELECT v.vin, v.sales_date, v.Purchase_Price, 
                                SUM(COALESCE(p.cost*p.quantity,CAST(0 AS Money))) AS part_costs
                            FROM Vehicle v  
                            LEFT JOIN Purchase_Order po ON v.vin = po.vin 
                            LEFT JOIN Part p ON po.purchase_order_number = p.purchase_order_number 
                            WHERE v.sales_date IS NOT NULL
                            GROUP BY v.vin)
                SELECT CAST(EXTRACT(year FROM vp.sales_date) AS INTEGER) AS sales_year,
                       CAST(EXTRACT(month FROM vp.sales_date) AS INTEGER) AS sales_month, 
                       COUNT(vp.sales_date) AS number_sold,
                       SUM(vp.Purchase_Price * 1.25 + vp.part_costs * 1.1) AS sales_income, 
                       SUM(vp.Purchase_Price * 0.25 + vp.part_costs * 0.1) AS net_income 
                    FROM Vehicle_Parts vp
                    GROUP BY sales_year, sales_month
                    ORDER BY sales_year DESC, sales_month DESC;''')
    sales = cur.fetchall()
    cur.close()
    conn.close()
    return sales

def get_sales_detail(year=None,month=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'''
                    WITH Vehicle_Parts AS (
                            SELECT v.vin, v.salesperson, v.Purchase_Price,
                                   SUM(COALESCE(p.cost*p.quantity,CAST(0 AS Money))) AS part_costs
                              FROM Vehicle v  
                              LEFT JOIN Purchase_Order po ON v.vin = po.vin 
                              LEFT JOIN Part p ON po.purchase_order_number = p.purchase_order_number 
                             WHERE EXTRACT(year FROM v.sales_date) = {year}
                               AND EXTRACT(month FROM v.sales_date) = {month}
                             GROUP BY v.vin)
                    SELECT COUNT(*) AS number_of_vehicles, u.first_name, u.last_name,
                           SUM(vp.Purchase_Price * 1.25 + vp.part_costs * 1.1) AS total_sales_income 
                      FROM Vehicle_Parts vp
                      JOIN BuzzCar_User u ON vp.salesperson = u.username
                     GROUP BY vp.salesperson, u.username
                     ORDER BY number_of_vehicles DESC, total_sales_income DESC;''')
    sales = cur.fetchall()
    cur.close()
    conn.close()
    return sales

def get_average_time_inventory():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT vt.vehicle_type_name AS VehicleType,
                          AVG(v.Sales_Date - v.Purchase_Date + 1) AS DaysInInventory
                     FROM Vehicle_Type vt
                     LEFT OUTER JOIN Vehicle v
                       ON v.Vehicle_Type = vt.vehicle_type_name
                      AND v.Sales_Date IS NOT NULL
                    GROUP BY vt.vehicle_type_name;
                ''')
    data = [(row['vehicletype'], row['daysininventory']) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return data

def get_price_per_condition(year=None,month=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
                    WITH Vehicle_Condition AS (
                       SELECT e.enumsortorder AS cond_id, e.enumlabel AS condition
                         FROM pg_enum e
                         JOIN pg_type t ON e.enumtypid = t.oid
                        WHERE t.typname = 'vehicle_condition'
                    )
                    SELECT vt.vehicle_type_name AS VehicleType, vc.Condition, 
                           COALESCE(AVG(CAST(v.Purchase_Price AS DECIMAL(10, 3))), 0) AS AveragePurchasePrice 
                      FROM Vehicle_Type vt 
                      NATURAL JOIN Vehicle_Condition vc 
                      LEFT OUTER JOIN Vehicle v
                        ON v.Vehicle_Type = vt.vehicle_type_name 
                       AND CAST(v.condition AS VARCHAR) = vc.condition 
                     GROUP BY vt.vehicle_type_name, vc.cond_id, vc.condition
                     ORDER BY vt.vehicle_type_name, vc.cond_id;
                ''')
    data = [(row['vehicletype'], row['condition'], float(row['averagepurchaseprice'])) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return data

def get_seller_history():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('(SELECT c.Customer_ID, ic.First_Name || \' \' || ic.Last_Name AS Name, Count(v.VIN) AS total_vehicles, ' +
'AVG(v.Purchase_Price::numeric) AS avg_purchase_price, ' + 
'COALESCE(PART_QUERY.parts_per_customer, 0) AS parts_per_customer, COALESCE(PART_QUERY.part_cost_per_customer, \'$0.00\') AS part_cost_per_customer, ' +
'COALESCE((CAST(parts_per_customer AS DECIMAL(10,2)) / CAST(Count(v.VIN) AS DECIMAL(10,2))), 0) AS avg_parts_ordered_per_vehicle, ' +
'COALESCE((part_cost_per_customer / Count(v.VIN)), \'$0.00\') AS avg_part_cost_per_vehicle ' +
'FROM Customer c ' +
'JOIN INDIVIDUAL ic ON c.Customer_ID = ic.Customer_ID ' +
'JOIN Vehicle v ON c.Customer_ID = v.Seller ' +
'LEFT JOIN ( ' +
	'SELECT c2.Customer_ID,  SUM(p2.quantity) AS parts_per_customer, SUM(p2.cost*p2.quantity) AS part_cost_per_customer ' +
	'FROM Customer c2 ' +
	'JOIN Business bc2 ON c2.Customer_ID = bc2.Customer_ID ' +
	'JOIN Vehicle v2 ON c2.Customer_ID = v2.Seller ' +
	'JOIN PURCHASE_ORDER po2 ON po2.VIN = v2.VIN ' +
	'JOIN PART p2 ON p2.purchase_order_number = po2.purchase_order_number ' +
	'GROUP BY c2.Customer_ID ' +
') AS PART_QUERY ON PART_QUERY.Customer_ID = c.Customer_ID ' +
'GROUP BY c.customer_id, ic.First_Name, ic.Last_Name, PART_QUERY.parts_per_customer, PART_QUERY.part_cost_per_customer) ' +
'UNION ' +
'(SELECT c.Customer_ID, bc.Business_Name AS Name, Count(v.VIN) AS total_vehicles, AVG(v.Purchase_Price::numeric) AS avg_purchase_price, ' +
'COALESCE(PART_QUERY.parts_per_customer, 0) AS parts_per_customer , COALESCE(PART_QUERY.part_cost_per_customer, \'$0.00\') AS part_cost_per_customer, ' +
'COALESCE((CAST(parts_per_customer AS DECIMAL(10,2)) / CAST(Count(v.VIN) AS DECIMAL(10,2))), 0) AS avg_parts_ordered_per_vehicle, ' +
'COALESCE((part_cost_per_customer / Count(v.VIN)), \'$0.00\') AS avg_part_cost_per_vehicle ' +
'FROM Customer c ' +
'JOIN Business bc ON c.Customer_ID = bc.Customer_ID ' +
'JOIN Vehicle v ON c.Customer_ID = v.Seller ' +
'LEFT JOIN ( ' +
	'SELECT c2.Customer_ID,  SUM(p2.quantity) AS parts_per_customer, SUM(p2.cost*p2.quantity) AS part_cost_per_customer ' +
	'FROM Customer c2 ' +
	'JOIN Business bc2 ON c2.Customer_ID = bc2.Customer_ID ' +
	'JOIN Vehicle v2 ON c2.Customer_ID = v2.Seller ' +
	'JOIN PURCHASE_ORDER po2 ON po2.VIN = v2.VIN ' +
	'JOIN PART p2 ON p2.purchase_order_number = po2.purchase_order_number ' +
	'GROUP BY c2.Customer_ID ' +
') AS PART_QUERY ON PART_QUERY.Customer_ID = c.Customer_ID ' +
'GROUP BY c.customer_id, bc.Business_Name, PART_QUERY.parts_per_customer, PART_QUERY.part_cost_per_customer) ' +
'ORDER BY total_vehicles desc, avg_purchase_price asc; ')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def get_current_part_status(part_number=None, po_number=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT status from PART WHERE Part_Number= %s AND Purchase_Order_Number = %s", (part_number, po_number))
    current_status = cur.fetchone()
    cur.close()
    conn.close()
    return current_status

def update_part_status_db(part_number=None, po_number=None, status=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Part SET Status = %s WHERE Part_Number= %s AND Purchase_Order_Number = %s;", (status, part_number, po_number,))
    conn.commit()
    cur.close()
    conn.close()

def get_customer_data(identifier=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT ic.customer_id, ic.First_Name || \' \' || ic.Last_Name AS Customer_Name ' +
        'FROM INDIVIDUAL ic ' +
        'WHERE ic.driver_license = %s ' +
        'UNION ' +
        'SELECT bc.customer_id, bc.Business_Name AS Customer_Name ' +
        'FROM BUSINESS bc ' +
        'WHERE bc.tax_id = %s;', (identifier, identifier))
    
    customer_data = cur.fetchone()
    cur.close()
    conn.close()
    return customer_data

def record_sale(date=None, logged_in_user=None, vin=None, customer_id=None):
    conn = get_db_connection()
    cur = conn.cursor()
    print("customerIDQQQ ", customer_id)
    cur.execute("UPDATE Vehicle SET Sales_Date = %s, Salesperson = %s, Buyer = %s WHERE VIN = %s", (date, logged_in_user, customer_id, vin))
    conn.commit()
    cur.close()
    conn.close()

def get_seller_name(customer_id=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
                  SELECT business_name As Name FROM Business WHERE customer_id = %s
                  UNION
                  SELECT first_name || ' ' || last_name As Name FROM Individual WHERE customer_id = %s
                """, (customer_id, customer_id))
    customer = cur.fetchone()
    cur.close()
    conn.close()
    return customer["name"]


def get_db_vendors(vendor_name_filter=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if vendor_name_filter:
        cur.execute("SELECT name FROM vendor WHERE name ILIKE %s;", (f"%{vendor_name_filter}%",))
    else:
        cur.execute("SELECT name FROM vendor")

    vendors = [row['name'] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return vendors
     
def get_sellers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.customer_id, c.email_address, b.business_name As name
          FROM Customer c NATURAL JOIN Business b
        UNION
        SELECT c.customer_id, c.email_address, i.first_name || ' ' || i.last_name As name
          FROM Customer c NATURAL JOIN Individual i
         ORDER BY name;
    """)
    sellers = cur.fetchall() if cur.rowcount > 0 else []
    cur.close()
    conn.close()
    return sellers

# Check if VIN exists in the database
def vin_exists(vin=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT vin FROM vehicle WHERE vin = %s", (vin,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

# Check if Vendor exists in the database
def vendor_exists(vendor=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM vendor WHERE name = %s", (vendor,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def get_max_order_number(vin=None):
    conn = get_db_connection()
    cur = conn.cursor()
    sql_query = """
                    SELECT MAX(SUBSTRING(purchase_order_number, POSITION('-' IN purchase_order_number) + 1)::INTEGER) AS max_order_number 
                    FROM PURCHASE_ORDER 
                    WHERE VIN = %s
                """
    cur.execute(sql_query, (vin,))
    max_order_number = cur.fetchone()['max_order_number']
    cur.close()
    conn.close()
    return max_order_number
