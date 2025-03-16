import os
import sys
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
import hashlib
import base64

# Import BlockJournal modules
from app.utils.logger import get_logger, set_log_level
from app.blockchain.blockchain import Blockchain
from app.blockchain.storage import BlockchainStorage
from app.models.user import User
from app.models.post import Post, Comment, Reaction
from app.crypto.encryption import (
    derive_key_from_password, 
    encrypt_data, 
    decrypt_data,
    generate_key_pair,
    generate_signing_key_pair
)

# Create main application logger
logger = get_logger('blockjournal_app')
logger.info("Starting BlockJournal application")

# Initialize Flask app
app = Flask(__name__, 
            template_folder='app/templates',
            static_folder='app/static')

# Filter für die Umwandlung von Unix-Timestamps in lesbare Datumsangaben
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    """Konvertiert einen Unix-Timestamp in ein lesbares Datum."""
    if not timestamp:
        return "Unbekanntes Datum"
    try:
        return datetime.fromtimestamp(float(timestamp)).strftime('%d.%m.%Y, %H:%M:%S')
    except (ValueError, TypeError):
        return "Ungültiges Datum"

# Configure Flask app
app.config.update(
    SECRET_KEY=os.urandom(24),
    SESSION_TYPE='filesystem',
    SESSION_PERMANENT=False,
    PERMANENT_SESSION_LIFETIME=1800,  # 30 minutes
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # 10 MB max upload size
    UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'uploads'),
    DATA_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'),
    BLOCKCHAIN_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'blockchain'),
    USER_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'users'),
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif'}
)

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['BLOCKCHAIN_FOLDER'], exist_ok=True)
os.makedirs(app.config['USER_FOLDER'], exist_ok=True)

# Application state
current_user = None
current_blockchain = None
blockchain_storage = None

# Utility functions
def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(view_func):
    """Decorator to require login for views."""
    def wrapped_view(**kwargs):
        if 'user_id' not in session or 'logged_in' not in session:
            flash('Bitte melden Sie sich an, um auf diese Seite zuzugreifen.', 'error')
            return redirect(url_for('login'))
        
        # Check if user is still authenticated
        global current_user
        if not current_user:
            # Versuche, den Benutzer aus der Datenbank zu laden
            user_id = session.get('user_id')
            if user_id and os.path.exists(os.path.join(app.config['USER_FOLDER'], f"{user_id}.json")):
                # Da wir das Passwort nicht in der Session haben, können wir den Benutzer nicht vollständig laden
                # Stattdessen erstellen wir ein vereinfachtes Benutzerobjekt nur für die Anzeige
                session.pop('user_id', None)
                session.pop('logged_in', None)
                flash('Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.', 'error')
                return redirect(url_for('login'))
            else:
                # Keine Benutzeridentifikation gefunden
                session.pop('user_id', None)
                session.pop('logged_in', None)
                flash('Bitte melden Sie sich an, um auf diese Seite zuzugreifen.', 'error')
                return redirect(url_for('login'))
        
        # Sitzungsdauer überschritten?
        login_time = session.get('login_time', 0)
        current_time = time.time()
        # 2 Stunden Timeout (7200 Sekunden)
        if current_time - login_time > 7200:
            session.pop('user_id', None)
            session.pop('logged_in', None)
            session.pop('login_time', None)
            flash('Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.', 'error')
            return redirect(url_for('login'))
        
        # Session-Zeitstempel aktualisieren
        session['login_time'] = current_time
        
        return view_func(**kwargs)
    
    # Preserve the original function name
    wrapped_view.__name__ = view_func.__name__
    return wrapped_view

