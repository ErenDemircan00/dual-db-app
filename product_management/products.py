from flask import Flask, request, render_template, redirect, url_for
from mongo_client import products_collection  # bağlantıyı buradan alıyoruz

app = Flask(__name__)

@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        
        product = {"name": name, "price": price, "description": description}
        products_collection.insert_one(product)
        return redirect(url_for('list_products'))
    
    return render_template('add_product.html')

@app.route('/products', methods=['GET'])
def list_products():
    products = products_collection.find()
    return render_template('product_list.html', products=products)
