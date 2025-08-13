import sqlite3
import hashlib
import json
import os
import datetime
from pathlib import Path
import logging

class ModShareDatabase:
    def __init__(self, db_path="mod_share.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with all necessary tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        is_moderator BOOLEAN DEFAULT 0,
                        avatar_path TEXT,
                        bio TEXT
                    )
                ''')
                
                # Mods table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mods (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        author_id INTEGER,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        download_count INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0.0,
                        rating_count INTEGER DEFAULT 0,
                        is_public BOOLEAN DEFAULT 1,
                        is_featured BOOLEAN DEFAULT 0,
                        game_compatibility TEXT,
                        version TEXT DEFAULT '1.0',
                        tags TEXT,
                        thumbnail_path TEXT,
                        FOREIGN KEY (author_id) REFERENCES users (id)
                    )
                ''')
                
                # Comments table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        mod_id INTEGER,
                        user_id INTEGER,
                        comment TEXT NOT NULL,
                        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_approved BOOLEAN DEFAULT 1,
                        FOREIGN KEY (mod_id) REFERENCES mods (id),
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                # Downloads table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS downloads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        mod_id INTEGER,
                        user_id INTEGER,
                        download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ip_address TEXT,
                        FOREIGN KEY (mod_id) REFERENCES mods (id),
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                # Categories table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        parent_id INTEGER,
                        FOREIGN KEY (parent_id) REFERENCES categories (id)
                    )
                ''')
                
                # Mod categories relationship table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mod_categories (
                        mod_id INTEGER,
                        category_id INTEGER,
                        PRIMARY KEY (mod_id, category_id),
                        FOREIGN KEY (mod_id) REFERENCES mods (id),
                        FOREIGN KEY (category_id) REFERENCES categories (id)
                    )
                ''')
                
                # Initialize default categories
                self._init_default_categories(cursor)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    def _init_default_categories(self, cursor):
        """Initialize default mod categories"""
        default_categories = [
            ("Game Mods", "General game modifications"),
            ("Character Mods", "Character replacements and additions"),
            ("Stage Mods", "Custom stages and stage modifications"),
            ("Music Mods", "Custom music and sound modifications"),
            ("Texture Mods", "Texture and visual modifications"),
            ("Utility Mods", "Tools and utilities"),
            ("Experimental", "Experimental and beta mods")
        ]
        
        for name, description in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, description)
                VALUES (?, ?)
            ''', (name, description))
    
    def hash_password(self, password):
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, email, password):
        """Create a new user account"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                password_hash = self.hash_password(password)
                
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash)
                    VALUES (?, ?, ?)
                ''', (username, email, password_hash))
                
                user_id = cursor.lastrowid
                conn.commit()
                self.logger.info(f"User created: {username}")
                return user_id
                
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                if "username" in str(e):
                    raise ValueError("Username already exists")
                else:
                    raise ValueError("Email already exists")
            raise
        except Exception as e:
            self.logger.error(f"User creation failed: {e}")
            raise
    
    def authenticate_user(self, username_or_email, password):
        """Authenticate a user login"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                password_hash = self.hash_password(password)
                
                cursor.execute('''
                    SELECT id, username, email, is_active, is_moderator
                    FROM users
                    WHERE (username = ? OR email = ?) AND password_hash = ? AND is_active = 1
                ''', (username_or_email, username_or_email, password_hash))
                
                user = cursor.fetchone()
                if user:
                    # Update last login
                    cursor.execute('''
                        UPDATE users SET last_login = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (user[0]))
                    conn.commit()
                    
                    return {
                        'id': user[0],
                        'username': user[1],
                        'email': user[2],
                        'is_active': user[3],
                        'is_moderator': user[4]
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            raise
    
    def upload_mod(self, title, description, author_id, file_path, game_compatibility, 
                   version="1.0", tags=None, is_public=True):
        """Upload a new mod"""
        try:
            file_size = os.path.getsize(file_path)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO mods (title, description, author_id, file_path, file_size,
                                    game_compatibility, version, tags, is_public)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title, description, author_id, file_path, file_size,
                     game_compatibility, version, tags, is_public))
                
                mod_id = cursor.lastrowid
                conn.commit()
                self.logger.info(f"Mod uploaded: {title} (ID: {mod_id})")
                return mod_id
                
        except Exception as e:
            self.logger.error(f"Mod upload failed: {e}")
            raise
    
    def get_mods(self, limit=20, offset=0, category_id=None, search_query=None, 
                 sort_by="upload_date", sort_order="DESC"):
        """Get mods with filtering and sorting"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT m.id, m.title, m.description, m.upload_date, m.download_count,
                           m.rating, m.rating_count, m.version, m.game_compatibility,
                           u.username as author_name, m.thumbnail_path
                    FROM mods m
                    JOIN users u ON m.author_id = u.id
                    WHERE m.is_public = 1
                '''
                params = []
                
                if category_id:
                    query += ''' AND m.id IN (
                        SELECT mod_id FROM mod_categories WHERE category_id = ?
                    )'''
                    params.append(category_id)
                
                if search_query:
                    query += ''' AND (m.title LIKE ? OR m.description LIKE ? OR m.tags LIKE ?)'''
                    search_term = f"%{search_query}%"
                    params.extend([search_term, search_term, search_term])
                
                query += f' ORDER BY m.{sort_by} {sort_order} LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                mods = cursor.fetchall()
                
                return [{
                    'id': mod[0],
                    'title': mod[1],
                    'description': mod[2],
                    'upload_date': mod[3],
                    'download_count': mod[4],
                    'rating': mod[5],
                    'rating_count': mod[6],
                    'version': mod[7],
                    'game_compatibility': mod[8],
                    'author_name': mod[9],
                    'thumbnail_path': mod[10]
                } for mod in mods]
                
        except Exception as e:
            self.logger.error(f"Get mods failed: {e}")
            raise
    
    def get_mod_details(self, mod_id):
        """Get detailed information about a specific mod"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT m.*, u.username as author_name, u.avatar_path as author_avatar
                    FROM mods m
                    JOIN users u ON m.author_id = u.id
                    WHERE m.id = ?
                ''', (mod_id,))
                
                mod = cursor.fetchone()
                if not mod:
                    return None
                
                # Get comments
                cursor.execute('''
                    SELECT c.*, u.username
                    FROM comments c
                    JOIN users u ON c.user_id = u.id
                    WHERE c.mod_id = ? AND c.is_approved = 1
                    ORDER BY c.created_date DESC
                ''', (mod_id,))
                
                comments = cursor.fetchall()
                
                return {
                    'id': mod[0],
                    'title': mod[1],
                    'description': mod[2],
                    'author_id': mod[3],
                    'file_path': mod[4],
                    'file_size': mod[5],
                    'upload_date': mod[6],
                    'download_count': mod[7],
                    'rating': mod[8],
                    'rating_count': mod[9],
                    'is_public': mod[10],
                    'is_featured': mod[11],
                    'game_compatibility': mod[12],
                    'version': mod[13],
                    'tags': mod[14],
                    'thumbnail_path': mod[15],
                    'author_name': mod[16],
                    'author_avatar': mod[17],
                    'comments': [{
                        'id': c[0],
                        'user_id': c[2],
                        'comment': c[3],
                        'rating': c[4],
                        'created_date': c[5],
                        'username': c[7]
                    } for c in comments]
                }
                
        except Exception as e:
            self.logger.error(f"Get mod details failed: {e}")
            raise
    
    def add_comment(self, mod_id, user_id, comment, rating=None):
        """Add a comment and rating to a mod"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO comments (mod_id, user_id, comment, rating)
                    VALUES (?, ?, ?, ?)
                ''', (mod_id, user_id, comment, rating))
                
                # Update mod rating if rating provided
                if rating:
                    cursor.execute('''
                        UPDATE mods 
                        SET rating = (
                            SELECT AVG(rating) 
                            FROM comments 
                            WHERE mod_id = ? AND rating IS NOT NULL
                        ),
                        rating_count = (
                            SELECT COUNT(*) 
                            FROM comments 
                            WHERE mod_id = ? AND rating IS NOT NULL
                        )
                        WHERE id = ?
                    ''', (mod_id, mod_id, mod_id))
                
                conn.commit()
                self.logger.info(f"Comment added to mod {mod_id}")
                
        except Exception as e:
            self.logger.error(f"Add comment failed: {e}")
            raise
    
    def record_download(self, mod_id, user_id=None, ip_address=None):
        """Record a mod download"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO downloads (mod_id, user_id, ip_address)
                    VALUES (?, ?, ?)
                ''', (mod_id, user_id, ip_address))
                
                cursor.execute('''
                    UPDATE mods SET download_count = download_count + 1
                    WHERE id = ?
                ''', (mod_id,))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Record download failed: {e}")
            raise
    
    def get_categories(self):
        """Get all categories"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, name, description, parent_id
                    FROM categories
                    ORDER BY name
                ''')
                
                return [{
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'parent_id': row[3]
                } for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Get categories failed: {e}")
            raise
    
    def get_user_mods(self, user_id):
        """Get all mods by a specific user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, title, description, upload_date, download_count,
                           rating, is_public, version
                    FROM mods
                    WHERE author_id = ?
                    ORDER BY upload_date DESC
                ''', (user_id,))
                
                return [{
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'upload_date': row[3],
                    'download_count': row[4],
                    'rating': row[5],
                    'is_public': row[6],
                    'version': row[7]
                } for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Get user mods failed: {e}")
            raise