def init_user_blockchain():
    """Initialize the blockchain for the current user."""
    global current_user, current_blockchain, blockchain_storage
    
    if not current_user:
        logger.error("Cannot initialize blockchain: No current user")
        return False
    
    # Initialize blockchain storage
    blockchain_storage = BlockchainStorage(
        app.config['BLOCKCHAIN_FOLDER'],
        current_user.user_id
    )
    
    # Try to load existing blockchain
    blockchain = blockchain_storage.load_blockchain(
        current_user.user_id,
        current_user.encryption_key,
        current_user.settings["mining_difficulty"]
    )
    
    if blockchain:
        current_blockchain = blockchain
        logger.info(f"Loaded existing blockchain for user {current_user.username}")
    else:
        # Create new blockchain
        current_blockchain = Blockchain(
            current_user.user_id,
            current_user.encryption_key,
            current_user.settings["mining_difficulty"]
        )
        blockchain_storage.save_blockchain(current_blockchain)
        logger.info(f"Created new blockchain for user {current_user.username}")
    
    return True

# Routes
@app.route('/')
def index():
    """Home page / landing page."""
    if 'user_id' in session:
        return redirect(url_for('feed'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        user_file = os.path.join(app.config['USER_FOLDER'], f"{username}.json")
        if os.path.exists(user_file):
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username)
        
        # Generate keys
        if not user.generate_keys(password):
            flash('Failed to generate cryptographic keys.', 'error')
            return render_template('register.html')
        
        # Save user data
        if not user.save_to_file(user_file):
            flash('Failed to save user data.', 'error')
            return render_template('register.html')
        
        # Log in the user
        global current_user
        current_user = user
        session['user_id'] = user.user_id
        session['logged_in'] = True
        session['login_time'] = time.time()
        
        # Initialize blockchain
        init_user_blockchain()
        
        flash('Registration successful!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate input
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html')
        
        # Check if user exists
        user_file = os.path.join(app.config['USER_FOLDER'], f"{username}.json")
        if not os.path.exists(user_file):
            flash('Invalid username or password.', 'error')
            return render_template('login.html')
        
        # Load user data
        user = User.load_from_file(user_file, password)
        if not user:
            flash('Invalid username or password.', 'error')
            return render_template('login.html')
        
        # Log in the user
        global current_user
        current_user = user
        session['user_id'] = user.user_id
        session['logged_in'] = True
        session['login_time'] = time.time()
        
        # Initialize blockchain
        init_user_blockchain()
        
        flash('Login successful!', 'success')
        return redirect(url_for('feed'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout."""
    global current_user
    
    if current_user:
        current_user.logout()
        current_user = None
    
    session.pop('user_id', None)
    session.pop('logged_in', None)
    session.pop('login_time', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/feed')
@login_required
def feed():
    """Main feed page."""
    global current_user, current_blockchain
    
    # Get posts from blockchain
    posts = []
    if current_blockchain:
        blockchain_posts = current_blockchain.get_data_by_type("post")
        
        # Chronological order (newest first)
        blockchain_posts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Convert to Post objects
        posts = []
        for post_data in blockchain_posts:
            try:
                post = Post(
                    post_data["author"],
                    post_data["content"],
                    post_data.get("post_id"),
                    post_data.get("type", "post")
                )
                posts.append(post)
            except Exception as e:
                logger.error(f"Error processing post: {str(e)}")
    
    return render_template('feed.html', user=current_user, posts=posts)

@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new post."""
    global current_user, current_blockchain
    
    if request.method == 'POST':
        content = request.form.get('content')
        
        if not content:
            flash('Post content cannot be empty.', 'error')
            return redirect(url_for('feed'))
        
        # Create post
        post = Post(current_user.user_id, content)
        
        # Process tags (from form or extracted from content)
        tags = request.form.get('tags', '')
        if tags:
            for tag in tags.split(','):
                tag = tag.strip()
                if tag:
                    post.add_tag(tag)
        
        # Sign post with user's signing key
        post.sign(current_user.signing_key)
        
        # Add to blockchain
        if current_blockchain:
            # Add post to pending data
            current_blockchain.add_data_to_pending(
                "post",
                content,
                {
                    "post_id": post.post_id,
                    "tags": post.tags,
                    "mentions": post.mentions
                }
            )
            
            # Mine pending data
            new_block = current_blockchain.mine_pending_data()
            
            if new_block and blockchain_storage:
                # Save updated blockchain
                blockchain_storage.save_blockchain(current_blockchain)
                flash('Post created successfully!', 'success')
            else:
                flash('Failed to add post to blockchain.', 'error')
        else:
            flash('Blockchain not initialized.', 'error')
        
        return redirect(url_for('feed'))
    
    return render_template('create_post.html', user=current_user)

@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    global current_user, current_blockchain
    
    # Get user's posts
    posts = []
    if current_blockchain:
        blockchain_posts = current_blockchain.get_data_by_type("post")
        
        # Filter for current user's posts
        user_posts = [p for p in blockchain_posts if p["author"] == current_user.user_id]
        
        # Chronological order (newest first)
        user_posts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Convert to Post objects
        posts = []
        for post_data in user_posts:
            try:
                post = Post(
                    post_data["author"],
                    post_data["content"],
                    post_data.get("post_id"),
                    post_data.get("type", "post")
                )
                posts.append(post)
            except Exception as e:
                logger.error(f"Error processing post: {str(e)}")
    
    return render_template('profile.html', user=current_user, posts=posts)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page."""
    global current_user, current_blockchain
    
    if request.method == 'POST':
        # Update profile data
        profile_data = {}
        
        display_name = request.form.get('display_name')
        if display_name:
            profile_data["display_name"] = display_name
        
        bio = request.form.get('bio')
        if bio:
            profile_data["bio"] = bio
        
        # Update user settings
        new_settings = {}
        
        mining_difficulty = request.form.get('mining_difficulty')
        if mining_difficulty:
            try:
                difficulty = int(mining_difficulty)
                if difficulty > 0:
                    new_settings["mining_difficulty"] = difficulty
            except ValueError:
                pass
        
        session_timeout = request.form.get('session_timeout')
        if session_timeout:
            try:
                timeout = int(session_timeout)
                if timeout > 0:
                    new_settings["session_timeout"] = timeout
            except ValueError:
                pass
        
        theme = request.form.get('theme')
        if theme in ['light', 'dark']:
            new_settings["theme"] = theme
        
        # Update user object
        if profile_data:
            current_user.update_profile(profile_data)
        
        if new_settings:
            current_user.update_settings(new_settings)
            
            # Update blockchain difficulty if it changed
            if "mining_difficulty" in new_settings and current_blockchain:
                current_blockchain.set_difficulty(new_settings["mining_difficulty"])
        
        # Save user data
        user_file = os.path.join(app.config['USER_FOLDER'], f"{current_user.username}.json")
        current_user.save_to_file(user_file)
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', user=current_user)

@app.route('/blockchain')
@login_required
def blockchain_info():
    """Blockchain information page."""
    global current_user, current_blockchain, blockchain_storage
    
    if not current_blockchain:
        flash('Blockchain not initialized.', 'error')
        return redirect(url_for('feed'))
    
    # Get blockchain statistics
    stats = {}
    if blockchain_storage:
        stats = blockchain_storage.get_chain_stats()
    
    # Get all blocks
    blocks = []
    if current_blockchain:
        for block in current_blockchain.chain:
            blocks.append({
                "index": block.index,
                "timestamp": block.timestamp,
                "data_count": len(block.data),
                "hash": block.hash,
                "previous_hash": block.previous_hash,
                "nonce": block.nonce,
                "difficulty": block.difficulty if hasattr(block, 'difficulty') else current_blockchain.difficulty,
                "data": block.data  # Vollständige Daten für die Anzeige hinzufügen
            })
    
    # Get the last block
    last_block = current_blockchain.chain[-1] if current_blockchain.chain else None
    
    return render_template(
        'blockchain_info.html',  # Korrekter Vorlagenname
        user=current_user, 
        blocks=blocks, 
        stats=stats,
        blockchain=current_blockchain,
        last_block=last_block,
        difficulty=current_blockchain.difficulty if current_blockchain else 4
    )

@app.route('/validate_blockchain')
@login_required
def validate_blockchain():
    """Validate the blockchain integrity."""
    global current_user, current_blockchain, blockchain_storage
    
    if not current_blockchain:
        flash('Blockchain not initialized.', 'error')
        return redirect(url_for('blockchain'))
    
    # Perform validation
    is_valid = current_blockchain.validate_chain()
    
    # Update blockchain statistics
    if blockchain_storage:
        stats = blockchain_storage.get_chain_stats()
        stats['is_valid'] = is_valid
        stats['last_validation'] = time.time()
        blockchain_storage.update_stats(stats)
        
    if is_valid:
        flash('Blockchain validation successful! All blocks are valid.', 'success')
    else:
        flash('Blockchain validation failed! There are integrity issues.', 'error')
    
    return redirect(url_for('blockchain'))

@app.route('/repair_blockchain')
@login_required
def repair_blockchain():
    """Attempt to repair the blockchain."""
    global current_user, current_blockchain, blockchain_storage
    
    if not current_blockchain:
        flash('Blockchain not initialized.', 'error')
        return redirect(url_for('blockchain'))
    
    # Simple repair strategy: Remove invalid blocks from the end until we find a valid chain
    repaired = False
    while len(current_blockchain.chain) > 1:  # Keep at least the genesis block
        if current_blockchain.validate_chain():
            repaired = True
            break
        else:
            # Remove the last block
            current_blockchain.chain.pop()
    
    # Update blockchain statistics
    if blockchain_storage:
        stats = blockchain_storage.get_chain_stats()
        stats['is_valid'] = True
        stats['last_validation'] = time.time()
        blockchain_storage.update_stats(stats)
    
    if repaired:
        flash('Blockchain repair successful! Invalid blocks have been removed.', 'success')
    else:
        flash('Blockchain repair failed. You may need to reinitialize your blockchain.', 'error')
    
    return redirect(url_for('blockchain'))

@app.route('/backup', methods=['GET', 'POST'])
@login_required
def backup():
    """Backup and restore blockchain data."""
    global current_user, blockchain_storage
    
    if not blockchain_storage:
        flash('Blockchain storage not initialized.', 'error')
        return redirect(url_for('feed'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'backup':
            # Create backup
            backup_path = blockchain_storage.create_backup()
            
            if backup_path:
                flash(f'Backup created successfully at {backup_path}', 'success')
            else:
                flash('Failed to create backup.', 'error')
        
        elif action == 'restore':
            # Restore from backup
            backup_path = request.form.get('backup_path')
            
            if not backup_path:
                flash('Backup path is required.', 'error')
            elif not os.path.exists(backup_path):
                flash('Backup path does not exist.', 'error')
            else:
                if blockchain_storage.restore_from_backup(backup_path):
                    flash('Blockchain restored successfully!', 'success')
                    
                    # Reload blockchain
                    init_user_blockchain()
                else:
                    flash('Failed to restore from backup.', 'error')
        
        return redirect(url_for('backup'))
    
    # Get available backups
    backups = []
    backup_dir = os.path.join(app.config['BLOCKCHAIN_FOLDER'], 'backups')
    
    if os.path.exists(backup_dir):
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            if os.path.isdir(item_path) and item.startswith(current_user.user_id):
                backup_time = None
                size_kb = 0
                
                # Try to parse timestamp from folder name
                parts = item.split('_')
                if len(parts) > 1:
                    try:
                        timestamp = parts[-2] + '_' + parts[-1]
                        backup_time = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                    except (ValueError, IndexError):
                        pass
                
                # Calculate backup size
                try:
                    size = 0
                    for dirpath, dirnames, filenames in os.walk(item_path):
                        for filename in filenames:
                            file_path = os.path.join(dirpath, filename)
                            size += os.path.getsize(file_path)
                    size_kb = size / 1024  # Convert to KB
                except Exception as e:
                    logger.error(f"Error calculating backup size: {str(e)}")
                
                backups.append({
                    'path': item_path,
                    'name': item,
                    'timestamp': backup_time.timestamp() if backup_time else time.time(),
                    'size': round(size_kb, 2)
                })
        
        # Sort by time (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('backup.html', user=current_user, backups=backups)

# Favicon-Route
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error=e, message='Page not found'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return render_template('error.html', error=e, message='Internal server error'), 500

# Run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
