import os
from .database import get_part_stats, get_monthly_sales, get_sales_detail, get_average_time_inventory, get_price_per_condition, get_seller_history, get_vehicle_types
from flask import Flask, render_template, redirect, url_for, request, Blueprint
from .auth import is_manager
from collections import OrderedDict

rep = Blueprint('rep', __name__)

@rep.route('/reports/')
def reports():
    if is_manager():
        return render_template('reports.html')
    else:
        return redirect(url_for('main.home'))

@rep.route('/reports/part_stats/')
def part_stats():
    if is_manager():
        parts = get_part_stats()
        return render_template('part_stats.html', parts=parts)
    else:
        return redirect(url_for('main.home'))

@rep.route('/reports/monthly_sales/')
def monthly_sales():
    if is_manager():
        sales = get_monthly_sales()
        return render_template('monthly_sales.html', sales=sales)
    else:
        return redirect(url_for('main.home'))

@rep.route('/reports/sales_detail/<year>/<month>')
def sales_detail(year=None,month=None):
    if is_manager():
        sales = get_sales_detail(year, month)
        return render_template('sales_detail.html', sales=sales)
    else:
        return redirect(url_for('main.home'))

@rep.route('/average-time-inventory')
def average_time_inventory():
    if is_manager():
        data = get_average_time_inventory()
        return render_template('average_time_inventory.html', data=data)
    else:
        return redirect(url_for('main.home'))

@rep.route('/price-per-condition')
def price_per_condition():
    if is_manager():
        vehicle_types = sorted(get_vehicle_types())
        data = get_price_per_condition()
        conditions = OrderedDict()

        for vehicle_type, condition, average_purchase_price in data:
            if condition in conditions:
                temp = conditions[condition]
                temp.append(average_purchase_price)
                conditions[condition] = temp
            else:
                conditions[condition] = [average_purchase_price]
        
        return render_template('price_per_condition.html', 
                               vehicle_types=vehicle_types, 
                               conditions=conditions)
    else:
        return redirect(url_for('main.home'))
    
@rep.route('/seller-history', methods = ['GET'])
def seller_history():
    data = get_seller_history()
    return render_template('seller_history.html', data = data)
