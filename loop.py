import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Uses PostgreSQL if DATABASE_URL environment variable is set, otherwise falls back to SQLite for instant hackathon demoing
DATABASE_URI = os.environ.get(
    'DATABASE_URL', 
    'sqlite:///foodbridge.db'
    # Example PostgreSQL URI: 'postgresql://postgres:password@localhost:5432/foodbridge'
)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------- DATABASE MODELS -----------------
class Donation(db.Model):
    __tablename__ = 'donations'
    id = db.Column(db.Integer, primary_key=True)
    donor_name = db.Column(db.String(120), nullable=False)
    donor_type = db.Column(db.String(60), nullable=False)  # Restaurant, Hostel/College, Bakery, Event, Household
    food_items = db.Column(db.String(200), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    is_fresh = db.Column(db.Boolean, default=True)         # True -> Human NGO Feed, False -> Animal Farmer Feed
    route_category = db.Column(db.String(60), nullable=False) # 'Human Consumption' or 'Animal Feed'
    shelf_life_hours = db.Column(db.Float, nullable=False)
    location_address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(40), default='Available') # Available, Claimed, Verified
    claimed_by = db.Column(db.String(120), nullable=True)
    pickup_time = db.Column(db.String(60), nullable=True)
    qr_token = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        expires_at = self.created_at + timedelta(hours=self.shelf_life_hours)
        remaining_seconds = max(0, int((expires_at - datetime.utcnow()).total_seconds()))
        return {
            'id': self.id,
            'donor_name': self.donor_name,
            'donor_type': self.donor_type,
            'food_items': self.food_items,
            'quantity_kg': self.quantity_kg,
            'is_fresh': self.is_fresh,
            'route_category': self.route_category,
            'shelf_life_hours': self.shelf_life_hours,
            'remaining_seconds': remaining_seconds,
            'location_address': self.location_address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'status': self.status,
            'claimed_by': self.claimed_by,
            'pickup_time': self.pickup_time,
            'qr_token': self.qr_token
        }

# ----------------- SEED INITIAL DATA -----------------
def seed_database():
    if Donation.query.count() == 0:
        sample_donations = [
            Donation(
                donor_name="SVCE College Campus Canteen",
                donor_type="Hostel/College",
                food_items="Veg Biryani, Dal Tadka & 80 Chapathis",
                quantity_kg=35.0,
                is_fresh=True,
                route_category="Human Consumption",
                shelf_life_hours=4.5,
                location_address="SVCE College, Tirupati, Andhra Pradesh",
                latitude=13.6288,
                longitude=79.4192,
                status="Available",
                qr_token="FB-QR-1001"
            ),
            Donation(
                donor_name="Grand Spice Kitchen & Banquet",
                donor_type="Restaurant",
                food_items="Paneer Butter Masala, Steamed Rice & Sweet Pongal",
                quantity_kg=48.0,
                is_fresh=True,
                route_category="Human Consumption",
                shelf_life_hours=3.0,
                location_address="MG Road, Secunderabad, Telangana",
                latitude=17.4399,
                longitude=78.4983,
                status="Available",
                qr_token="FB-QR-1002"
            ),
            Donation(
                donor_name="Sunrise Artisan Bakery",
                donor_type="Bakery",
                food_items="Day-Old Bread Loaves, Croissants & Vegetable Cuttings",
                quantity_kg=22.0,
                is_fresh=False,
                route_category="Animal Feed",
                shelf_life_hours=12.0,
                location_address="Banjara Hills, Hyderabad, Telangana",
                latitude=17.4156,
                longitude=78.4347,
                status="Available",
                qr_token="FB-QR-1003"
            ),
            Donation(
                donor_name="Royal Convention Wedding Hall",
                donor_type="Events/Wedding",
                food_items="Mixed Vegetable Curry, Sambar & Pulav",
                quantity_kg=65.0,
                is_fresh=True,
                route_category="Human Consumption",
                shelf_life_hours=2.5,
                location_address="Hitech City, Hyderabad, Telangana",
                latitude=17.4435,
                longitude=78.3772,
                status="Claimed",
                claimed_by="Akshaya Trust NGO",
                pickup_time="19:30 HRS",
                qr_token="FB-QR-1004"
            ),
            Donation(
                donor_name="GreenLeaf Supermarket",
                donor_type="Restaurant",
                food_items="Bruised Fruits, Leafy Greens & Kitchen Peels",
                quantity_kg=30.0,
                is_fresh=False,
                route_category="Animal Feed",
                shelf_life_hours=8.0,
                location_address="Gachibowli, Hyderabad, Telangana",
                latitude=17.4401,
                longitude=78.3489,
                status="Verified",
                claimed_by="Nandi Goshala Sanctuary",
                pickup_time="16:15 HRS",
                qr_token="FB-QR-1005"
            )
        ]
        db.session.bulk_save_objects(sample_donations)
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_database()

