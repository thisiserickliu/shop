from flask import Flask, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, HiddenField, SelectField, SubmitField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, current_user


import random



app = Flask(__name__)
photos = UploadSet('photos', IMAGES)

app.config['UPLOADED_PHOTOS_DEST'] = 'images'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trendy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'efb5a2f4c16f4afd95b9574b49706709'
app.config['SECURITY_REGISTERABLE'] = False
app.config['SECURITY_PASSWORD_SALT'] = 'mysalt'
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True



configure_uploads(app, photos)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    price = db.Column(db.Integer) #NT Dollars
    stock = db.Column(db.Integer)
    description1 = db.Column(db.String(200))
    description2 = db.Column(db.String(200))
    description3 = db.Column(db.String(200))
    images = db.relationship('ProductImage', backref='product', lazy=True)

    orders = db.relationship('Order_Item', backref='product', lazy=True)

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    url = db.Column(db.String(200), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(5))
    fullname = db.Column(db.String(20))
    phone_number = db.Column(db.Integer)
    email = db.Column(db.String(50))
    address = db.Column(db.String(100))
    city = db.Column(db.String(100))
    status = db.Column(db.String(10))
    payment_type = db.Column(db.String(10))
    items = db.relationship('Order_Item', backref='order', lazy=True)

    def order_total(self):
        return db.session.query(db.func.sum(Order_Item.quantity * Product.price)).join(Product).filter(Order_Item.order_id == self.id).scalar()

    def quantity_total(self):
        return db.session.query(db.func.sum(Order_Item.quantity)).filter(Order_Item.order_id == self.id).scalar()

class Order_Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)

class AddProduct(FlaskForm):
    name = StringField('Name')
    price = IntegerField('Price')
    stock = IntegerField('Number')
    description1 = TextAreaField('Description 1')
    description2 = TextAreaField('Description 2')
    description3 = TextAreaField('Description 3')
    image1 = FileField('Image 1', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg'], 'JPEG images only!')
    ])
    image2 = FileField('Image 2', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg'], 'JPEG images only!')
    ])
    image3 = FileField('Image 3', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg'], 'JPEG images only!')
    ])


class AddToCart(FlaskForm):
    quantity = IntegerField('Quantity')
    id = HiddenField('ID')

class Checkout(FlaskForm):
    fullname = StringField('Full Name')
    phone_number = StringField('Number')
    email = StringField('Email')
    address = StringField('Address')
    city = StringField('City')
    payment_type = SelectField('Payment Type', choices=[('信用卡', '信用卡支付'), ('轉帳', '銀行郵局轉帳')])


def handle_cart():
    products = []
    grand_total = 0
    total_quantity = 0
    index = 0

    for item in session['cart']:
        product = Product.query.filter_by(id=item['id']).first()

        quantity = int(item['quantity'])
        total_quantity += item['quantity']
        total = quantity * product.price
        grand_total += total
        # Choose the first image URL as the product image
        image = product.images[0].url if product.images else None
        products.append({'id': product.id, 'name': product.name, 'price': product.price, 'image': image,
                         'quantity': quantity, 'total': total, 'index': index})
        index += 1

    return products, grand_total, total_quantity

@app.route('/')
def index():

    products = Product.query.all()

    return render_template('index.html', products=products)

@app.route('/product/<id>')
def product(id):
    product = Product.query.filter_by(id=id).first()
    form = AddToCart()

    return render_template('view-product.html', product=product, form=form)

@app.route('/quick-add/<id>')
def quick_add(id):
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append({'id': id, 'quantity': 1})
    session.modified = True

    return redirect(url_for('index'))
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'cart' not in session:
        session['cart'] = []

    form = AddToCart()

    if form.validate_on_submit():

        print(form.quantity.data)
        print(form.id.data)

        session['cart'].append({'id': form.id.data, 'quantity': form.quantity.data})
        session.modified = True


    return redirect(url_for('index'))

@app.route('/cart')
def cart():

    products, grand_total, total_quantity = handle_cart()

    return render_template('cart.html', products=products, grand_total=grand_total, total_quantity=total_quantity)

@app.route('/remove-from-cart/<index>')
def remove_from_cart(index):
    del session['cart'][int(index)]
    session.modified = True
    print(session['cart'])
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    form = Checkout()

    products, grand_total, total_quantity = handle_cart()

    if form.validate_on_submit():
        order = Order()
        form.populate_obj(order)
        order.reference = ''.join([random.choice('ABCDE') for _ in range(5)])
        order.status = "處理中"

        for product in products:
            order.item = Order_Item(quantity=product['quantity'], product_id=product['id'])
            order.items.append(order.item)

            product = Product.query.filter_by(id=product['id']).update({'stock': Product.stock - product['quantity']})

        db.session.add(order)
        db.session.commit()
        session.modified = True
        return redirect(url_for('index'))

    return render_template('checkout.html', form=form, grand_total=grand_total, total_quantity=total_quantity)

@app.route('/admin')
@login_required
def admin():
    products = Product.query.all()
    products_in_stock = Product.query.filter(Product.stock > 0).count()

    orders = Order.query.all()

    return render_template('admin/index.html', admin=True, products=products, products_in_stock=products_in_stock, orders=orders)

@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add():
    form = AddProduct()
    image_files = [form.image1.data, form.image2.data, form.image3.data]
    image_urls = []
    if form.validate_on_submit():
        for image_file in image_files:
            filename = photos.save(image_file)
            image_url = photos.url(filename)
            image_urls.append(image_url)

        new_product = Product(
            name=form.name.data,
            price=form.price.data,
            stock=form.stock.data,
            description1=form.description1.data,
            description2=form.description2.data,
            description3=form.description3.data,
        )
        db.session.add(new_product)
        db.session.commit()

        for image_url in image_urls:
            new_image = ProductImage(product_id=new_product.id, url=image_url)
            db.session.add(new_image)

        db.session.commit()

        return redirect(url_for('admin'))
    else:
        # 表单验证失败，打印错误信息
        print(form.errors)

    return render_template('admin/add-product.html', admin=True, form=form)

@app.route('/admin/order/<order_id>')
@login_required
def order(order_id):
    order = Order.query.filter_by(id=int(order_id)).first()


    return render_template('admin/view-order.html', order=order, admin=True)

@app.route('/logout')
def logout():
    # 清除会话
    session.clear()
    # 重定向到登录页面
    return redirect(url_for('admin'))

if __name__ == '__main__':
    manager.run()