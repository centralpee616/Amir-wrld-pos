from flask import Flask, render_template, request, redirect
from flask import send_file
import openpyxl
from io import BytesIO
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta

def malaysia_time():

    return datetime.utcnow() + timedelta(hours=8)

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


import os
from werkzeug.utils import secure_filename


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

    recent_sales = sales[:3]

    today = date.today()

    today_sales = [
        s for s in sales
        if s.date.date() == today
    ]

    now = malaysia_time()

    current_month = now.month
    current_year = now.year
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
        sales=recent_sales,
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

        barber = db.session.get(
    Barber,
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
    malaysia_time().strftime("%d%m%y-%H%M%S")
)

        receipt_image = None

        if request.form['payment_method'] == "QR":

            file = request.files.get('receipt')

            if file and file.filename != "":

                try:

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

                except Exception as e:

                    print("UPLOAD ERROR:")
                    print(e)

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

        current_datetime=(
    datetime.utcnow() +
    timedelta(hours=8)
).strftime('%Y-%m-%dT%H:%M') )

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

    sale = db.get_or_404(
    Sale,
    id
)

    barbers = Barber.query.all()

    if request.method == "POST":

        barber = db.session.get(
    Barber,
    int(request.form['barber'])
)

        amount = float(
            request.form['amount']
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

    sale = db.get_or_404(
    Sale,
    id
)

    db.session.delete(sale)

    db.session.commit()

    return redirect('/')

@app.route('/receipt/<int:id>')
def receipt(id):

    sale = db.get_or_404(
    Sale,
    id
)

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

@app.route('/transactions')
def all_transactions():

    sales = Sale.query.order_by(
        Sale.date.desc()
    ).all()

    return render_template(
        'transactions.html',
        sales=sales
    )

@app.route('/barbers')
def manage_barbers():

    barbers = Barber.query.order_by(
        Barber.name
    ).all()

    return render_template(
        'barbers.html',
        barbers=barbers
    )


@app.route('/edit-barber/<int:id>',
methods=['GET', 'POST'])
def edit_barber(id):

    barber = db.get_or_404(
    Barber,
    id
)

    if request.method == "POST":

        barber.name = request.form['name']

        barber.commission_rate = float(
            request.form['commission']
        )

        db.session.commit()

        return redirect('/barbers')

    return render_template(
        'edit_barber.html',
        barber=barber
    )


@app.route('/delete-barber/<int:id>')
def delete_barber(id):

    barber = db.get_or_404(
    Barber,
    id
)

    sales_count = Sale.query.filter_by(
        barber_id=barber.id
    ).count()

    if sales_count > 0:

        return (
            f"Cannot delete {barber.name}. "
            "This barber has sales records."
        )

    db.session.delete(barber)

    db.session.commit()

    return redirect('/barbers')

@app.route('/export-sales')
def export_sales():

    workbook = openpyxl.Workbook()

    # SALES SHEET

    sales_sheet = workbook.active

    sales_sheet.title = "Sales"

    headers = [
        "Date",
        "Receipt No",
        "Service",
        "Barber",
        "Payment Method",
        "Amount",
        "Commission",
        "Receipt Image"
    ]

    for col_num, header in enumerate(headers, 1):

        sales_sheet.cell(
            row=1,
            column=col_num
        ).value = header

        sales_sheet.cell(
    row=row_num,
    column=8
).value = (
    sale.receipt_image
    if sale.receipt_image
    else "No Image"
)

    sales = Sale.query.order_by(
        Sale.date.desc()
    ).all()

    row_num = 2

    for sale in sales:

        sales_sheet.cell(
            row=row_num,
            column=1
        ).value = sale.date.strftime(
            "%d/%m/%Y %H:%M"
        )

        sales_sheet.cell(
            row=row_num,
            column=2
        ).value = sale.receipt_no

        sales_sheet.cell(
            row=row_num,
            column=3
        ).value = sale.service

        sales_sheet.cell(
            row=row_num,
            column=4
        ).value = sale.barber.name

        sales_sheet.cell(
            row=row_num,
            column=5
        ).value = sale.payment_method

        sales_sheet.cell(
            row=row_num,
            column=6
        ).value = sale.amount

        sales_sheet.cell(
            row=row_num,
            column=7
        ).value = sale.commission

        row_num += 1

    # BARBERS SHEET

    barber_sheet = workbook.create_sheet(
        "Barbers"
    )

    barber_sheet.cell(
        1,
        1
    ).value = "Name"

    barber_sheet.cell(
        1,
        2
    ).value = "Commission %"

    barbers = Barber.query.order_by(
        Barber.name
    ).all()

    row_num = 2

    for barber in barbers:

        barber_sheet.cell(
            row_num,
            1
        ).value = barber.name

        barber_sheet.cell(
            row_num,
            2
        ).value = barber.commission_rate

        row_num += 1

    # SUMMARY SHEET

    summary_sheet = workbook.create_sheet(
        "Summary"
    )

    summary_sheet["A1"] = "Total Sales"

    summary_sheet["B1"] = sum(
        sale.amount
        for sale in sales
    )

    summary_sheet["A2"] = "Total Haircuts"

    summary_sheet["B2"] = len(
        sales
    )

    summary_sheet["A3"] = "Total Commission"

    summary_sheet["B3"] = sum(
        sale.commission
        for sale in sales
    )

    # DOWNLOAD

    output = BytesIO()

    workbook.save(
        output
    )

    output.seek(
        0
    )

    return send_file(
        output,
        download_name=
        "AMIR_WRLD_Backup.xlsx",
        as_attachment=True
    ) 


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(
    host="0.0.0.0",
    port=5000
)

    