# ----------------- ROUTES & REST API -----------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/donations', methods=['GET'])
def get_donations():
    donations = Donation.query.order_by(Donation.id.desc()).all()
    return jsonify([d.to_dict() for d in donations])

@app.route('/api/donations', methods=['POST'])
def create_donation():
    data = request.json
    is_fresh = bool(data.get('is_fresh', True))
    route_category = "Human Consumption" if is_fresh else "Animal Feed"
    new_id = Donation.query.count() + 1001

    donation = Donation(
        donor_name=data.get('donor_name', 'Anonymous Donor'),
        donor_type=data.get('donor_type', 'Restaurant'),
        food_items=data.get('food_items', 'Assorted Meals'),
        quantity_kg=float(data.get('quantity_kg', 10)),
        is_fresh=is_fresh,
        route_category=route_category,
        shelf_life_hours=float(data.get('shelf_life_hours', 4)),
        location_address=data.get('location_address', 'SVCE College Campus'),
        latitude=data.get('latitude', 17.4065),
        longitude=data.get('longitude', 78.4772),
        status='Available',
        qr_token=f"FB-QR-{new_id}"
    )
    db.session.add(donation)
    db.session.commit()
    return jsonify({"message": "Donation listed successfully!", "donation": donation.to_dict()}), 201

@app.route('/api/claim/<int:donation_id>', methods=['POST'])
def claim_donation(donation_id):
    data = request.json
    donation = Donation.query.get_or_404(donation_id)
    donation.status = 'Claimed'
    donation.claimed_by = data.get('claimed_by', 'Local NGO Volunteer')
    donation.pickup_time = data.get('pickup_time', datetime.now().strftime("%H:%M HRS"))
    db.session.commit()
    return jsonify({"message": "Donation claimed!", "donation": donation.to_dict()})

@app.route('/api/verify-qr', methods=['POST'])
def verify_qr():
    data = request.json
    qr_token = data.get('qr_token', '').strip().upper()
    donation = Donation.query.filter_by(qr_token=qr_token).first()
    if not donation:
        return jsonify({"success": False, "message": "Invalid QR Code Token!"}), 404
    donation.status = 'Verified'
    if not donation.claimed_by:
        donation.claimed_by = "Rapid Rescue Volunteer"
    db.session.commit()
    return jsonify({
        "success": True,
        "message": f"Verified handoff of {donation.quantity_kg} kg from {donation.donor_name}!",
        "donation": donation.to_dict()
    })

@app.route('/api/chat', methods=['POST'])
def annam_dhutha_chat():
    user_msg = request.json.get('message', '').lower()
    available = Donation.query.filter_by(status='Available').all()
    total_kg = sum(d.quantity_kg for d in Donation.query.all())

    if any(k in user_msg for k in ['nearby', 'available', 'find', 'food', 'pickup']):
        if not available:
            reply = "Namaste! I am Annam Dhutha. Right now all listed batches have been claimed! You can post a new donation on the 'Donate Food' tab."
        else:
            items = ", ".join([f"{d.food_items} ({d.quantity_kg}kg at {d.location_address})" for d in available[:3]])
            reply = f"Namaste! There are currently {len(available)} active food pickups available: {items}. Click 'Navigate' on any card to open Google Maps directions!"
    elif any(k in user_msg for k in ['animal', 'scrap', 'spoiled', 'farm', 'zero-waste', 'route']):
        reply = "FoodBridge uses Zero-Waste Dual Routing! Fresh meals go directly to NGOs and shelters for human consumption, while spoiled food or kitchen scraps are routed to local animal farmers and cattle sanctuaries."
    elif any(k in user_msg for k in ['qr', 'verify', 'code', 'safety']):
        reply = "Every listing generates a dynamic QR token (e.g., FB-QR-1001). When the volunteer arrives, scanning or entering this QR token in the 'QR Handoff' tab verifies a trusted, safe pickup!"
    elif any(k in user_msg for k in ['impact', 'co2', 'saved', 'stats', 'chart']):
        reply = f"So far, our community has tracked {total_kg:.1f} kg of food across the platform, preventing approximately {total_kg * 2.5:.1f} kg of CO2 emissions! Check the 'Analytics & PyCharts' tab for live breakdowns."
    elif any(k in user_msg for k in ['team', 'who', 'svce', 'loop']):
        reply = "FoodBridge was created by Team THE FOOD LOOP from SVCE College: Manikanta, Abhi, Harshith, and Pawan!"
    else:
        reply = "Namaste! I am Annam Dhutha (अन्नं दूत), your AI Food Rescue Messenger. Ask me about available nearby food, Google Maps navigation, Zero-Waste dual routing, QR verification, or our CO2 impact charts!"

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True, port=5000)