import os
import socket
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from database.db_connection import db, ma, mail
from routes.auth_routes import auth_bp
from routes.report_routes import report_bp
from sqlalchemy import inspect, text


load_dotenv()

def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    CORS(app)
    
    # Configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@127.0.0.1/reva_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'reva-secret-key')
    
    # Mail Configurations
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 465))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
    
    # Initialize DB, Marshmallow, and Mail
    db.init_app(app)
    ma.init_app(app)
    mail.init_app(app)
    
    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(report_bp)

    # Health Check
    @app.route('/', methods=['GET'])
    def index():
        return {"message": "REVA Modular Backend is active", "status": "online"}, 200

    @app.route('/ping', methods=['GET'])
    def ping():
        return {"status": "online", "system": "REVA Modular Engine"}, 200

    # Ensure upload folder exists
    if not os.path.exists('uploads'):
        os.makedirs('uploads')



    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Safety Add Columns for OTP
        try:
            inspector = inspect(db.engine)

            if 'users' in inspector.get_table_names():
                columns = [c['name'] for c in inspector.get_columns('users')]
                if 'otp' not in columns:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN otp VARCHAR(10);"))
                if 'otp_expiry' not in columns:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN otp_expiry DATETIME;"))
                    
                if 'location' not in columns:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN location VARCHAR(100);"))
                if 'height' not in columns:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN height VARCHAR(20);"))
                if 'weight' not in columns:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN weight VARCHAR(20);"))
                if 'blood_type' not in columns:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN blood_type VARCHAR(20);"))
                if 'allergies' not in columns:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN allergies TEXT;"))
                    
                # Health Score Updates
                inspector_hr = inspect(db.engine)
                if 'health_reports' in inspector_hr.get_table_names():
                    hr_cols = [c['name'] for c in inspector_hr.get_columns('health_reports')]
                    if 'activity_score' not in hr_cols:
                        db.session.execute(text("ALTER TABLE health_reports ADD COLUMN activity_score INTEGER;"))
                    if 'wellness_score' not in hr_cols:
                        db.session.execute(text("ALTER TABLE health_reports ADD COLUMN wellness_score INTEGER;"))
                
                inspector_fc = inspect(db.engine)
                if 'followup_comparisons' in inspector_fc.get_table_names():
                    fc_cols = [c['name'] for c in inspector_fc.get_columns('followup_comparisons')]
                    if 'activity_improvement' not in fc_cols:
                        db.session.execute(text("ALTER TABLE followup_comparisons ADD COLUMN activity_improvement FLOAT;"))
                    if 'wellness_improvement' not in fc_cols:
                        db.session.execute(text("ALTER TABLE followup_comparisons ADD COLUMN wellness_improvement FLOAT;"))
                    
                db.session.commit()
                print("✅ [DATABASE] Columns verified.")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ [DATABASE] Failed to update columns: {str(e)}")
            
        print("✅ REVA Backend Processing Engine Ready.")


    return app

if __name__ == "__main__":
    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    app = create_app()
    local_ip = get_local_ip()
    print(f"\n🚀 REVA Modular Backend starting on: http://180.235.121.253:8151")
    print(f"📡 Local fallback: http://127.0.0.1:8000")
    print("----------------------------------------------")
    app.run(debug=False, host='0.0.0.0', port=8151, threaded=True)
