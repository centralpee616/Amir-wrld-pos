from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from datetime import datetime, date
def malaysia_time():
    return datetime.now()

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


import os
from werkzeug.utils import secure_filename

import os

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'sqlite:///database.db'
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Barber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    commission_rate = db.Column(db.Float)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(100))
    service = db.Column(db.String(100))
    amount = db.Column(db.Float)
    commission = db.Column(db.Float)
    date = db.Column(
    db.DateTime,
    default=malaysia_time
)
    payment_method = db.Column(db.String(20))
    receipt_no = db.Column(db.String(50))
    receipt_image = db.Column(
    db.String(255)
)


    barber_id = db.Column(
        db.Integer,
        db.ForeignKey('barber.id')
    )

    barber = db.relationship('Barber')

@app.route('/')
def home():

    sales = Sale.query.order_by(
        Sale.date.desc()
    ).all()

    today = date.today()

    today_sales = [
        s for s in sales
        if s.date.date() == today
    ]

    current_month = datetime.now().month
    current_year = datetime.now().year

    month_sales = [
        s for s in sales
        if s.date.month == current_month
        and s.date.year == current_year
    ]

    today_total = sum(
        s.amount for s in today_sales
    )

    month_total = sum(
        s.amount for s in month_sales
    )

    total_commission = sum(
        s.commission for s in sales
    )

    return render_template(
    'index.html',
    sales=sales,
    today_total=today_total,
    month_total=month_total,
    today_count=len(today_sales),
    month_count=len(month_sales),
    total_commission=total_commission
)

@app.route('/add-barber', methods=['GET','POST'])
def add_barber():

    if request.method == "POST":

        barber = Barber(
            name=request.form['name'],
            commission_rate=float(
                request.form['commission']
            )
        )

        db.session.add(barber)
        db.session.commit()

        return redirect('/')

    return render_template('add_barber.html')

@app.route('/add-sale', methods=['GET', 'POST'])
def add_sale():

    barbers = Barber.query.all()

    if request.method == "POST":

        barber = Barber.query.get(
            int(request.form['barber'])
        )

        amount = float(
            request.form['amount']
        )

        selected_date = datetime.strptime(
            request.form['transaction_date'],
            '%Y-%m-%dT%H:%M'
        )

        commission = (
            amount *
            barber.commission_rate
        ) / 100

        receipt_no = (
            "AW-" +
            datetime.now().strftime("%d%m%y-%H%M%S")
        )

        receipt_image = None

        if request.form['payment_method'] == "QR":

            file = request.files.get('receipt')

            if file and file.filename != "":

                filename = secure_filename(
                    file.filename
                )

                filename = (
                    receipt_no +
                    "_" +
                    filename
                )

                file.save(
                    os.path.join(
                        app.config['UPLOAD_FOLDER'],
                        filename
                    )
                )

                receipt_image = filename

        sale = Sale(
            service=request.form['service'],
            amount=amount,
            commission=commission,
            payment_method=request.form['payment_method'],
            receipt_no=receipt_no,
            receipt_image=receipt_image,
            date=selected_date,
            barber=barber
        )

        db.session.add(sale)
        db.session.commit()

        return redirect('/')

    return render_template(
        'add_sale.html',
        barbers=barbers,
        current_datetime=datetime.now().strftime('%Y-%m-%dT%H:%M')
    )

@app.route('/report')
def report():

    return render_template(
        'barber_report_select.html'
    )

@app.route('/report/view', methods=['POST'])
def report_view():

    selected_date = request.form['date']

    selected_date = datetime.strptime(
        selected_date,
        "%Y-%m-%d"
    ).date()

    barbers = Barber.query.all()

    report_data = []

    for barber in barbers:

        sales = Sale.query.filter_by(
            barber_id=barber.id
        ).all()

        sales = [
            s for s in sales
            if s.date.date() == selected_date
        ]

        report_data.append({
            "name": barber.name,
            "sales": sum(s.amount for s in sales),
            "commission": sum(s.commission for s in sales),
            "cuts": len(sales)
        })

    report_data.sort(
        key=lambda x: x['sales'],
        reverse=True
    )

    return render_template(
        'report.html',
        report_data=report_data,
        selected_date=selected_date
    )


