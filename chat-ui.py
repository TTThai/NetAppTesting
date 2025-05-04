#!/usr/bin/env python3
import os
import json
import time
import socket
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import customtkinter as ctk
from node_controller import NodeController
import base64
import hashlib
import uuid
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk
import io
import sys

from user_management import UserManager
from chatroom_manager import ChatroomManager
from lib.logging import create_frontend_logger

ALLOWED_FILE_TYPES = [
    ('Images', '*.png *.jpg *.jpeg *.gif'),
    ('Text files', '*.txt'),
    ('PDF files', '*.pdf'),
    ('Documents', '*.doc *.docx'),
    ('All files', '*.*')  
]
MAX_FILE_SIZE = 5 * 1024 * 1024 

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NetApp Chat")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        self.session_id = str(uuid.uuid4())[:8]
        self.logger = create_frontend_logger(self.session_id)
        self.logger.system("Application started", {"session_id": self.session_id})
        
        self.user_manager = UserManager()
        self.chatroom_manager = ChatroomManager()
        self.controller = NodeController()
        
        # Default state
        self.node_address = None
        self.current_user = None
        self.selected_chatroom = None
        self.selected_peer = None
        self.chatrooms = {} 
        self.peers = {}
        self.downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads", "NetApp")
        os.makedirs(self.downloads_folder, exist_ok=True)
    
        self.setup_login_ui()
        
        # Start polling thread 
        self.polling_active = False
    
    def get_local_ip(self):
        """Get local IP address"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            return f"{ip}:7091"
        except Exception:
            return "127.0.0.1:7091"  # Fallback to localhost, change later
        finally:
            s.close()
    
    def setup_login_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.login_frame = ctk.CTkFrame(self.root)
        self.login_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        app_title = ctk.CTkLabel(self.login_frame, text="NetApp Chat", font=("Helvetica", 24, "bold"))
        app_title.pack(pady=(20, 40))
        
        login_form = ctk.CTkFrame(self.login_frame)
        login_form.pack(padx=20, pady=20)
        
        username_label = ctk.CTkLabel(login_form, text="Username:")
        username_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.username_entry = ctk.CTkEntry(login_form, width=200)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)
        
        password_label = ctk.CTkLabel(login_form, text="Password:")
        password_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.password_entry = ctk.CTkEntry(login_form, width=200, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Node address
        address_label = ctk.CTkLabel(login_form, text="Node Address:")
        address_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.address_entry = ctk.CTkEntry(login_form, width=200)
        self.address_entry.grid(row=2, column=1, padx=10, pady=10)
        self.address_entry.insert(0, self.get_local_ip())
        
        login_button = ctk.CTkButton(login_form, text="Login", command=self.login)
        login_button.grid(row=3, column=0, padx=10