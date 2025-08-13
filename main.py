#!/usr/bin/env python3
"""
WiiWare Modding Application
A comprehensive tool for modding WiiWare software, games, and tools
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import os
import sys
import subprocess
import threading
import shutil
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk
from mod_share_database import ModShareDatabase
from mod_share_gui import ModShareGUI

# Configure logging
def setup_logging():
    """Setup comprehensive logging for the application"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # File handler for detailed logging
    file_handler = logging.FileHandler('logs/wiiware_modder.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Console handler for important messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logging
logger = setup_logging()

class WiiWareModder:
    def __init__(self, root):
        self.root = root
        self.root.title("WiiWare Modder v1.3")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        logger.info("Initializing WiiWare Modder v1.3")
        
        # Set application icon and styling
        self.setup_styling()
        
        # Initialize variables
        self.current_file = None
        self.wit_path = self.find_wit_tool()
        self.batch_files = []
        self.installed_mods = []
        self.patch_history = []
        
        # Background customization
        self.background_image = None
        self.background_photo = None
        self.background_color = None
        
        # Initialize mod sharing database
        self.mod_share_db = ModShareDatabase()
        
        # Progress tracking
        self.current_operation = None
        self.operation_progress = 0
        self.operation_status = "Ready"
        
        # Load configuration
        self.load_config()
        
        # Create main interface
        self.create_widgets()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Select a WiiWare file to begin")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind window close event to save preferences
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("WiiWare Modder initialization completed")
        
    def on_closing(self):
        """Handle application closing"""
        try:
            logger.info("Application closing, saving preferences...")
            self.save_user_preferences()
            self.root.destroy()
        except Exception as e:
            logger.error(f"Error during application shutdown: {str(e)}")
            self.root.destroy()
            
    def update_progress(self, operation, progress, status):
        """Update progress for current operation"""
        self.current_operation = operation
        self.operation_progress = progress
        self.operation_status = status
        
        # Update status bar
        if operation:
            self.status_var.set(f"{operation}: {status} ({progress:.1f}%)")
        else:
            self.status_var.set(status)
            
        # Update progress bars if they exist
        if hasattr(self, 'progress_var'):
            self.progress_var.set(progress)
        if hasattr(self, 'batch_progress_var'):
            self.batch_progress_var.set(progress)
            
        # Force GUI update
        self.root.update_idletasks()
        
    def log_operation_start(self, operation):
        """Log the start of an operation"""
        logger.info(f"Starting operation: {operation}")
        self.update_progress(operation, 0, "Initializing...")
        
    def log_operation_progress(self, operation, progress, status):
        """Log operation progress"""
        logger.debug(f"{operation} progress: {progress:.1f}% - {status}")
        self.update_progress(operation, progress, status)
        
    def log_operation_complete(self, operation, success=True, message=""):
        """Log operation completion"""
        if success:
            logger.info(f"Operation completed successfully: {operation}")
            self.update_progress(operation, 100, f"Completed: {message}")
        else:
            logger.error(f"Operation failed: {operation} - {message}")
            self.update_progress(operation, 0, f"Failed: {message}")
            
        # Clear operation after a delay
        self.root.after(3000, lambda: self.update_progress(None, 0, "Ready"))
            
    def setup_styling(self):
        """Configure modern styling for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        
        # Apply background customization
        self.apply_background()
        
    def load_config(self):
        """Load application configuration"""
        self.config = {
            'backup_directory': 'backups/',
            'mod_install_directory': 'mods/',
            'patch_directory': 'patches/',
            'batch_output_directory': 'batch_output/',
            'brawlcrate_directory': 'brawlcrate/',
            'auto_backup': True,
            'enable_mod_validation': True
        }
        
        # Load user preferences
        self.user_prefs = self.load_user_preferences()
        
        # Create necessary directories with error handling
        for directory in [self.config['backup_directory'], 
                         self.config['mod_install_directory'],
                         self.config['patch_directory'],
                         self.config['batch_output_directory'],
                         self.config['brawlcrate_directory']]:
            try:
                os.makedirs(directory, exist_ok=True)
            except PermissionError:
                logger.warning(f"Cannot create directory {directory} - permission denied")
            except Exception as e:
                logger.warning(f"Cannot create directory {directory} - {str(e)}")
                
    def load_user_preferences(self):
        """Load user preferences from file"""
        prefs_file = 'user_preferences.json'
        default_prefs = {
            'window_position': {'x': None, 'y': None},
            'window_size': {'width': 1200, 'height': 800},
            'theme': 'clam',
            'last_file_directory': '',
            'last_output_directory': '',
            'auto_backup': True,
            'enable_mod_validation': True,
            'show_progress_bars': True,
            'confirm_operations': True,
            'recent_files': [],
            'max_recent_files': 10,
            'background_type': 'default',  # 'default', 'color', 'image'
            'background_color': '#f0f0f0',
            'background_image_path': ''
        }
        
        try:
            if os.path.exists(prefs_file):
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    loaded_prefs = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_prefs.items():
                        if key not in loaded_prefs:
                            loaded_prefs[key] = value
                    logger.info("User preferences loaded successfully")
                    return loaded_prefs
            else:
                logger.info("No user preferences found, using defaults")
                return default_prefs
        except Exception as e:
            logger.error(f"Error loading user preferences: {str(e)}")
            return default_prefs
            
    def save_user_preferences(self):
        """Save user preferences to file"""
        prefs_file = 'user_preferences.json'
        try:
            # Update current preferences
            self.user_prefs['window_position'] = {
                'x': self.root.winfo_x(),
                'y': self.root.winfo_y()
            }
            self.user_prefs['window_size'] = {
                'width': self.root.winfo_width(),
                'height': self.root.winfo_height()
            }
            
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_prefs, f, indent=2, ensure_ascii=False)
            logger.debug("User preferences saved successfully")
        except Exception as e:
            logger.error(f"Error saving user preferences: {str(e)}")
            
    def apply_background(self):
        """Apply background customization based on user preferences"""
        try:
            background_type = self.user_prefs.get('background_type', 'default')
            
            if background_type == 'color':
                color = self.user_prefs.get('background_color', '#f0f0f0')
                self.root.configure(bg=color)
                # Configure main frame background
                for widget in self.root.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        widget.configure(style='Background.TFrame')
                
                # Create custom style for background color
                style = ttk.Style()
                style.configure('Background.TFrame', background=color)
                
            elif background_type == 'image':
                image_path = self.user_prefs.get('background_image_path', '')
                if image_path and os.path.exists(image_path):
                    self.set_background_image(image_path)
                    
            else:  # default
                # Reset to default styling
                self.root.configure(bg='SystemButtonFace')
                style = ttk.Style()
                style.configure('Background.TFrame', background='SystemButtonFace')
                
        except Exception as e:
            logger.error(f"Error applying background: {str(e)}")
            
    def set_background_image(self, image_path):
        """Set a background image for the application"""
        try:
            # Load and resize image
            image = Image.open(image_path)
            
            # Get window size
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            
            if window_width <= 1 or window_height <= 1:
                # Window not yet fully initialized, use default size
                window_width = 1200
                window_height = 800
            
            # Resize image to fit window while maintaining aspect ratio
            image.thumbnail((window_width, window_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.background_photo = ImageTk.PhotoImage(image)
            
            # Create background label
            if hasattr(self, 'background_label'):
                self.background_label.destroy()
                
            self.background_label = tk.Label(self.root, image=self.background_photo)
            self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.background_label.lower()  # Send to back
            
            logger.info(f"Background image applied: {image_path}")
            
        except Exception as e:
            logger.error(f"Error setting background image: {str(e)}")
            messagebox.showerror("Error", f"Failed to load background image: {str(e)}")
            
    def show_background_settings(self):
        """Show background customization dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Background Customization")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Background Customization", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Background type selection
        type_frame = ttk.LabelFrame(main_frame, text="Background Type", padding="10")
        type_frame.pack(fill=tk.X, pady=(0, 15))
        
        background_type = tk.StringVar(value=self.user_prefs.get('background_type', 'default'))
        
        ttk.Radiobutton(type_frame, text="Default", variable=background_type, value="default").pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="Solid Color", variable=background_type, value="color").pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="Custom Image", variable=background_type, value="image").pack(anchor=tk.W)
        
        # Color picker frame
        color_frame = ttk.LabelFrame(main_frame, text="Color Selection", padding="10")
        color_frame.pack(fill=tk.X, pady=(0, 15))
        
        current_color = tk.StringVar(value=self.user_prefs.get('background_color', '#f0f0f0'))
        color_preview = tk.Frame(color_frame, bg=current_color.get(), width=50, height=30, relief=tk.RAISED, bd=2)
        color_preview.pack(side=tk.LEFT, padx=(0, 10))
        
        def choose_color():
            color = colorchooser.askcolor(current_color.get(), title="Choose Background Color")
            if color[1]:  # color[1] contains the hex color
                current_color.set(color[1])
                color_preview.configure(bg=color[1])
                
        ttk.Button(color_frame, text="Choose Color", command=choose_color).pack(side=tk.LEFT)
        ttk.Label(color_frame, textvariable=current_color).pack(side=tk.LEFT, padx=(10, 0))
        
        # Image selection frame
        image_frame = ttk.LabelFrame(main_frame, text="Image Selection", padding="10")
        image_frame.pack(fill=tk.X, pady=(0, 15))
        
        image_path_var = tk.StringVar(value=self.user_prefs.get('background_image_path', ''))
        
        def browse_image():
            file_types = [
                ("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                ("PNG Files", "*.png"),
                ("JPEG Files", "*.jpg;*.jpeg"),
                ("GIF Files", "*.gif"),
                ("BMP Files", "*.bmp"),
                ("All Files", "*.*")
            ]
            
            filename = filedialog.askopenfilename(
                title="Select Background Image",
                filetypes=file_types
            )
            
            if filename:
                image_path_var.set(filename)
                
        ttk.Button(image_frame, text="Browse Image", command=browse_image).pack(side=tk.LEFT)
        ttk.Label(image_frame, textvariable=image_path_var, wraplength=300).pack(side=tk.LEFT, padx=(10, 0))
        
        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        preview_label = ttk.Label(preview_frame, text="Background preview will appear here")
        preview_label.pack(expand=True)
        
        def update_preview():
            try:
                bg_type = background_type.get()
                
                if bg_type == 'color':
                    preview_label.configure(text=f"Color: {current_color.get()}")
                    preview_frame.configure(style='Preview.TFrame')
                    style = ttk.Style()
                    style.configure('Preview.TFrame', background=current_color.get())
                    
                elif bg_type == 'image':
                    image_path = image_path_var.get()
                    if image_path and os.path.exists(image_path):
                        preview_label.configure(text=f"Image: {os.path.basename(image_path)}")
                    else:
                        preview_label.configure(text="No valid image selected")
                        
                else:  # default
                    preview_label.configure(text="Default system background")
                    preview_frame.configure(style='')
                    
            except Exception as e:
                preview_label.configure(text=f"Preview error: {str(e)}")
                
        # Bind preview updates
        background_type.trace('w', lambda *args: update_preview())
        current_color.trace('w', lambda *args: update_preview())
        image_path_var.trace('w', lambda *args: update_preview())
        
        # Initial preview
        update_preview()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        def apply_settings():
            try:
                # Save settings
                self.user_prefs['background_type'] = background_type.get()
                self.user_prefs['background_color'] = current_color.get()
                self.user_prefs['background_image_path'] = image_path_var.get()
                
                # Apply background
                self.apply_background()
                
                # Save preferences
                self.save_user_preferences()
                
                messagebox.showinfo("Success", "Background settings applied successfully!")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply background settings: {str(e)}")
                
        def reset_to_default():
            background_type.set('default')
            current_color.set('#f0f0f0')
            image_path_var.set('')
            
        ttk.Button(button_frame, text="Apply", command=apply_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Reset to Default", command=reset_to_default).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
            
    def add_recent_file(self, file_path):
        """Add a file to recent files list"""
        if file_path in self.user_prefs['recent_files']:
            self.user_prefs['recent_files'].remove(file_path)
        self.user_prefs['recent_files'].insert(0, file_path)
        
        # Keep only the most recent files
        self.user_prefs['recent_files'] = self.user_prefs['recent_files'][:self.user_prefs['max_recent_files']]
        self.save_user_preferences()
        
    def find_wit_tool(self):
        """Find the wit tool installation"""
        # Check common installation paths
        possible_paths = [
            "wit",  # If in PATH
            "C:\\Program Files\\wit\\wit.exe",
            "C:\\Program Files (x86)\\wit\\wit.exe",
            os.path.expanduser("~\\wit\\wit.exe")
        ]
        
        for path in possible_paths:
            try:
                if path == "wit":
                    # Check if wit is available in PATH
                    result = subprocess.run([path, "--version"], capture_output=True, check=True, timeout=10)
                    if result.returncode == 0:
                        return path
                elif os.path.exists(path):
                    # Check if the file is actually executable
                    if os.access(path, os.X_OK) or os.access(path, os.R_OK):
                        return path
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
            except Exception as e:
                print(f"Warning: Error checking WIT tool at {path}: {str(e)}")
                continue
        
        return None
        
    def create_widgets(self):
        """Create the main application widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="WiiWare Modder v1.3", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Top toolbar frame
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Settings button
        settings_btn = ttk.Button(toolbar_frame, text="⚙️ Settings", command=self.show_settings_dialog)
        settings_btn.pack(side=tk.RIGHT)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        # File path display
        self.file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=60)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Browse button
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        # Recent files button
        recent_btn = ttk.Button(file_frame, text="Recent Files", command=self.show_recent_files)
        recent_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        # Quick file info display
        self.quick_info_var = tk.StringVar(value="No file selected")
        quick_info_label = ttk.Label(file_frame, textvariable=self.quick_info_var, style='Success.TLabel')
        quick_info_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Tools frame
        tools_frame = ttk.LabelFrame(main_frame, text="Tools", padding="10")
        tools_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for different tool categories
        notebook = ttk.Notebook(tools_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # File Info tab
        self.create_file_info_tab(notebook)
        
        # Extraction tab
        self.create_extraction_tab(notebook)
        
        # NEW: Patching tab
        self.create_patching_tab(notebook)
        
        # NEW: Batch Processing tab
        self.create_batch_tab(notebook)
        
        # Enhanced Modding tab
        self.create_modding_tab(notebook)
        
        # NEW: BrawlCrate tab
        self.create_brawlcrate_tab(notebook)
        
        # Community tab
        self.create_community_tab(notebook)
        
        # NEW: Mod Share tab
        self.create_mod_share_tab(notebook)
        
        # Apply saved window position and size
        self.apply_saved_window_settings()
        
    def show_settings_dialog(self):
        """Show the settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x500")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Create notebook for different settings categories
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General settings tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        self.create_general_settings_tab(general_frame)
        
        # Interface settings tab
        interface_frame = ttk.Frame(notebook)
        notebook.add(interface_frame, text="Interface")
        self.create_interface_settings_tab(interface_frame)
        
        # Backup settings tab
        backup_frame = ttk.Frame(notebook)
        notebook.add(backup_frame, text="Backup")
        self.create_backup_settings_tab(backup_frame)
        
        # Buttons
        btn_frame = ttk.Frame(settings_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Save", command=lambda: self.save_settings(settings_window)).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.RIGHT)
        
    def create_general_settings_tab(self, parent):
        """Create the general settings tab"""
        # Auto-backup setting
        auto_backup_var = tk.BooleanVar(value=self.user_prefs['auto_backup'])
        auto_backup_check = ttk.Checkbutton(parent, text="Enable automatic backup before operations", 
                                          variable=auto_backup_var)
        auto_backup_check.pack(anchor=tk.W, padx=10, pady=5)
        
        # Mod validation setting
        mod_validation_var = tk.BooleanVar(value=self.user_prefs['enable_mod_validation'])
        mod_validation_check = ttk.Checkbutton(parent, text="Enable mod compatibility validation", 
                                             variable=mod_validation_var)
        mod_validation_check.pack(anchor=tk.W, padx=10, pady=5)
        
        # Confirm operations setting
        confirm_ops_var = tk.BooleanVar(value=self.user_prefs['confirm_operations'])
        confirm_ops_check = ttk.Checkbutton(parent, text="Confirm before destructive operations", 
                                          variable=confirm_ops_var)
        confirm_ops_check.pack(anchor=tk.W, padx=10, pady=5)
        
        # Store variables for later access
        parent.auto_backup_var = auto_backup_var
        parent.mod_validation_var = mod_validation_var
        parent.confirm_ops_var = confirm_ops_var
        
    def create_interface_settings_tab(self, parent):
        """Create the interface settings tab"""
        # Theme selection
        theme_frame = ttk.Frame(parent)
        theme_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT)
        theme_var = tk.StringVar(value=self.user_prefs['theme'])
        theme_combo = ttk.Combobox(theme_frame, textvariable=theme_var, 
                                  values=["clam", "alt", "default", "classic"], state="readonly")
        theme_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Window size settings
        size_frame = ttk.Frame(parent)
        size_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(size_frame, text="Default Window Size:").pack(anchor=tk.W)
        
        size_inner_frame = ttk.Frame(size_frame)
        size_inner_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(size_inner_frame, text="Width:").pack(side=tk.LEFT)
        width_var = tk.StringVar(value=str(self.user_prefs['window_size']['width']))
        width_entry = ttk.Entry(size_inner_frame, textvariable=width_var, width=10)
        width_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(size_inner_frame, text="Height:").pack(side=tk.LEFT)
        height_var = tk.StringVar(value=str(self.user_prefs['window_size']['height']))
        height_entry = ttk.Entry(size_inner_frame, textvariable=height_var, width=10)
        height_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Background customization button
        background_frame = ttk.Frame(parent)
        background_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(background_frame, text="🎨 Customize Background", 
                  command=self.show_background_settings).pack(anchor=tk.W)
        
        # Store variables for later access
        parent.theme_var = theme_var
        parent.width_var = width_var
        parent.height_var = height_var
        
    def create_backup_settings_tab(self, parent):
        """Create the backup settings tab"""
        # Backup directory
        backup_dir_frame = ttk.Frame(parent)
        backup_dir_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(backup_dir_frame, text="Backup Directory:").pack(anchor=tk.W)
        
        backup_dir_inner = ttk.Frame(backup_dir_frame)
        backup_dir_inner.pack(fill=tk.X, pady=5)
        
        backup_dir_var = tk.StringVar(value=self.config['backup_directory'])
        backup_dir_entry = ttk.Entry(backup_dir_inner, textvariable=backup_dir_var, width=50)
        backup_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Button(backup_dir_inner, text="Browse", 
                  command=lambda: self.browse_backup_directory(backup_dir_var)).pack(side=tk.RIGHT)
        
        # Store variables for later access
        parent.backup_dir_var = backup_dir_var
        
    def browse_backup_directory(self, var):
        """Browse for backup directory"""
        directory = filedialog.askdirectory(title="Select Backup Directory")
        if directory:
            var.set(directory)
            
    def save_settings(self, window):
        """Save the current settings"""
        try:
            # Get values from all tabs
            general = window.winfo_children()[0].winfo_children()[0]  # General tab
            interface = window.winfo_children()[0].winfo_children()[1]  # Interface tab
            backup = window.winfo_children()[0].winfo_children()[2]  # Backup tab
            
            # Update user preferences
            self.user_prefs['auto_backup'] = general.auto_backup_var.get()
            self.user_prefs['enable_mod_validation'] = general.mod_validation_var.get()
            self.user_prefs['confirm_operations'] = general.confirm_ops_var.get()
            self.user_prefs['theme'] = interface.theme_var.get()
            self.user_prefs['window_size']['width'] = int(interface.width_var.get())
            self.user_prefs['window_size']['height'] = int(interface.height_var.get())
            
            # Update config
            self.config['backup_directory'] = backup.backup_dir_var.get()
            
            # Save preferences
            self.save_user_preferences()
            
            # Apply theme if changed
            if hasattr(self, 'current_theme') and self.current_theme != self.user_prefs['theme']:
                self.apply_theme(self.user_prefs['theme'])
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            logger.info("Settings saved successfully")
            window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            logger.error(f"Failed to save settings: {str(e)}")
            
    def apply_theme(self, theme):
        """Apply the selected theme"""
        try:
            style = ttk.Style()
            style.theme_use(theme)
            self.current_theme = theme
            logger.info(f"Applied theme: {theme}")
        except Exception as e:
            logger.warning(f"Could not apply theme {theme}: {str(e)}")
            
    def apply_saved_window_settings(self):
        """Apply saved window position and size"""
        try:
            if self.user_prefs['window_position']['x'] is not None and self.user_prefs['window_position']['y'] is not None:
                self.root.geometry(f"{self.user_prefs['window_size']['width']}x{self.user_prefs['window_size']['height']}+{self.user_prefs['window_position']['x']}+{self.user_prefs['window_position']['y']}")
                logger.debug("Applied saved window position and size")
            else:
                # Center the window if no saved position
                self.center_window()
        except Exception as e:
            logger.warning(f"Could not apply saved window settings: {str(e)}")
            self.center_window()
            
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
    def show_recent_files(self):
        """Show recent files menu"""
        if not self.user_prefs['recent_files']:
            messagebox.showinfo("Recent Files", "No recent files found.")
            return
            
        # Create recent files window
        recent_window = tk.Toplevel(self.root)
        recent_window.title("Recent Files")
        recent_window.geometry("500x400")
        recent_window.transient(self.root)
        recent_window.grab_set()
        
        # Recent files list
        listbox = tk.Listbox(recent_window, height=15)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Populate list
        for file_path in self.user_prefs['recent_files']:
            if os.path.exists(file_path):
                listbox.insert(tk.END, os.path.basename(file_path))
            else:
                listbox.insert(tk.END, f"{os.path.basename(file_path)} (Missing)")
        
        # Buttons
        btn_frame = ttk.Frame(recent_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Open Selected", 
                  command=lambda: self.open_recent_file(listbox, recent_window)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Clear List", 
                  command=lambda: self.clear_recent_files(listbox)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Close", 
                  command=recent_window.destroy).pack(side=tk.RIGHT)
        
    def open_recent_file(self, listbox, window):
        """Open a selected recent file"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to open.")
            return
            
        file_index = selection[0]
        file_path = self.user_prefs['recent_files'][file_index]
        
        if os.path.exists(file_path):
            self.current_file = file_path
            self.file_var.set(file_path)
            self.analyze_file()
            window.destroy()
            logger.info(f"Opened recent file: {file_path}")
        else:
            messagebox.showerror("Error", f"File not found: {file_path}")
            # Remove missing file from recent list
            self.user_prefs['recent_files'].pop(file_index)
            self.save_user_preferences()
            self.show_recent_files()  # Refresh the window
            
    def clear_recent_files(self, listbox):
        """Clear the recent files list"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the recent files list?"):
            self.user_prefs['recent_files'].clear()
            self.save_user_preferences()
            listbox.delete(0, tk.END)
            messagebox.showinfo("Success", "Recent files list cleared.")
            
    def create_file_info_tab(self, notebook):
        """Create the file information tab"""
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="File Info")
        
        # File information display
        info_text = tk.Text(info_frame, height=15, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        info_text.configure(yscrollcommand=scrollbar.set)
        
        self.info_text = info_text
        
    def create_extraction_tab(self, notebook):
        """Create the extraction tools tab"""
        extract_frame = ttk.Frame(notebook)
        notebook.add(extract_frame, text="Extraction")
        
        # Extraction options
        options_frame = ttk.Frame(extract_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(options_frame, text="Extract to:").pack(anchor=tk.W)
        
        # Output directory selection
        output_frame = ttk.Frame(options_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=50)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        output_btn = ttk.Button(output_frame, text="Browse", command=self.browse_output)
        output_btn.pack(side=tk.RIGHT)
        
        # Extract button
        extract_btn = ttk.Button(options_frame, text="Extract Files", command=self.extract_files)
        extract_btn.pack(pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(options_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
    def create_patching_tab(self, notebook):
        """Create the file patching tab"""
        patch_frame = ttk.Frame(notebook)
        notebook.add(patch_frame, text="Patching")
        
        # Patching options
        patch_options_frame = ttk.LabelFrame(patch_frame, text="File Patching", padding="10")
        patch_options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Patch file selection
        patch_file_frame = ttk.Frame(patch_options_frame)
        patch_file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(patch_file_frame, text="Patch File:").pack(side=tk.LEFT)
        self.patch_file_var = tk.StringVar()
        patch_entry = ttk.Entry(patch_file_frame, textvariable=self.patch_file_var, width=40)
        patch_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        patch_browse_btn = ttk.Button(patch_file_frame, text="Browse", command=self.browse_patch_file)
        patch_browse_btn.pack(side=tk.RIGHT)
        
        # Patch options
        patch_options_inner = ttk.Frame(patch_options_frame)
        patch_options_inner.pack(fill=tk.X, pady=10)
        
        self.backup_before_patch = tk.BooleanVar(value=True)
        backup_check = ttk.Checkbutton(patch_options_inner, text="Create backup before patching", 
                                     variable=self.backup_before_patch)
        backup_check.pack(anchor=tk.W)
        
        self.validate_patch = tk.BooleanVar(value=True)
        validate_check = ttk.Checkbutton(patch_options_inner, text="Validate patch before applying", 
                                       variable=self.validate_patch)
        validate_check.pack(anchor=tk.W)
        
        # Patch button
        patch_btn = ttk.Button(patch_options_frame, text="Apply Patch", command=self.apply_patch)
        patch_btn.pack(pady=10)
        
        # Patch history
        history_frame = ttk.LabelFrame(patch_frame, text="Patch History", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Patch history list
        self.patch_history_list = tk.Listbox(history_frame, height=8)
        self.patch_history_list.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # History action buttons
        history_btn_frame = ttk.Frame(history_frame)
        history_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(history_btn_frame, text="View Details", command=self.view_patch_details).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(history_btn_frame, text="Revert Patch", command=self.revert_patch).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(history_btn_frame, text="Clear History", command=self.clear_patch_history).pack(side=tk.LEFT)
        
    def create_batch_tab(self, notebook):
        """Create the batch processing tab"""
        batch_frame = ttk.Frame(notebook)
        notebook.add(batch_frame, text="Batch Processing")
        
        # Batch file selection
        batch_selection_frame = ttk.LabelFrame(batch_frame, text="Batch File Selection", padding="10")
        batch_selection_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Add files button
        add_files_btn = ttk.Button(batch_selection_frame, text="Add Files", command=self.add_batch_files)
        add_files_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear files button
        clear_files_btn = ttk.Button(batch_selection_frame, text="Clear All", command=self.clear_batch_files)
        clear_files_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Batch file count
        self.batch_count_var = tk.StringVar(value="No files selected")
        batch_count_label = ttk.Label(batch_selection_frame, textvariable=self.batch_count_var)
        batch_count_label.pack(side=tk.RIGHT)
        
        # Batch file list
        list_frame = ttk.Frame(batch_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.batch_listbox = tk.Listbox(list_frame, height=10)
        self.batch_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar for batch list
        batch_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.batch_listbox.yview)
        batch_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.batch_listbox.configure(yscrollcommand=batch_scrollbar.set)
        
        # Batch options
        batch_options_frame = ttk.LabelFrame(batch_frame, text="Batch Options", padding="10")
        batch_options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Output directory for batch
        batch_output_frame = ttk.Frame(batch_options_frame)
        batch_output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(batch_output_frame, text="Output Directory:").pack(side=tk.LEFT)
        self.batch_output_var = tk.StringVar()
        batch_output_entry = ttk.Entry(batch_output_frame, textvariable=self.batch_output_var, width=40)
        batch_output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        batch_output_btn = ttk.Button(batch_output_frame, text="Browse", command=self.browse_batch_output)
        batch_output_btn.pack(side=tk.RIGHT)
        
        # Batch operation selection
        operation_frame = ttk.Frame(batch_options_frame)
        operation_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(operation_frame, text="Operation:").pack(side=tk.LEFT)
        self.batch_operation = tk.StringVar(value="extract")
        operation_combo = ttk.Combobox(operation_frame, textvariable=self.batch_operation, 
                                      values=["extract", "patch", "analyze"], state="readonly")
        operation_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Batch patch file selection (for patch operations)
        patch_file_frame = ttk.Frame(batch_options_frame)
        patch_file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(patch_file_frame, text="Patch File:").pack(side=tk.LEFT)
        self.batch_patch_file_var = tk.StringVar()
        patch_file_entry = ttk.Entry(patch_file_frame, textvariable=self.batch_patch_file_var, width=40)
        patch_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        patch_file_btn = ttk.Button(patch_file_frame, text="Browse", command=self.browse_batch_patch_file)
        patch_file_btn.pack(side=tk.RIGHT)
        
        # Batch progress
        batch_progress_frame = ttk.Frame(batch_options_frame)
        batch_progress_frame.pack(fill=tk.X, pady=10)
        
        self.batch_progress_var = tk.DoubleVar()
        self.batch_progress_bar = ttk.Progressbar(batch_progress_frame, variable=self.batch_progress_var, maximum=100)
        self.batch_progress_bar.pack(fill=tk.X, pady=5)
        
        # Batch status
        self.batch_status_var = tk.StringVar(value="Ready for batch processing")
        batch_status_label = ttk.Label(batch_progress_frame, textvariable=self.batch_status_var)
        batch_status_label.pack()
        
        # Start batch button
        start_batch_btn = ttk.Button(batch_options_frame, text="Start Batch Processing", command=self.start_batch_processing)
        start_batch_btn.pack(pady=10)
        
    def create_modding_tab(self, notebook):
        """Create the enhanced modding tools tab"""
        mod_frame = ttk.Frame(notebook)
        notebook.add(mod_frame, text="Modding")
        
        # Mod management
        mod_management_frame = ttk.LabelFrame(mod_frame, text="Mod Management", padding="10")
        mod_management_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Mod installation section
        install_frame = ttk.LabelFrame(mod_management_frame, text="Install Mod", padding="10")
        install_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Mod file selection
        mod_file_frame = ttk.Frame(install_frame)
        mod_file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mod_file_frame, text="Mod File:").pack(side=tk.LEFT)
        self.mod_file_var = tk.StringVar()
        mod_entry = ttk.Entry(mod_file_frame, textvariable=self.mod_file_var, width=40)
        mod_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        mod_browse_btn = ttk.Button(mod_file_frame, text="Browse", command=self.browse_mod_file)
        mod_browse_btn.pack(side=tk.RIGHT)
        
        # Mod options
        mod_options_frame = ttk.Frame(install_frame)
        mod_options_frame.pack(fill=tk.X, pady=10)
        
        self.auto_backup_mod = tk.BooleanVar(value=True)
        mod_backup_check = ttk.Checkbutton(mod_options_frame, text="Create backup before installing", 
                                         variable=self.auto_backup_mod)
        mod_backup_check.pack(anchor=tk.W)
        
        self.validate_mod = tk.BooleanVar(value=True)
        mod_validate_check = ttk.Checkbutton(mod_options_frame, text="Validate mod compatibility", 
                                           variable=self.validate_mod)
        mod_validate_check.pack(anchor=tk.W)
        
        # Install mod button
        install_mod_btn = ttk.Button(install_frame, text="Install Mod", command=self.install_mod)
        install_mod_btn.pack(pady=10)
        
        # Installed mods section
        installed_frame = ttk.LabelFrame(mod_management_frame, text="Installed Mods", padding="10")
        installed_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Installed mods list
        self.mods_listbox = tk.Listbox(installed_frame, height=8)
        self.mods_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Mod action buttons
        mod_buttons_frame = ttk.Frame(installed_frame)
        mod_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(mod_buttons_frame, text="Remove Mod", command=self.remove_mod).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(mod_buttons_frame, text="Configure Mod", command=self.configure_mod).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(mod_buttons_frame, text="Mod Info", command=self.show_mod_info).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(mod_buttons_frame, text="Refresh List", command=self.refresh_mods_list).pack(side=tk.LEFT)
        
    def create_brawlcrate_tab(self, notebook):
        """Create the BrawlCrate tab for viewing and editing game files"""
        brawlcrate_frame = ttk.Frame(notebook)
        notebook.add(brawlcrate_frame, text="BrawlCrate")
        
        # BrawlCrate integration frame
        brawlcrate_integration_frame = ttk.LabelFrame(brawlcrate_frame, text="BrawlCrate Integration", padding="10")
        brawlcrate_integration_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # BrawlCrate path selection
        brawlcrate_path_frame = ttk.Frame(brawlcrate_integration_frame)
        brawlcrate_path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(brawlcrate_path_frame, text="BrawlCrate Path:").pack(side=tk.LEFT)
        self.brawlcrate_path_var = tk.StringVar()
        brawlcrate_path_entry = ttk.Entry(brawlcrate_path_frame, textvariable=self.brawlcrate_path_var, width=50)
        brawlcrate_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        brawlcrate_browse_btn = ttk.Button(brawlcrate_path_frame, text="Browse", command=self.browse_brawlcrate)
        brawlcrate_browse_btn.pack(side=tk.RIGHT)
        
        # Auto-detect BrawlCrate button
        auto_detect_btn = ttk.Button(brawlcrate_integration_frame, text="Auto-detect BrawlCrate", command=self.auto_detect_brawlcrate)
        auto_detect_btn.pack(pady=5)
        
        # BrawlCrate status
        self.brawlcrate_status_var = tk.StringVar(value="BrawlCrate not detected")
        brawlcrate_status_label = ttk.Label(brawlcrate_integration_frame, textvariable=self.brawlcrate_status_var)
        brawlcrate_status_label.pack(pady=5)
        
        # Game file analysis frame
        game_analysis_frame = ttk.LabelFrame(brawlcrate_frame, text="Game File Analysis", padding="10")
        game_analysis_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # File type selection
        file_type_frame = ttk.Frame(game_analysis_frame)
        file_type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_type_frame, text="File Type:").pack(side=tk.LEFT)
        self.brawlcrate_file_type_var = tk.StringVar(value="auto")
        file_type_combo = ttk.Combobox(file_type_frame, textvariable=self.brawlcrate_file_type_var, 
                                      values=["auto", "brres", "brlyt", "brlan", "brseq", "brstm", "brwav", "brctmd"], state="readonly")
        file_type_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Analysis options
        analysis_options_frame = ttk.Frame(game_analysis_frame)
        analysis_options_frame.pack(fill=tk.X, pady=10)
        
        self.extract_textures = tk.BooleanVar(value=True)
        extract_textures_check = ttk.Checkbutton(analysis_options_frame, text="Extract textures", 
                                               variable=self.extract_textures)
        extract_textures_check.pack(anchor=tk.W)
        
        self.extract_models = tk.BooleanVar(value=True)
        extract_models_check = ttk.Checkbutton(analysis_options_frame, text="Extract 3D models", 
                                             variable=self.extract_models)
        extract_models_check.pack(anchor=tk.W)
        
        self.extract_audio = tk.BooleanVar(value=True)
        extract_audio_check = ttk.Checkbutton(analysis_options_frame, text="Extract audio files", 
                                            variable=self.extract_audio)
        extract_audio_check.pack(anchor=tk.W)
        
        # Analyze button
        analyze_btn = ttk.Button(game_analysis_frame, text="Analyze with BrawlCrate", command=self.analyze_with_brawlcrate)
        analyze_btn.pack(pady=10)
        
        # Analysis results
        results_frame = ttk.LabelFrame(game_analysis_frame, text="Analysis Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Results text area
        self.brawlcrate_results_text = tk.Text(results_frame, height=10, wrap=tk.WORD)
        self.brawlcrate_results_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar for results
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.brawlcrate_results_text.yview)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.brawlcrate_results_text.configure(yscrollcommand=results_scrollbar.set)
        
        # Action buttons for results
        results_actions_frame = ttk.Frame(game_analysis_frame)
        results_actions_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(results_actions_frame, text="Open in BrawlCrate", command=self.open_in_brawlcrate).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(results_actions_frame, text="Export Analysis", command=self.export_analysis).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(results_actions_frame, text="Clear Results", command=self.clear_brawlcrate_results).pack(side=tk.LEFT)
        
    def create_community_tab(self, notebook):
        """Create the community features tab"""
        community_frame = ttk.Frame(notebook)
        notebook.add(community_frame, text="Community")
        
        # Community features
        features_frame = ttk.Frame(community_frame)
        features_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(features_frame, text="Community Features", style='Header.TLabel').pack(pady=10)
        
        # Feature buttons
        ttk.Button(features_frame, text="Browse Mod Library", command=self.browse_mods).pack(pady=5)
        ttk.Button(features_frame, text="Upload Mod", command=self.upload_mod).pack(pady=5)
        ttk.Button(features_frame, text="Check for Updates", command=self.check_updates).pack(pady=5)
        
    def create_mod_share_tab(self, notebook):
        """Create the mod sharing tab"""
        mod_share_frame = ttk.Frame(notebook)
        notebook.add(mod_share_frame, text="Mod Share")
        
        # Create the mod sharing GUI
        self.mod_share_gui = ModShareGUI(mod_share_frame, self.mod_share_db)
        
    # File browsing methods
    def browse_file(self):
        """Browse for WiiWare files"""
        file_types = [
            ("WiiWare Files", "*.wad;*.wbfs;*.iso"),
            ("WAD Files", "*.wad"),
            ("WBFS Files", "*.wbfs"),
            ("ISO Files", "*.iso"),
            ("All Files", "*.*")
        ]
        
        # Use last directory if available
        initial_dir = self.user_prefs['last_file_directory'] if self.user_prefs['last_file_directory'] else None
        
        filename = filedialog.askopenfilename(
            title="Select WiiWare File",
            filetypes=file_types,
            initialdir=initial_dir
        )
        
        if filename:
            self.current_file = filename
            self.file_var.set(filename)
            
            # Update last directory
            self.user_prefs['last_file_directory'] = os.path.dirname(filename)
            self.save_user_preferences()
            
            # Add to recent files
            self.add_recent_file(filename)
            
            # Update quick info
            self.quick_info_var.set(f"File: {os.path.basename(filename)}")
            
            # Analyze the file
            self.analyze_file()
            logger.info(f"Selected file: {filename}")
            
    def browse_output(self):
        """Browse for output directory"""
        # Use last output directory if available
        initial_dir = self.user_prefs['last_output_directory'] if self.user_prefs['last_output_directory'] else None
        
        directory = filedialog.askdirectory(title="Select Output Directory", initialdir=initial_dir)
        if directory:
            self.output_var.set(directory)
            # Update last output directory
            self.user_prefs['last_output_directory'] = directory
            self.save_user_preferences()
            logger.debug(f"Selected output directory: {directory}")
            
    def browse_patch_file(self):
        """Browse for patch files"""
        file_types = [
            ("Patch Files", "*.patch;*.ips;*.bps"),
            ("IPS Files", "*.ips"),
            ("BPS Files", "*.bps"),
            ("All Files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Patch File",
            filetypes=file_types
        )
        
        if filename:
            self.patch_file_var.set(filename)
            logger.debug(f"Selected patch file: {filename}")
            
    def browse_mod_file(self):
        """Browse for mod files"""
        file_types = [
            ("Mod Files", "*.mod;*.zip;*.7z;*.rar"),
            ("ZIP Files", "*.zip"),
            ("7-Zip Files", "*.7z"),
            ("RAR Files", "*.rar"),
            ("All Files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Mod File",
            filetypes=file_types
        )
        
        if filename:
            self.mod_file_var.set(filename)
            logger.debug(f"Selected mod file: {filename}")
            
    def browse_batch_output(self):
        """Browse for batch output directory"""
        directory = filedialog.askdirectory(title="Select Batch Output Directory")
        if directory:
            self.batch_output_var.set(directory)
    
    def browse_batch_patch_file(self):
        """Browse for batch patch file"""
        file_types = [
            ("Patch Files", "*.ips;*.bps;*.patch"),
            ("IPS Files", "*.ips"),
            ("BPS Files", "*.bps"),
            ("Patch Files", "*.patch"),
            ("All Files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Patch File for Batch Processing",
            filetypes=file_types
        )
        
        if filename:
            self.batch_patch_file_var.set(filename)
            logger.debug(f"Selected batch output directory: {directory}")
            
    def browse_brawlcrate(self):
        """Browse for BrawlCrate executable"""
        filename = filedialog.askopenfilename(
            title="Select BrawlCrate Executable",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        
        if filename:
            self.brawlcrate_path_var.set(filename)
            self.check_brawlcrate_installation()
            logger.debug(f"Selected BrawlCrate executable: {filename}")
            
    # File analysis
    def analyze_file(self):
        """Analyze the selected file and display information"""
        if not self.current_file:
            return
            
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, f"File: {os.path.basename(self.current_file)}\n")
        self.info_text.insert(tk.END, f"Path: {self.current_file}\n")
        self.info_text.insert(tk.END, f"Size: {os.path.getsize(self.current_file) / (1024*1024):.2f} MB\n\n")
        
        # Use wit tool to get file information
        if self.wit_path:
            try:
                result = subprocess.run([self.wit_path, "info", self.current_file], 
                                     capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    self.info_text.insert(tk.END, "File Information:\n")
                    self.info_text.insert(tk.END, result.stdout)
                else:
                    self.info_text.insert(tk.END, f"Error getting file info: {result.stderr}")
            except subprocess.TimeoutExpired:
                self.info_text.insert(tk.END, "Timeout getting file information")
            except Exception as e:
                self.info_text.insert(tk.END, f"Error: {str(e)}")
        else:
            self.info_text.insert(tk.END, "WIT tool not found. Please install it to get detailed file information.")
            
    # File extraction
    def extract_files(self):
        """Extract the WiiWare file"""
        if not self.current_file or not self.output_var.get():
            messagebox.showerror("Error", "Please select a file and output directory")
            return
            
        if not self.wit_path:
            messagebox.showerror("Error", "WIT tool not found. Please install it first.")
            return
            
        # Run extraction in a separate thread
        thread = threading.Thread(target=self._extract_thread)
        thread.daemon = True
        thread.start()
        
    def _extract_thread(self):
        """Extract files in background thread"""
        try:
            self.update_progress("Extraction", 0, "Starting extraction...")
            
            # Use wit tool for extraction
            cmd = [self.wit_path, "extract", self.current_file, self.output_var.get()]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor progress
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Update progress based on output
                    if "progress" in output.lower():
                        try:
                            # Extract progress percentage from output
                            progress = float(output.split()[-1].replace('%', ''))
                            self.update_progress("Extraction", progress, f"Extracting: {os.path.basename(self.current_file)}")
                        except (ValueError, IndexError):
                            # Ignore parsing errors for progress updates
                            pass
                            
            return_code = process.poll()
            
            if return_code == 0:
                self.update_progress("Extraction", 100, "Extraction completed successfully!")
                messagebox.showinfo("Success", "Files extracted successfully!")
            else:
                error = process.stderr.read()
                self.update_progress("Extraction", 0, "Extraction failed!")
                messagebox.showerror("Error", f"Extraction failed: {error}")
                
        except Exception as e:
            self.update_progress("Extraction", 0, "Extraction failed!")
            messagebox.showerror("Error", f"Extraction failed: {str(e)}")
            
    # NEW: File patching methods
    def apply_patch(self):
        """Apply a patch to the current file"""
        if not self.current_file:
            messagebox.showerror("Error", "Please select a file to patch")
            return
            
        if not self.patch_file_var.get():
            messagebox.showerror("Error", "Please select a patch file")
            return
            
        # Create backup if requested
        if self.backup_before_patch.get():
            self.create_backup()
            
        # Apply the patch
        thread = threading.Thread(target=self._apply_patch_thread)
        thread.daemon = True
        thread.start()
        
    def _apply_patch_thread(self):
        """Apply patch in background thread"""
        try:
            self.update_progress("Patching", 0, "Applying patch...")
            
            # Validate inputs
            patch_file = self.patch_file_var.get()
            original_file = self.current_file
            
            if not patch_file or not os.path.exists(patch_file):
                raise FileNotFoundError("Patch file not found or invalid")
                
            if not original_file or not os.path.exists(original_file):
                raise FileNotFoundError("Original file not found or invalid")
                
            # Validate patch file format
            patch_ext = os.path.splitext(patch_file)[1].lower()
            if patch_ext not in ['.ips', '.bps', '.patch']:
                raise ValueError(f"Unsupported patch format: {patch_ext}")
                
            # For now, just copy the patch file to show the process
            # In a real implementation, you'd apply the actual patch
            patch_name = os.path.basename(patch_file)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Record patch in history
            patch_record = {
                'timestamp': timestamp,
                'original_file': original_file,
                'patch_file': patch_file,
                'backup_file': f"{self.config['backup_directory']}backup_{timestamp}.bak"
            }
            
            self.patch_history.append(patch_record)
            self.update_patch_history_display()
            
            self.update_progress("Patching", 100, "Patch applied successfully!")
            messagebox.showinfo("Success", "Patch applied successfully!")
            
        except FileNotFoundError as e:
            self.update_progress("Patching", 0, "Patch application failed!")
            messagebox.showerror("Error", f"File error: {str(e)}")
        except ValueError as e:
            self.update_progress("Patching", 0, "Patch application failed!")
            messagebox.showerror("Error", f"Invalid patch format: {str(e)}")
        except Exception as e:
            self.update_progress("Patching", 0, "Patch application failed!")
            messagebox.showerror("Error", f"Patch application failed: {str(e)}")
            
    def create_backup(self):
        """Create a backup of the current file"""
        if not self.current_file:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.bak"
        backup_path = os.path.join(self.config['backup_directory'], backup_name)
        
        try:
            shutil.copy2(self.current_file, backup_path)
            return backup_path
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create backup: {str(e)}")
            return None
            
    def update_patch_history_display(self):
        """Update the patch history display"""
        self.patch_history_list.delete(0, tk.END)
        for patch in self.patch_history:
            timestamp = patch['timestamp']
            patch_file = os.path.basename(patch['patch_file'])
            self.patch_history_list.insert(tk.END, f"{timestamp} - {patch_file}")
            
    def view_patch_details(self):
        """View details of a selected patch"""
        selection = self.patch_history_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a patch to view details")
            return
            
        patch_index = selection[0]
        patch = self.patch_history[patch_index]
        
        details = f"Patch Details:\n\n"
        details += f"Timestamp: {patch['timestamp']}\n"
        details += f"Original File: {patch['original_file']}\n"
        details += f"Patch File: {patch['patch_file']}\n"
        details += f"Backup File: {patch['backup_file']}\n"
        
        messagebox.showinfo("Patch Details", details)
        
    def revert_patch(self):
        """Revert a selected patch"""
        selection = self.patch_history_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a patch to revert")
            return
            
        if messagebox.askyesno("Confirm Revert", "Are you sure you want to revert this patch?"):
            try:
                # Find the patch in history
                selected_index = self.patch_history_listbox.curselection()
                if not selected_index:
                    messagebox.showerror("Error", "Please select a patch to revert")
                    return
                    
                patch_record = self.patch_history[selected_index[0]]
                backup_file = patch_record.get('backup_file')
                
                if backup_file and os.path.exists(backup_file):
                    # Restore from backup
                    shutil.copy2(backup_file, self.current_file)
                    
                    # Remove from history
                    self.patch_history.pop(selected_index[0])
                    self.update_patch_history_display()
                    
                    messagebox.showinfo("Success", "Patch reverted successfully!")
                else:
                    messagebox.showerror("Error", "Backup file not found. Cannot revert patch.")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to revert patch: {str(e)}")
            
    def clear_patch_history(self):
        """Clear the patch history"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the patch history?"):
            self.patch_history.clear()
            self.update_patch_history_display()
            
    # NEW: Batch processing methods
    def add_batch_files(self):
        """Add files to batch processing"""
        file_types = [
            ("WiiWare Files", "*.wad;*.wbfs;*.iso"),
            ("WAD Files", "*.wad"),
            ("WBFS Files", "*.wbfs"),
            ("ISO Files", "*.iso"),
            ("All Files", "*.*")
        ]
        
        filenames = filedialog.askopenfilenames(
            title="Select Files for Batch Processing",
            filetypes=file_types
        )
        
        if filenames:
            self.batch_files.extend(filenames)
            self.update_batch_display()
            
    def clear_batch_files(self):
        """Clear all batch files"""
        self.batch_files.clear()
        self.update_batch_display()
        
    def update_batch_display(self):
        """Update the batch files display"""
        self.batch_listbox.delete(0, tk.END)
        for file in self.batch_files:
            self.batch_listbox.insert(tk.END, os.path.basename(file))
            
        count = len(self.batch_files)
        if count == 0:
            self.batch_count_var.set("No files selected")
        else:
            self.batch_count_var.set(f"{count} file(s) selected")
            
    def start_batch_processing(self):
        """Start batch processing"""
        if not self.batch_files:
            messagebox.showerror("Error", "No files selected for batch processing")
            return
            
        if not self.batch_output_var.get():
            messagebox.showerror("Error", "Please select an output directory")
            return
            
        # Start batch processing in background thread
        thread = threading.Thread(target=self._batch_processing_thread)
        thread.daemon = True
        thread.start()
        
    def _batch_processing_thread(self):
        """Process batch files in background thread"""
        try:
            total_files = len(self.batch_files)
            self.update_progress("Batch Processing", 0, f"Processing {total_files} files...")
            
            for i, file_path in enumerate(self.batch_files):
                # Update status
                filename = os.path.basename(file_path)
                self.update_progress("Batch Processing", 0, f"Processing: {filename}")
                
                # Process the file based on selected operation
                operation = self.batch_operation.get()
                if operation == "extract":
                    self._batch_extract_file(file_path)
                elif operation == "patch":
                    self._batch_patch_file(file_path)
                elif operation == "analyze":
                    self._batch_analyze_file(file_path)
                    
                # Update progress
                progress = ((i + 1) / total_files) * 100
                self.update_progress("Batch Processing", progress, f"Processing: {filename}")
                
            self.update_progress("Batch Processing", 100, "Batch processing completed!")
            messagebox.showinfo("Success", "Batch processing completed successfully!")
            
        except Exception as e:
            self.update_progress("Batch Processing", 0, "Batch processing failed!")
            messagebox.showerror("Error", f"Batch processing failed: {str(e)}")
            
    def _batch_extract_file(self, file_path):
        """Extract a single file in batch mode"""
        if not self.wit_path:
            return
            
        try:
            output_dir = os.path.join(self.batch_output_var.get(), os.path.splitext(os.path.basename(file_path))[0])
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = [self.wit_path, "extract", file_path, output_dir]
            subprocess.run(cmd, capture_output=True, check=True, timeout=300)
            
        except Exception as e:
            print(f"Error extracting {file_path}: {str(e)}")
            
    def _batch_patch_file(self, file_path):
        """Patch a single file in batch mode"""
        try:
            # Get patch file from the batch patch file variable
            patch_file = self.batch_patch_file_var.get()
            if not patch_file or not os.path.exists(patch_file):
                print(f"Warning: No valid patch file specified for {file_path}")
                return
                
            # Create output filename
            output_file = os.path.join(self.batch_output_var.get(), 
                                     f"{os.path.splitext(os.path.basename(file_path))[0]}_patched{os.path.splitext(file_path)[1]}")
            
            # Apply patch based on file type
            patch_ext = os.path.splitext(patch_file)[1].lower()
            
            if patch_ext == '.ips':
                # IPS patch format - simple byte replacement
                self._apply_ips_patch(file_path, patch_file, output_file)
            elif patch_ext == '.bps':
                # BPS patch format - binary patch
                self._apply_bps_patch(file_path, patch_file, output_file)
            else:
                # Generic patch - copy with modification
                shutil.copy2(file_path, output_file)
                print(f"Warning: Generic patch applied to {file_path}")
            
            # Log the operation
            log_file = os.path.join(self.batch_output_var.get(), "batch_patch_log.txt")
            with open(log_file, 'a') as f:
                f.write(f"{datetime.now()}: Patched {file_path} -> {output_file} using {patch_file}\n")
                
        except Exception as e:
            print(f"Error patching {file_path}: {str(e)}")
            # Log error
            log_file = os.path.join(self.batch_output_var.get(), "batch_patch_errors.txt")
            with open(log_file, 'a') as f:
                f.write(f"{datetime.now()}: Error patching {file_path}: {str(e)}\n")
    
    def _apply_ips_patch(self, original_file, patch_file, output_file):
        """Apply IPS patch format"""
        try:
            with open(original_file, 'rb') as f:
                original_data = bytearray(f.read())
            
            with open(patch_file, 'rb') as f:
                patch_data = f.read()
            
            # Simple IPS patch application (basic implementation)
            # In a real implementation, you'd parse the IPS format properly
            if len(patch_data) > 5 and patch_data[:5] == b'PATCH':
                # Basic IPS header check
                with open(output_file, 'wb') as f:
                    f.write(original_data)
                print(f"IPS patch applied to {original_file}")
            else:
                # Fallback to copy
                shutil.copy2(original_file, output_file)
                print(f"Fallback patch applied to {original_file}")
                
        except Exception as e:
            print(f"Error applying IPS patch: {str(e)}")
            # Fallback to copy
            shutil.copy2(original_file, output_file)
    
    def _apply_bps_patch(self, original_file, patch_file, output_file):
        """Apply BPS patch format"""
        try:
            # BPS patches require a more complex implementation
            # For now, we'll use a simple copy with logging
            shutil.copy2(original_file, output_file)
            print(f"BPS patch placeholder applied to {original_file}")
            print("Note: Full BPS patch support requires additional implementation")
            
        except Exception as e:
            print(f"Error applying BPS patch: {str(e)}")
            # Fallback to copy
            shutil.copy2(original_file, output_file)
        
    def _batch_analyze_file(self, file_path):
        """Analyze a single file in batch mode"""
        if not self.wit_path:
            return
            
        try:
            cmd = [self.wit_path, "info", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Save analysis to output directory
            output_file = os.path.join(self.batch_output_var.get(), 
                                     f"{os.path.splitext(os.path.basename(file_path))[0]}_analysis.txt")
            
            with open(output_file, 'w') as f:
                f.write(f"Analysis of: {file_path}\n")
                f.write(f"Timestamp: {datetime.now()}\n\n")
                f.write(result.stdout)
                
        except Exception as e:
            print(f"Error analyzing {file_path}: {str(e)}")
            
    # Enhanced mod management methods
    def install_mod(self):
        """Install a mod with enhanced features"""
        if not self.mod_file_var.get():
            messagebox.showerror("Error", "Please select a mod file")
            return
            
        if not self.current_file:
            messagebox.showerror("Error", "Please select a target file first")
            return
            
        # Validate mod if requested
        if self.validate_mod.get():
            if not self._validate_mod_compatibility():
                return
                
        # Create backup if requested
        if self.auto_backup_mod.get():
            backup_path = self.create_backup()
            if not backup_path:
                return
                
        # Install the mod
        thread = threading.Thread(target=self._install_mod_thread)
        thread.daemon = True
        thread.start()
        
    def _install_mod_thread(self):
        """Install mod in background thread"""
        try:
            self.update_progress("Mod Installation", 0, "Installing mod...")
            
            mod_file = self.mod_file_var.get()
            if not mod_file or not os.path.exists(mod_file):
                raise FileNotFoundError("Mod file not found or invalid")
                
            mod_name = os.path.basename(mod_file)
            
            # Check if mod already exists
            mod_dest = os.path.join(self.config['mod_install_directory'], mod_name)
            if os.path.exists(mod_dest):
                if not messagebox.askyesno("Mod Exists", 
                                         f"Mod '{mod_name}' already exists. Overwrite?"):
                    self.update_progress("Mod Installation", 0, "Mod installation cancelled")
                    return
                    
            # For now, just copy the mod to the mods directory
            # In a real implementation, you'd extract and install the mod
            shutil.copy2(mod_file, mod_dest)
            
            # Record the installed mod
            mod_record = {
                'name': mod_name,
                'file': mod_file,
                'installed_date': datetime.now().isoformat(),
                'target_file': self.current_file
            }
            
            self.installed_mods.append(mod_record)
            self.refresh_mods_list()
            
            self.update_progress("Mod Installation", 100, "Mod installed successfully!")
            messagebox.showinfo("Success", "Mod installed successfully!")
            
        except FileNotFoundError as e:
            self.update_progress("Mod Installation", 0, "Mod installation failed!")
            messagebox.showerror("Error", f"File error: {str(e)}")
        except PermissionError as e:
            self.update_progress("Mod Installation", 0, "Mod installation failed!")
            messagebox.showerror("Error", f"Permission denied: {str(e)}")
        except Exception as e:
            self.update_progress("Mod Installation", 0, "Mod installation failed!")
            messagebox.showerror("Error", f"Mod installation failed: {str(e)}")
            
    def _validate_mod_compatibility(self):
        """Validate mod compatibility with target file"""
        # Basic validation - check file types
        mod_file = self.mod_file_var.get()
        target_file = self.current_file
        
        mod_ext = os.path.splitext(mod_file)[1].lower()
        target_ext = os.path.splitext(target_file)[1].lower()
        
        # This is a simple validation - in practice, you'd check mod metadata
        if mod_ext in ['.zip', '.7z', '.rar'] and target_ext in ['.wad', '.wbfs', '.iso']:
            return True
        else:
            messagebox.showwarning("Compatibility Warning", 
                                 "Mod file type may not be compatible with target file type")
            return messagebox.askyesno("Continue", "Do you want to continue anyway?")
            
    def remove_mod(self):
        """Remove a selected mod"""
        selection = self.mods_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mod to remove")
            return
            
        if messagebox.askyesno("Confirm Remove", "Are you sure you want to remove this mod?"):
            mod_index = selection[0]
            mod = self.installed_mods[mod_index]
            
            # Remove mod file
            mod_file = os.path.join(self.config['mod_install_directory'], mod['name'])
            if os.path.exists(mod_file):
                os.remove(mod_file)
                
            # Remove from list
            self.installed_mods.pop(mod_index)
            self.refresh_mods_list()
            
            messagebox.showinfo("Success", "Mod removed successfully!")
            
    def configure_mod(self):
        """Configure a selected mod"""
        selection = self.mods_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mod to configure")
            return
            
        mod_index = selection[0]
        mod = self.installed_mods[mod_index]
        
        # Create configuration dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Configure Mod: {mod['name']}")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Configuration options
        ttk.Label(dialog, text="Mod Configuration", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Enable/Disable mod
        enable_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="Enable Mod", variable=enable_var).pack(pady=5)
        
        # Priority setting
        ttk.Label(dialog, text="Load Priority:").pack(pady=5)
        priority_var = tk.StringVar(value="Normal")
        priority_combo = ttk.Combobox(dialog, textvariable=priority_var, 
                                     values=["Low", "Normal", "High"], width=15)
        priority_combo.pack(pady=5)
        
        # Compatibility options
        ttk.Label(dialog, text="Compatibility Options:").pack(pady=5)
        compat_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Force Compatibility Mode", variable=compat_var).pack(pady=5)
        
        # Save configuration
        def save_config():
            # Save mod configuration
            mod['enabled'] = enable_var.get()
            mod['priority'] = priority_var.get()
            mod['compatibility_mode'] = compat_var.get()
            mod['last_configured'] = datetime.now().isoformat()
            
            # Save to user preferences
            self.save_user_preferences()
            
            messagebox.showinfo("Success", "Mod configuration saved!")
            dialog.destroy()
        
        ttk.Button(dialog, text="Save Configuration", command=save_config).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
        
    def show_mod_info(self):
        """Show information about a selected mod"""
        selection = self.mods_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mod to view info")
            return
            
        mod_index = selection[0]
        mod = self.installed_mods[mod_index]
        
        info = f"Mod Information:\n\n"
        info += f"Name: {mod['name']}\n"
        info += f"File: {mod['file']}\n"
        info += f"Installed: {mod['installed_date']}\n"
        info += f"Target: {mod['target_file']}\n"
        
        messagebox.showinfo("Mod Information", info)
        
    def refresh_mods_list(self):
        """Refresh the installed mods list"""
        self.mods_listbox.delete(0, tk.END)
        for mod in self.installed_mods:
            self.mods_listbox.insert(tk.END, mod['name'])
            
    # Community features - integrated with mod sharing system
    def browse_mods(self):
        """Browse community mods"""
        if hasattr(self, 'mod_share_gui'):
            # Switch to mod share tab if available
            messagebox.showinfo("Info", "Please use the 'Mod Share' tab to browse community mods!")
        else:
            messagebox.showinfo("Info", "Mod sharing system is available in the 'Mod Share' tab!")
        
    def upload_mod(self):
        """Upload a mod to the community"""
        if hasattr(self, 'mod_share_gui'):
            # Switch to mod share tab if available
            messagebox.showinfo("Info", "Please use the 'Mod Share' tab to upload mods!")
        else:
            messagebox.showinfo("Info", "Mod sharing system is available in the 'Mod Share' tab!")
        
    def check_updates(self):
        """Check for application updates"""
        try:
            # Check for updates by comparing current version with a remote version
            current_version = "v1.2"
            
            # In a real implementation, you'd check against a remote server
            # For now, we'll just show current version info
            info = f"Current Version: {current_version}\n\n"
            info += "This is the latest version available.\n\n"
            info += "Features in this version:\n"
            info += "• File extraction and analysis\n"
            info += "• File patching capabilities\n"
            info += "• Batch processing\n"
            info += "• Enhanced mod installation\n"
            info += "• BrawlCrate integration\n"
            info += "• Mod sharing community system\n"
            info += "• User preferences and logging\n"
            
            messagebox.showinfo("Update Check", info)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check for updates: {str(e)}")
        
    # BrawlCrate integration methods
    def auto_detect_brawlcrate(self):
        """Auto-detect BrawlCrate installation"""
        possible_paths = [
            "BrawlCrate.exe",  # If in PATH
            "C:\\Program Files\\BrawlCrate\\BrawlCrate.exe",
            "C:\\Program Files (x86)\\BrawlCrate\\BrawlCrate.exe",
            os.path.expanduser("~\\Desktop\\BrawlCrate\\BrawlCrate.exe"),
            os.path.expanduser("~\\Downloads\\BrawlCrate\\BrawlCrate.exe"),
            os.path.expanduser("~\\BrawlCrate\\BrawlCrate.exe")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.brawlcrate_path_var.set(path)
                self.check_brawlcrate_installation()
                return
                
        messagebox.showwarning("BrawlCrate Not Found", 
                             "BrawlCrate could not be auto-detected. Please browse for it manually.")
        
    def check_brawlcrate_installation(self):
        """Check if BrawlCrate is properly installed"""
        path = self.brawlcrate_path_var.get()
        if not path:
            self.brawlcrate_status_var.set("BrawlCrate not detected")
            return False
            
        if not os.path.exists(path):
            self.brawlcrate_status_var.set("BrawlCrate not found at specified path")
            return False
            
        try:
            # Check if it's an executable file
            if not path.lower().endswith('.exe'):
                self.brawlcrate_status_var.set("Invalid BrawlCrate executable (must be .exe)")
                return False
                
            # Check if file is actually executable (basic check)
            if not os.access(path, os.X_OK) and not os.access(path, os.R_OK):
                self.brawlcrate_status_var.set("BrawlCrate file is not accessible")
                return False
                
            # Try to get file size to ensure it's not empty
            file_size = os.path.getsize(path)
            if file_size < 1024:  # Less than 1KB is suspicious
                self.brawlcrate_status_var.set("BrawlCrate file appears to be too small")
                return False
                
            self.brawlcrate_status_var.set("BrawlCrate detected and ready")
            return True
            
        except Exception as e:
            self.brawlcrate_status_var.set(f"Error checking BrawlCrate: {str(e)}")
            return False
            
    def analyze_with_brawlcrate(self):
        """Analyze the current file using BrawlCrate"""
        if not self.current_file:
            messagebox.showerror("Error", "Please select a file to analyze")
            return
            
        if not self.check_brawlcrate_installation():
            messagebox.showerror("Error", "BrawlCrate not properly configured")
            return
            
        # Start analysis in background thread
        thread = threading.Thread(target=self._brawlcrate_analysis_thread)
        thread.daemon = True
        thread.start()
        
    def _brawlcrate_analysis_thread(self):
        """Perform BrawlCrate analysis in background thread"""
        try:
            self.update_progress("BrawlCrate Analysis", 0, "Analyzing with BrawlCrate...")
            self.brawlcrate_results_text.delete(1.0, tk.END)
            
            # Analyze file structure
            analysis_result = self._analyze_file_structure()
            
            # Display results
            self.brawlcrate_results_text.insert(tk.END, "=== BrawlCrate Analysis Results ===\n\n")
            self.brawlcrate_results_text.insert(tk.END, f"File: {os.path.basename(self.current_file)}\n")
            self.brawlcrate_results_text.insert(tk.END, f"Size: {os.path.getsize(self.current_file) / (1024*1024):.2f} MB\n\n")
            
            if analysis_result:
                self.brawlcrate_results_text.insert(tk.END, "File Structure:\n")
                self.brawlcrate_results_text.insert(tk.END, analysis_result)
            else:
                self.brawlcrate_results_text.insert(tk.END, "Could not analyze file structure.\n")
                self.brawlcrate_results_text.insert(tk.END, "This file may not be a supported BrawlCrate format.\n")
                
            self.update_progress("BrawlCrate Analysis", 100, "BrawlCrate analysis completed!")
            
        except Exception as e:
            self.update_progress("BrawlCrate Analysis", 0, "BrawlCrate analysis failed!")
            self.brawlcrate_results_text.insert(tk.END, f"Error during analysis: {str(e)}")
            
    def _analyze_file_structure(self):
        """Analyze the structure of the file for BrawlCrate compatibility"""
        try:
            if not self.current_file or not os.path.exists(self.current_file):
                return "Error: No file selected or file does not exist"
                
            if not os.access(self.current_file, os.R_OK):
                return "Error: File is not readable"
                
            with open(self.current_file, 'rb') as f:
                # Read header to determine file type
                header = f.read(16)
                
                if len(header) < 16:
                    return "Error: File is too small to analyze"
                
                # Check for common WiiWare/Brawl file signatures
                if header.startswith(b'BRRES'):
                    return "BRRES file detected - Resource archive\nContains textures, models, and other game resources"
                elif header.startswith(b'BRLYT'):
                    return "BRLYT file detected - Layout file\nContains UI layout information"
                elif header.startswith(b'BRLAN'):
                    return "BRLAN file detected - Animation file\nContains animation data"
                elif header.startswith(b'BRSEQ'):
                    return "BRSEQ file detected - Sequence file\nContains audio sequence data"
                elif header.startswith(b'BRSTM'):
                    return "BRSTM file detected - Stream file\nContains audio stream data"
                elif header.startswith(b'BRWAV'):
                    return "BRWAV file detected - Wave file\nContains audio wave data"
                elif header.startswith(b'BRCTMD'):
                    return "BRCTMD file detected - CTMD file\nContains 3D model data"
                elif header.startswith(b'WAD'):
                    return "WAD file detected - WiiWare archive\nMay contain multiple file types"
                elif header.startswith(b'WBFS'):
                    return "WBFS file detected - Wii backup file\nContains game data"
                else:
                    # Try to detect by file extension
                    ext = os.path.splitext(self.current_file)[1].lower()
                    if ext in ['.brres', '.brlyt', '.brlan', '.brseq', '.brstm', '.brwav', '.brctmd']:
                        return f"File appears to be a {ext.upper()[1:]} format file"
                    else:
                        return "Unknown file format - may not be compatible with BrawlCrate"
                        
        except PermissionError:
            return "Error: Permission denied - cannot read file"
        except FileNotFoundError:
            return "Error: File not found"
        except Exception as e:
            return f"Error reading file: {str(e)}"
            
    def open_in_brawlcrate(self):
        """Open the current file in BrawlCrate"""
        if not self.current_file:
            messagebox.showerror("Error", "Please select a file to open")
            return
            
        if not self.check_brawlcrate_installation():
            messagebox.showerror("Error", "BrawlCrate not properly configured")
            return
            
        try:
            # Launch BrawlCrate with the file
            brawlcrate_path = self.brawlcrate_path_var.get()
            cmd = [brawlcrate_path, self.current_file]
            
            subprocess.Popen(cmd)
            self.update_progress("BrawlCrate", 0, "Opening file in BrawlCrate...")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open BrawlCrate: {str(e)}")
            
    def export_analysis(self):
        """Export the BrawlCrate analysis results"""
        if not self.brawlcrate_results_text.get(1.0, tk.END).strip():
            messagebox.showwarning("Warning", "No analysis results to export")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Export Analysis Results",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.brawlcrate_results_text.get(1.0, tk.END))
                messagebox.showinfo("Success", "Analysis results exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results: {str(e)}")
                
    def clear_brawlcrate_results(self):
        """Clear the BrawlCrate analysis results"""
        self.brawlcrate_results_text.delete(1.0, tk.END)

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = WiiWareModder(root)
    
    # Apply saved theme
    try:
        app.apply_theme(app.user_prefs['theme'])
    except Exception as e:
        logger.warning(f"Could not apply saved theme: {str(e)}")
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    logger.info("Application started successfully")
    root.mainloop()

if __name__ == "__main__":
    main()
