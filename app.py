from flask import Flask, render_template, request, redirect, url_for, session
import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# База данных номеров и паролей (только номера и пароли)
USERS = {
    '79115002090': '2621',
    '9115002090': '2621',
    '79112223344': '1111',
    '79005553535': '2222',
    '79217778899': '3333',
    '79314445566': '4444',
}

MAX_ATTEMPTS = 20
LOCKOUT_TIME = 60

def normalize_phone(phone):
    return ''.join(filter(str.isdigit, phone))

def get_password_by_phone(phone):
    """Находит пароль по номеру телефона"""
    clean_phone = normalize_phone(phone)
    
    # Проверяем полный номер
    if clean_phone in USERS:
        return USERS[clean_phone]
    
    # Проверяем короткий номер (без 7)
    if len(clean_phone) == 10 and clean_phone in USERS:
        return USERS[clean_phone]
    
    # Проверяем окончание номера
    for stored_phone in USERS.keys():
        if clean_phone.endswith(stored_phone):
            return USERS[stored_phone]
    
    return None

@app.route('/')
def index():
    session.pop('password_attempts', None)
    session.pop('lockout_time', None)
    session.pop('phone', None)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('password_attempts', None)
    session.pop('lockout_time', None)
    
    if request.method == 'POST':
        phone_number = request.form.get('phoneNumber')
        if phone_number:
            password = get_password_by_phone(phone_number)
            if password:
                session['phone'] = phone_number
                session['correct_password'] = password  # Сохраняем правильный пароль
                return redirect(url_for('password'))
            else:
                return render_template('login.html', error="Неверный номер телефона")
    
    return render_template('login.html')

@app.route('/password', methods=['GET', 'POST'])
def password():
    if not session.get('phone'):
        return redirect(url_for('login'))
    
    if session.get('lockout_time'):
        lockout_time = session['lockout_time']
        if datetime.datetime.now().timestamp() < lockout_time:
            remaining_time = int(lockout_time - datetime.datetime.now().timestamp())
            phone = session.get('phone', 'неизвестный номер')
            attempts = session.get('password_attempts', MAX_ATTEMPTS)
            return render_template('password.html', 
                                phone=phone,
                                locked=True,
                                remaining_time=remaining_time,
                                attempts=attempts)
        else:
            session.pop('lockout_time', None)
            session.pop('password_attempts', None)

    if request.method == 'POST':
        password_input = request.form.get('pinCode')
        attempts = session.get('password_attempts', 0)
        correct_password = session.get('correct_password')
        
        if password_input == correct_password:
            session.pop('password_attempts', None)
            session.pop('lockout_time', None)
            session['entered_password'] = password_input
            return redirect(url_for('success'))
        else:
            attempts += 1
            session['password_attempts'] = attempts
            
            if attempts >= MAX_ATTEMPTS:
                lockout_time = datetime.datetime.now().timestamp() + LOCKOUT_TIME
                session['lockout_time'] = lockout_time
            
            phone = session.get('phone', 'неизвестный номер')
            remaining_attempts = MAX_ATTEMPTS - attempts
            
            return render_template('password.html', 
                                phone=phone,
                                error="Неверный пароль",
                                attempts=attempts,
                                remaining_attempts=remaining_attempts,
                                locked=(attempts >= MAX_ATTEMPTS))
    
    attempts = session.get('password_attempts', 0)
    remaining_attempts = MAX_ATTEMPTS - attempts
    phone = session.get('phone', 'неизвестный номер')
    locked = session.get('lockout_time') is not None
    
    return render_template('password.html', 
                         phone=phone,
                         attempts=attempts,
                         remaining_attempts=remaining_attempts,
                         locked=locked)

@app.route('/success')
def success():
    phone = session.get('phone', 'неизвестный номер')
    password = session.get('entered_password', 'неизвестный пароль')
    return render_template('success.html', 
                         phone=phone, 
                         password=password), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)