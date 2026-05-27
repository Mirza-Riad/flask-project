from flask import Flask, render_template, request, jsonify
import mysql.connector

app = Flask(__name__)


# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",
        database="animal_analyzer"
    )


# Home route
@app.route('/')
def home():
    return render_template('index.html')


# =========================
# Animal analysis endpoint — FIXED
# Now correctly uses user-provided meat_price
# =========================
@app.route('/analyze', methods=['POST'])
def analyze_animal():
    data = request.json
    animal_type = data.get('animal_type')
    price       = float(data.get('price'))
    meat_price  = float(data.get('meat_price'))  # ✅ now actually used

    # Per-animal config
    if animal_type == 'cow':
        meat_per_kg_buy = 900     # approx market price per kg live weight
        dress_percent   = 0.58    # 58% meat yield from live weight
        height          = "4.5 feet (Approx)"
    elif animal_type == 'goat':
        meat_per_kg_buy = 1100
        dress_percent   = 0.48
        height          = "2.5 feet (Approx)"
    else:  # sheep
        meat_per_kg_buy = 1050
        dress_percent   = 0.50
        height          = "3 feet (Approx)"

    # Weight calculations
    live_weight_kg  = price / meat_per_kg_buy
    meat_yield_kg   = live_weight_kg * dress_percent

    # Mon conversion (1 মণ = 40 kg)
    live_weight_mon = live_weight_kg / 40
    meat_yield_mon  = meat_yield_kg  / 40

    # Fair price using the user-supplied meat price per kg ✅
    expected_fair_price = meat_yield_kg * meat_price

    # Market status
    if price < expected_fair_price * 0.90:
        status = "Cheap"
    elif price > expected_fair_price * 1.10:
        status = "Expensive"
    else:
        status = "Fair"

    # Equal 3-way distribution (কোরবানির নিয়ম)
    share = meat_yield_kg / 3

    return jsonify({
        "live_weight_kg":   round(live_weight_kg, 2),
        "live_weight_mon":  round(live_weight_mon, 3),
        "meat_yield_kg":    round(meat_yield_kg, 2),
        "meat_yield_mon":   round(meat_yield_mon, 3),
        "height":           height,
        "expected_fair_price": round(expected_fair_price, 2),
        "market_status":    status,
        "distribution": {
            "family":    round(share, 2),
            "relatives": round(share, 2),
            "poor":      round(share, 2)
        }
    })


# =========================
# Profit calculation endpoint — FIXED
# Stores animal_type from request, not hardcoded 'cow'
# =========================
@app.route('/calculate_profit', methods=['POST'])
def calculate_profit():
    data = request.json

    buy_price       = float(data.get('buy_price'))
    total_food_cost = float(data.get('food_cost', 0))
    sell_price      = float(data.get('sell_price'))

    total_investment = buy_price + total_food_cost
    net_profit       = sell_price - total_investment

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO farmer_records
        (animal_type, buy_price, daily_food_cost, months_kept, total_food_cost, sell_price, net_profit)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data.get('animal_type', 'unknown'),
            buy_price,
            data.get('daily_food_cost', 0.0),
            data.get('months_kept', 0),
            total_food_cost,
            sell_price,
            net_profit
        ))
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Database Error: {e}")

    return jsonify({
        "buy_price":        buy_price,
        "food_cost":        total_food_cost,
        "total_investment": total_investment,
        "sell_price":       sell_price,
        "net_profit":       net_profit
    })


if __name__ == '__main__':
    app.run(debug=True)