#!/usr/bin/env python3
"""
Setup script for Spending Manager Telegram Bot
Hướng dẫn thiết lập Bot Quản Lý Chi Tiêu
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Kiểm tra phiên bản Python"""
    if sys.version_info < (3, 8):
        print("❌ Bot yêu cầu Python 3.8 trở lên")
        print(f"   Phiên bản hiện tại: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_requirements():
    """Cài đặt các thư viện cần thiết"""
    print("\n📦 Đang cài đặt thư viện...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Đã cài đặt thành công các thư viện")
        return True
    except subprocess.CalledProcessError:
        print("❌ Lỗi cài đặt thư viện")
        return False

def setup_env_file():
    """Thiết lập file .env"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ File .env đã tồn tại")
        return True
    
    if env_example.exists():
        # Copy from example
        with open(env_example, 'r') as f:
            content = f.read()
        
        print("\n🔑 Thiết lập Bot Token:")
        print("1. Mở Telegram và tìm @BotFather")
        print("2. Gửi lệnh /newbot")
        print("3. Làm theo hướng dẫn để tạo bot")
        print("4. Sao chép token bot")
        
        token = input("\nNhập Bot Token: ").strip()
        
        if token:
            content = content.replace("your_bot_token_here", token)
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ Đã tạo file .env")
            return True
        else:
            print("❌ Token không được để trống")
            return False
    else:
        print("❌ Không tìm thấy file .env.example")
        return False

def test_bot_token():
    """Kiểm tra bot token"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            print("❌ Không tìm thấy TELEGRAM_BOT_TOKEN trong file .env")
            return False
        
        if len(token) < 40:
            print("❌ Bot token có vẻ không hợp lệ (quá ngắn)")
            return False
        
        print("✅ Bot token đã được thiết lập")
        return True
    except ImportError:
        print("❌ Chưa cài đặt python-dotenv")
        return False

def main():
    print("🚀 Thiết lập Bot Quản Lý Chi Tiêu Telegram")
    print("=" * 50)
    
    # Kiểm tra Python version
    if not check_python_version():
        return
    
    # Cài đặt requirements
    if not install_requirements():
        return
    
    # Thiết lập .env
    if not setup_env_file():
        return
    
    # Test bot token
    if not test_bot_token():
        return
    
    print("\n🎉 Thiết lập hoàn tất!")
    print("\n📋 Các bước tiếp theo:")
    print("1. Chạy bot: python spending_bot.py")
    print("2. Tìm bot trên Telegram và gửi /start")
    print("3. Bắt đầu quản lý chi tiêu!")
    
    run_now = input("\nChạy bot ngay bây giờ? (y/n): ").strip().lower()
    if run_now in ['y', 'yes']:
        print("\n🤖 Đang khởi động bot...")
        try:
            subprocess.run([sys.executable, "spending_bot.py"])
        except KeyboardInterrupt:
            print("\n👋 Bot đã dừng!")

if __name__ == "__main__":
    main()