import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import shutil
from datetime import datetime
from mod_share_database import ModShareDatabase
import logging

class ModShareGUI:
    def __init__(self, parent, database):
        self.parent = parent
        self.database = database
        self.logger = logging.getLogger(__name__)
        self.current_user = None
        self.current_mods = []
        self.current_page = 0
        self.mods_per_page = 10
        
        # Create mods directory if it doesn't exist
        self.mods_dir = "shared_mods"
        os.makedirs(self.mods_dir, exist_ok=True)
        
        self.create_widgets()
        self.refresh_mods_list()
    
    def create_widgets(self):
        """Create the mod sharing interface"""
        # Main frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Login/User frame
        self.create_user_frame()
        
        # Search and filter frame
        self.create_search_frame()
        
        # Mods display frame
        self.create_mods_display_frame()
        
        # Upload frame (initially hidden)
        self.create_upload_frame()
        
        # Comments frame (initially hidden)
        self.create_comments_frame()
    
    def create_user_frame(self):
        """Create the user login/registration frame"""
        self.user_frame = ttk.LabelFrame(self.main_frame, text="Account", padding=10)
        self.user_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Login frame
        self.login_frame = ttk.Frame(self.user_frame)
        self.login_frame.pack(fill=tk.X)
        
        ttk.Label(self.login_frame, text="Username/Email:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self.login_frame, textvariable=self.username_var, width=20)
        self.username_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(self.login_frame, text="Password:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.login_frame, textvariable=self.password_var, show="*", width=15)
        self.password_entry.grid(row=0, column=3, padx=(0, 10))
        
        self.login_button = ttk.Button(self.login_frame, text="Login", command=self.login)
        self.login_button.grid(row=0, column=4, padx=(0, 5))
        
        self.register_button = ttk.Button(self.login_frame, text="Register", command=self.show_register_dialog)
        self.register_button.grid(row=0, column=5, padx=(0, 5))
        
        # User info frame (initially hidden)
        self.user_info_frame = ttk.Frame(self.user_frame)
        
        self.user_info_label = ttk.Label(self.user_info_frame, text="")
        self.user_info_label.pack(side=tk.LEFT)
        
        self.logout_button = ttk.Button(self.user_info_frame, text="Logout", command=self.logout)
        self.logout_button.pack(side=tk.RIGHT)
        
        self.upload_button = ttk.Button(self.user_info_frame, text="Upload Mod", command=self.show_upload_frame)
        self.upload_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        self.my_mods_button = ttk.Button(self.user_info_frame, text="My Mods", command=self.show_my_mods)
        self.my_mods_button.pack(side=tk.RIGHT, padx=(0, 10))
    
    def create_search_frame(self):
        """Create the search and filter frame"""
        self.search_frame = ttk.LabelFrame(self.main_frame, text="Search & Filter", padding=10)
        self.search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Search
        ttk.Label(self.search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # Category filter
        ttk.Label(self.search_frame, text="Category:").pack(side=tk.LEFT)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(self.search_frame, textvariable=self.category_var, width=15)
        self.category_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        # Sort options
        ttk.Label(self.search_frame, text="Sort by:").pack(side=tk.LEFT)
        self.sort_var = tk.StringVar(value="upload_date")
        self.sort_combo = ttk.Combobox(self.search_frame, textvariable=self.sort_var, 
                                      values=["upload_date", "download_count", "rating", "title"], width=12)
        self.sort_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        # Search button
        self.search_button = ttk.Button(self.search_frame, text="Search", command=self.search_mods)
        self.search_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Load categories
        self.load_categories()
    
    def create_mods_display_frame(self):
        """Create the mods display frame"""
        self.mods_frame = ttk.LabelFrame(self.main_frame, text="Available Mods", padding=10)
        self.mods_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Mods list
        self.mods_tree = ttk.Treeview(self.mods_frame, columns=("title", "author", "rating", "downloads", "date"), 
                                     show="headings", height=15)
        
        self.mods_tree.heading("title", text="Title")
        self.mods_tree.heading("author", text="Author")
        self.mods_tree.heading("rating", text="Rating")
        self.mods_tree.heading("downloads", text="Downloads")
        self.mods_tree.heading("date", text="Upload Date")
        
        self.mods_tree.column("title", width=200)
        self.mods_tree.column("author", width=100)
        self.mods_tree.column("rating", width=80)
        self.mods_tree.column("downloads", width=80)
        self.mods_tree.column("date", width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.mods_frame, orient=tk.VERTICAL, command=self.mods_tree.yview)
        self.mods_tree.configure(yscrollcommand=scrollbar.set)
        
        self.mods_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to view mod details
        self.mods_tree.bind("<Double-1>", self.view_mod_details)
        
        # Pagination frame
        self.pagination_frame = ttk.Frame(self.mods_frame)
        self.pagination_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.prev_button = ttk.Button(self.pagination_frame, text="Previous", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT)
        
        self.page_label = ttk.Label(self.pagination_frame, text="Page 1")
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        self.next_button = ttk.Button(self.pagination_frame, text="Next", command=self.next_page)
        self.next_button.pack(side=tk.LEFT)
    
    def create_upload_frame(self):
        """Create the mod upload frame"""
        self.upload_frame = ttk.LabelFrame(self.main_frame, text="Upload Mod", padding=10)
        
        # Title
        ttk.Label(self.upload_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.upload_title_var = tk.StringVar()
        ttk.Entry(self.upload_frame, textvariable=self.upload_title_var, width=50).grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Description
        ttk.Label(self.upload_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.upload_desc_text = scrolledtext.ScrolledText(self.upload_frame, width=50, height=5)
        self.upload_desc_text.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # File selection
        ttk.Label(self.upload_frame, text="Mod File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.upload_file_var = tk.StringVar()
        ttk.Entry(self.upload_frame, textvariable=self.upload_file_var, width=40).grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Button(self.upload_frame, text="Browse", command=self.browse_upload_file).grid(row=2, column=2, padx=(5, 0), pady=5)
        
        # Game compatibility
        ttk.Label(self.upload_frame, text="Game Compatibility:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.upload_game_var = tk.StringVar()
        ttk.Entry(self.upload_frame, textvariable=self.upload_game_var, width=30).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Version
        ttk.Label(self.upload_frame, text="Version:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.upload_version_var = tk.StringVar(value="1.0")
        ttk.Entry(self.upload_frame, textvariable=self.upload_version_var, width=10).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Tags
        ttk.Label(self.upload_frame, text="Tags:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.upload_tags_var = tk.StringVar()
        ttk.Entry(self.upload_frame, textvariable=self.upload_tags_var, width=30).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Public/Private
        self.upload_public_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.upload_frame, text="Public", variable=self.upload_public_var).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # Upload button
        ttk.Button(self.upload_frame, text="Upload Mod", command=self.upload_mod).grid(row=7, column=1, sticky=tk.W, pady=10)
        ttk.Button(self.upload_frame, text="Cancel", command=self.hide_upload_frame).grid(row=7, column=2, padx=(5, 0), pady=10)
    
    def create_comments_frame(self):
        """Create the comments frame"""
        self.comments_frame = ttk.LabelFrame(self.main_frame, text="Comments & Ratings", padding=10)
        
        # Comments display
        self.comments_text = scrolledtext.ScrolledText(self.comments_frame, width=60, height=10)
        self.comments_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Add comment frame
        comment_input_frame = ttk.Frame(self.comments_frame)
        comment_input_frame.pack(fill=tk.X)
        
        ttk.Label(comment_input_frame, text="Your Comment:").pack(side=tk.LEFT)
        self.comment_var = tk.StringVar()
        ttk.Entry(comment_input_frame, textvariable=self.comment_var, width=40).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(comment_input_frame, text="Rating:").pack(side=tk.LEFT)
        self.rating_var = tk.IntVar(value=5)
        rating_combo = ttk.Combobox(comment_input_frame, textvariable=self.rating_var, 
                                   values=[1, 2, 3, 4, 5], width=5)
        rating_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(comment_input_frame, text="Add Comment", command=self.add_comment).pack(side=tk.LEFT)
        ttk.Button(comment_input_frame, text="Close", command=self.hide_comments_frame).pack(side=tk.RIGHT)
    
    def load_categories(self):
        """Load categories into the combo box"""
        try:
            categories = self.database.get_categories()
            self.category_combo['values'] = ['All Categories'] + [cat['name'] for cat in categories]
            self.category_combo.set('All Categories')
        except Exception as e:
            self.logger.error(f"Failed to load categories: {e}")
    
    def login(self):
        """Handle user login"""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        try:
            user = self.database.authenticate_user(username, password)
            if user:
                self.current_user = user
                self.show_user_info()
                messagebox.showinfo("Success", f"Welcome back, {user['username']}!")
                self.refresh_mods_list()
            else:
                messagebox.showerror("Error", "Invalid username or password")
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            messagebox.showerror("Error", f"Login failed: {str(e)}")
    
    def show_register_dialog(self):
        """Show user registration dialog"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Register Account")
        dialog.geometry("400x300")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.parent.winfo_rootx() + 50, self.parent.winfo_rooty() + 50))
        
        # Registration form
        ttk.Label(dialog, text="Username:").pack(pady=5)
        username_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=username_var, width=30).pack(pady=5)
        
        ttk.Label(dialog, text="Email:").pack(pady=5)
        email_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=email_var, width=30).pack(pady=5)
        
        ttk.Label(dialog, text="Password:").pack(pady=5)
        password_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=password_var, show="*", width=30).pack(pady=5)
        
        ttk.Label(dialog, text="Confirm Password:").pack(pady=5)
        confirm_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=confirm_var, show="*", width=30).pack(pady=5)
        
        def register():
            username = username_var.get().strip()
            email = email_var.get().strip()
            password = password_var.get()
            confirm = confirm_var.get()
            
            if not all([username, email, password, confirm]):
                messagebox.showerror("Error", "All fields are required")
                return
            
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match")
                return
            
            if len(password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters")
                return
            
            try:
                user_id = self.database.create_user(username, email, password)
                messagebox.showinfo("Success", "Account created successfully! You can now login.")
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
            except Exception as e:
                self.logger.error(f"Registration failed: {e}")
                messagebox.showerror("Error", f"Registration failed: {str(e)}")
        
        ttk.Button(dialog, text="Register", command=register).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def logout(self):
        """Handle user logout"""
        self.current_user = None
        self.hide_user_info()
        self.username_var.set("")
        self.password_var.set("")
        messagebox.showinfo("Success", "Logged out successfully")
    
    def show_user_info(self):
        """Show user information after login"""
        self.login_frame.pack_forget()
        self.user_info_frame.pack(fill=tk.X)
        self.user_info_label.config(text=f"Welcome, {self.current_user['username']}!")
    
    def hide_user_info(self):
        """Hide user information after logout"""
        self.user_info_frame.pack_forget()
        self.login_frame.pack(fill=tk.X)
    
    def search_mods(self):
        """Search and filter mods"""
        self.current_page = 0
        self.refresh_mods_list()
    
    def refresh_mods_list(self):
        """Refresh the mods list display"""
        try:
            # Clear current list
            for item in self.mods_tree.get_children():
                self.mods_tree.delete(item)
            
            # Get search parameters
            search_query = self.search_var.get().strip()
            category_name = self.category_var.get()
            sort_by = self.sort_var.get()
            
            # Get category ID if not "All Categories"
            category_id = None
            if category_name and category_name != "All Categories":
                categories = self.database.get_categories()
                for cat in categories:
                    if cat['name'] == category_name:
                        category_id = cat['id']
                        break
            
            # Get mods
            mods = self.database.get_mods(
                limit=self.mods_per_page,
                offset=self.current_page * self.mods_per_page,
                category_id=category_id,
                search_query=search_query if search_query else None,
                sort_by=sort_by,
                sort_order="DESC"
            )
            
            # Display mods
            for mod in mods:
                rating_text = f"{mod['rating']:.1f} ({mod['rating_count']})" if mod['rating'] > 0 else "No ratings"
                date_text = mod['upload_date'][:10] if mod['upload_date'] else "Unknown"
                
                self.mods_tree.insert("", tk.END, values=(
                    mod['title'],
                    mod['author_name'],
                    rating_text,
                    mod['download_count'],
                    date_text
                ), tags=(mod['id'],))
            
            # Update pagination
            self.update_pagination()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh mods list: {e}")
            messagebox.showerror("Error", f"Failed to load mods: {str(e)}")
    
    def update_pagination(self):
        """Update pagination controls"""
        self.page_label.config(text=f"Page {self.current_page + 1}")
        self.prev_button.config(state=tk.DISABLED if self.current_page == 0 else tk.NORMAL)
        
        # Check if there are more pages
        try:
            next_mods = self.database.get_mods(
                limit=self.mods_per_page,
                offset=(self.current_page + 1) * self.mods_per_page
            )
            self.next_button.config(state=tk.NORMAL if next_mods else tk.DISABLED)
        except:
            self.next_button.config(state=tk.DISABLED)
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_mods_list()
    
    def next_page(self):
        """Go to next page"""
        self.current_page += 1
        self.refresh_mods_list()
    
    def view_mod_details(self, event):
        """View detailed information about a mod"""
        selection = self.mods_tree.selection()
        if not selection:
            return
        
        mod_id = self.mods_tree.item(selection[0], "tags")[0]
        
        try:
            mod_details = self.database.get_mod_details(mod_id)
            if not mod_details:
                messagebox.showerror("Error", "Mod not found")
                return
            
            self.show_mod_details_dialog(mod_details)
            
        except Exception as e:
            self.logger.error(f"Failed to get mod details: {e}")
            messagebox.showerror("Error", f"Failed to load mod details: {str(e)}")
    
    def show_mod_details_dialog(self, mod_details):
        """Show mod details in a dialog"""
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Mod Details: {mod_details['title']}")
        dialog.geometry("600x500")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.parent.winfo_rootx() + 50, self.parent.winfo_rooty() + 50))
        
        # Mod information
        info_frame = ttk.LabelFrame(dialog, text="Mod Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"Title: {mod_details['title']}", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Author: {mod_details['author_name']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Version: {mod_details['version']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Game Compatibility: {mod_details['game_compatibility']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Rating: {mod_details['rating']:.1f}/5.0 ({mod_details['rating_count']} ratings)").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Downloads: {mod_details['download_count']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Upload Date: {mod_details['upload_date']}").pack(anchor=tk.W)
        
        if mod_details['tags']:
            ttk.Label(info_frame, text=f"Tags: {mod_details['tags']}").pack(anchor=tk.W)
        
        # Description
        desc_frame = ttk.LabelFrame(dialog, text="Description", padding=10)
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        desc_text = scrolledtext.ScrolledText(desc_frame, wrap=tk.WORD, height=8)
        desc_text.pack(fill=tk.BOTH, expand=True)
        desc_text.insert(tk.END, mod_details['description'] or "No description provided")
        desc_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Download", command=lambda: self.download_mod(mod_details)).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="View Comments", command=lambda: self.show_comments(mod_details['id'])).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def download_mod(self, mod_details):
        """Download a mod"""
        try:
            # Record the download
            self.database.record_download(
                mod_details['id'],
                user_id=self.current_user['id'] if self.current_user else None
            )
            
            # Copy file to downloads directory
            downloads_dir = "downloads"
            os.makedirs(downloads_dir, exist_ok=True)
            
            source_path = mod_details['file_path']
            filename = os.path.basename(source_path)
            dest_path = os.path.join(downloads_dir, filename)
            
            shutil.copy2(source_path, dest_path)
            
            messagebox.showinfo("Success", f"Mod downloaded successfully!\nSaved to: {dest_path}")
            
            # Refresh the mods list to update download count
            self.refresh_mods_list()
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            messagebox.showerror("Error", f"Download failed: {str(e)}")
    
    def show_comments(self, mod_id):
        """Show comments for a mod"""
        self.current_mod_id = mod_id
        self.refresh_comments()
        self.comments_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
    
    def refresh_comments(self):
        """Refresh the comments display"""
        try:
            mod_details = self.database.get_mod_details(self.current_mod_id)
            if not mod_details:
                return
            
            # Clear comments
            self.comments_text.config(state=tk.NORMAL)
            self.comments_text.delete(1.0, tk.END)
            
            # Display comments
            for comment in mod_details['comments']:
                rating_text = f"Rating: {comment['rating']}/5" if comment['rating'] else "No rating"
                date_text = comment['created_date'][:19] if comment['created_date'] else "Unknown"
                
                self.comments_text.insert(tk.END, f"By {comment['username']} on {date_text}\n")
                self.comments_text.insert(tk.END, f"{rating_text}\n")
                self.comments_text.insert(tk.END, f"{comment['comment']}\n")
                self.comments_text.insert(tk.END, "-" * 50 + "\n\n")
            
            self.comments_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.logger.error(f"Failed to refresh comments: {e}")
    
    def add_comment(self):
        """Add a comment to the current mod"""
        if not self.current_user:
            messagebox.showerror("Error", "You must be logged in to comment")
            return
        
        comment = self.comment_var.get().strip()
        rating = self.rating_var.get()
        
        if not comment:
            messagebox.showerror("Error", "Please enter a comment")
            return
        
        try:
            self.database.add_comment(self.current_mod_id, self.current_user['id'], comment, rating)
            self.comment_var.set("")
            self.refresh_comments()
            messagebox.showinfo("Success", "Comment added successfully!")
        except Exception as e:
            self.logger.error(f"Failed to add comment: {e}")
            messagebox.showerror("Error", f"Failed to add comment: {str(e)}")
    
    def hide_comments_frame(self):
        """Hide the comments frame"""
        self.comments_frame.pack_forget()
    
    def show_upload_frame(self):
        """Show the upload frame"""
        if not self.current_user:
            messagebox.showerror("Error", "You must be logged in to upload mods")
            return
        
        self.upload_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
    
    def hide_upload_frame(self):
        """Hide the upload frame"""
        self.upload_frame.pack_forget()
    
    def browse_upload_file(self):
        """Browse for a mod file to upload"""
        file_path = filedialog.askopenfilename(
            title="Select Mod File",
            filetypes=[
                ("All supported files", "*.zip;*.rar;*.7z;*.wad;*.wbfs;*.iso"),
                ("ZIP files", "*.zip"),
                ("RAR files", "*.rar"),
                ("7-Zip files", "*.7z"),
                ("WAD files", "*.wad"),
                ("WBFS files", "*.wbfs"),
                ("ISO files", "*.iso"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.upload_file_var.set(file_path)
    
    def upload_mod(self):
        """Upload a new mod"""
        if not self.current_user:
            messagebox.showerror("Error", "You must be logged in to upload mods")
            return
        
        # Get form data
        title = self.upload_title_var.get().strip()
        description = self.upload_desc_text.get(1.0, tk.END).strip()
        file_path = self.upload_file_var.get().strip()
        game_compatibility = self.upload_game_var.get().strip()
        version = self.upload_version_var.get().strip()
        tags = self.upload_tags_var.get().strip()
        is_public = self.upload_public_var.get()
        
        # Validate input
        if not all([title, file_path, game_compatibility]):
            messagebox.showerror("Error", "Title, file, and game compatibility are required")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Selected file does not exist")
            return
        
        try:
            # Copy file to mods directory
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.mods_dir, f"{self.current_user['id']}_{filename}")
            shutil.copy2(file_path, dest_path)
            
            # Upload to database
            mod_id = self.database.upload_mod(
                title=title,
                description=description,
                author_id=self.current_user['id'],
                file_path=dest_path,
                game_compatibility=game_compatibility,
                version=version,
                tags=tags,
                is_public=is_public
            )
            
            messagebox.showinfo("Success", f"Mod uploaded successfully! (ID: {mod_id})")
            
            # Clear form
            self.upload_title_var.set("")
            self.upload_desc_text.delete(1.0, tk.END)
            self.upload_file_var.set("")
            self.upload_game_var.set("")
            self.upload_version_var.set("1.0")
            self.upload_tags_var.set("")
            self.upload_public_var.set(True)
            
            # Hide upload frame and refresh mods list
            self.hide_upload_frame()
            self.refresh_mods_list()
            
        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            messagebox.showerror("Error", f"Upload failed: {str(e)}")
    
    def show_my_mods(self):
        """Show mods uploaded by the current user"""
        if not self.current_user:
            messagebox.showerror("Error", "You must be logged in to view your mods")
            return
        
        try:
            user_mods = self.database.get_user_mods(self.current_user['id'])
            
            dialog = tk.Toplevel(self.parent)
            dialog.title("My Mods")
            dialog.geometry("800x600")
            dialog.transient(self.parent)
            dialog.grab_set()
            
            # Center the dialog
            dialog.geometry("+%d+%d" % (self.parent.winfo_rootx() + 50, self.parent.winfo_rooty() + 50))
            
            # Create treeview
            tree = ttk.Treeview(dialog, columns=("title", "version", "downloads", "rating", "public", "date"), 
                               show="headings", height=20)
            
            tree.heading("title", text="Title")
            tree.heading("version", text="Version")
            tree.heading("downloads", text="Downloads")
            tree.heading("rating", text="Rating")
            tree.heading("public", text="Public")
            tree.heading("date", text="Upload Date")
            
            tree.column("title", width=200)
            tree.column("version", width=80)
            tree.column("downloads", width=80)
            tree.column("rating", width=80)
            tree.column("public", width=60)
            tree.column("date", width=120)
            
            # Add mods to treeview
            for mod in user_mods:
                rating_text = f"{mod['rating']:.1f}" if mod['rating'] > 0 else "No ratings"
                public_text = "Yes" if mod['is_public'] else "No"
                date_text = mod['upload_date'][:10] if mod['upload_date'] else "Unknown"
                
                tree.insert("", tk.END, values=(
                    mod['title'],
                    mod['version'],
                    mod['download_count'],
                    rating_text,
                    public_text,
                    date_text
                ), tags=(mod['id'],))
            
            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Bind double-click to view details
            tree.bind("<Double-1>", lambda e: self.view_mod_details_from_tree(tree, e))
            
            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
            
        except Exception as e:
            self.logger.error(f"Failed to show user mods: {e}")
            messagebox.showerror("Error", f"Failed to load your mods: {str(e)}")
    
    def view_mod_details_from_tree(self, tree, event):
        """View mod details from the user mods tree"""
        selection = tree.selection()
        if not selection:
            return
        
        mod_id = tree.item(selection[0], "tags")[0]
        
        try:
            mod_details = self.database.get_mod_details(mod_id)
            if mod_details:
                self.show_mod_details_dialog(mod_details)
        except Exception as e:
            self.logger.error(f"Failed to get mod details: {e}")
            messagebox.showerror("Error", f"Failed to load mod details: {str(e)}")