@app.route('/daily-report')
def daily_report():

    return render_template(
        'daily_report_select.html'
    )

    today = date.today()

    sales = Sale.query.order_by(
        Sale.date.desc()
    ).all()

    daily_sales = [
        s for s in sales
        if s.date.date() == today
    ]

    total = sum(
        s.amount for s in daily_sales
    )

    return render_template(
        'daily_report.html',
        sales=daily_sales,
        total=total
    )
@app.route('/daily-report/view', methods=['POST'])
def daily_report_view():

    selected_date = request.form['date']

    selected_date = datetime.strptime(
        selected_date,
        "%Y-%m-%d"
    ).date()

    sales = Sale.query.order_by(
        Sale.date.desc()
    ).all()

    daily_sales = [
        s for s in sales
        if s.date.date() == selected_date
    ]

    total = sum(
        s.amount for s in daily_sales
    )

    return render_template(
        'daily_report.html',
        sales=daily_sales,
        total=total,
        selected_date=selected_date
    )

@app.route('/monthly-report')
def monthly_report():

    return render_template(
        'monthly_report_select.html'
    )

    now = datetime.now()

    sales = Sale.query.order_by(
        Sale.date.desc()
    ).all()

    monthly_sales = [
        s for s in sales
        if s.date.month == now.month
        and s.date.year == now.year
    ]

    total = sum(
        s.amount for s in monthly_sales
    )

    return render_template(
        'monthly_report.html',
        sales=monthly_sales,
        total=total
    )

@app.route('/monthly-report/view', methods=['POST'])
def monthly_report_view():

    selected_month = request.form['month']

    year = int(selected_month.split('-')[0])
    month = int(selected_month.split('-')[1])

    sales = Sale.query.order_by(
        Sale.date.desc()
    ).all()

    monthly_sales = [
        s for s in sales
        if s.date.year == year
        and s.date.month == month
    ]

    total = sum(
        s.amount for s in monthly_sales
    )

    barbers = Barber.query.all()

    barber_data = []

    for barber in barbers:

        barber_sales = [
            s for s in monthly_sales
            if s.barber_id == barber.id
        ]

        barber_data.append({
            "name": barber.name,
            "sales": sum(s.amount for s in barber_sales),
            "commission": sum(s.commission for s in barber_sales),
            "cuts": len(barber_sales)
        })

    barber_data.sort(
        key=lambda x: x['sales'],
        reverse=True
    )

    return render_template(
        'monthly_report.html',
        sales=monthly_sales,
        total=total,
        selected_month=selected_month,
        barber_data=barber_data
    )

@app.route('/edit-sale/<int:id>', methods=['GET', 'POST'])
def edit_sale(id):

    sale = Sale.query.get_or_404(id)

    barbers = Barber.query.all()

    if request.method == "POST":

        barber = Barber.query.get(
            int(request.form['barber'])
        )

        amount = float(
            request.form['amount']
        )

        selected_date = datetime.strptime(
    request.form['transaction_date'],
    '%Y-%m-%dT%H:%M'
)

        commission = (
            amount *
            barber.commission_rate
        ) / 100

        sale.service = request.form['service']
        sale.amount = amount
        sale.commission = commission
        sale.barber = barber

        db.session.commit()

        return redirect('/')

    return render_template(
        'edit_sale.html',
        sale=sale,
        barbers=barbers
    )
@app.route('/delete-sale/<int:id>')
def delete_sale(id):

    sale = Sale.query.get_or_404(id)

    db.session.delete(sale)

    db.session.commit()

    return redirect('/')

@app.route('/receipt/<int:id>')
def receipt(id):

    sale = Sale.query.get_or_404(id)

    return render_template(
        'receipt.html',
        sale=sale
    )

from flask import send_from_directory

@app.route('/uploads/<filename>')
def uploaded_file(filename):

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename
    )

@app.route('/time-test')
def time_test():

    return str(
        malaysia_time()
    )

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(
    host="0.0.0.0",
    port=5000
)

    