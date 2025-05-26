import logging
import sqlite3
from datetime import datetime
import pytz
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Hanoi timezone (GMT+7)
HANOI_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

def get_hanoi_time():
    """Get current time in Hanoi timezone"""
    return datetime.now(HANOI_TZ)

def format_hanoi_datetime(dt_str):
    """Format datetime string that's already in Hanoi timezone"""
    try:
        # Parse datetime string (already in Hanoi timezone)
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%d/%m %H:%M')
    except:
        return dt_str

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('spending.db')
    cursor = conn.cursor()
    
    # Create transactions table (renamed from expenses to handle both income and expenses)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    ''')
    
    # Create budgets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            month TEXT NOT NULL,
            UNIQUE(user_id, category, month)
        )
    ''')
    
    conn.commit()
    conn.close()

# Categories for income and expenses
INCOME_CATEGORIES = {
    'wrk': '💼 Công việc',
    'ano': '💰 Khác'
}

EXPENSE_CATEGORIES = {
    'shp': '🛍️ Mua sắm',
    'eat': '🍽️ Ăn uống', 
    'ser': '🔧 Dịch vụ',
    'ent': '🎬 Giải trí',
    'inv': '📈 Đầu tư',
    'wrk': '💼 Công việc',
    'ano': '📦 Khác'
}

def parse_amount(amount_str):
    """Parse amount string with support for 'k' (thousand) and 'm' (million) suffix
    Numbers without suffix are automatically treated as 'k' (thousands)"""
    try:
        amount_str = amount_str.lower().strip()
        if amount_str.endswith('m'):
            # Remove 'm' and multiply by 1,000,000
            number_part = amount_str[:-1]
            return float(number_part) * 1000000
        elif amount_str.endswith('k'):
            # Remove 'k' and multiply by 1,000
            number_part = amount_str[:-1]
            return float(number_part) * 1000
        else:
            # No suffix = automatically treat as 'k' (thousands)
            return float(amount_str) * 1000
    except ValueError:
        raise ValueError("Số tiền không hợp lệ")

# Helper functions
def add_transaction(user_id, transaction_type, amount, category, description=""):
    conn = sqlite3.connect('spending.db')
    cursor = conn.cursor()
    date = get_hanoi_time().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO transactions (user_id, type, amount, category, description, date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, transaction_type, amount, category, description, date))
    
    conn.commit()
    conn.close()

def get_monthly_summary(user_id, month=None):
    if month is None:
        month = get_hanoi_time().strftime('%Y-%m')
    
    conn = sqlite3.connect('spending.db')
    cursor = conn.cursor()
    
    # Get income
    cursor.execute('''
        SELECT category, SUM(amount) FROM transactions 
        WHERE user_id = ? AND type = 'thu' AND date LIKE ?
        GROUP BY category
    ''', (user_id, f'{month}%'))
    income = cursor.fetchall()
    
    # Get expenses
    cursor.execute('''
        SELECT category, SUM(amount) FROM transactions 
        WHERE user_id = ? AND type = 'chi' AND date LIKE ?
        GROUP BY category
    ''', (user_id, f'{month}%'))
    expenses = cursor.fetchall()
    
    conn.close()
    return income, expenses

def get_monthly_spending(user_id, month=None):
    if month is None:
        month = get_hanoi_time().strftime('%Y-%m')
    
    conn = sqlite3.connect('spending.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT category, SUM(amount) FROM transactions 
        WHERE user_id = ? AND type = 'chi' AND date LIKE ?
        GROUP BY category
    ''', (user_id, f'{month}%'))
    
    results = cursor.fetchall()
    conn.close()
    return results

def set_budget(user_id, category, amount):
    conn = sqlite3.connect('spending.db')
    cursor = conn.cursor()
    month = get_hanoi_time().strftime('%Y-%m')
    
    cursor.execute('''
        INSERT OR REPLACE INTO budgets (user_id, category, amount, month)
        VALUES (?, ?, ?, ?)
    ''', (user_id, category, amount, month))
    
    conn.commit()
    conn.close()

def get_budget_status(user_id):
    conn = sqlite3.connect('spending.db')
    cursor = conn.cursor()
    month = get_hanoi_time().strftime('%Y-%m')
    
    # Get budgets for current month
    cursor.execute('''
        SELECT category, amount FROM budgets 
        WHERE user_id = ? AND month = ?
    ''', (user_id, month))
    
    budgets = dict(cursor.fetchall())
    
    # Get spending for current month
    spending = dict(get_monthly_spending(user_id, month))
    
    conn.close()
    
    status = []
    for category, budget_amount in budgets.items():
        spent = spending.get(category, 0)
        remaining = budget_amount - spent
        percentage = (spent / budget_amount) * 100 if budget_amount > 0 else 0
        
        status.append({
            'category': category,
            'budget': budget_amount,
            'spent': spent,
            'remaining': remaining,
            'percentage': percentage
        })
    
    return status

def get_recent_transactions(user_id, limit=10):
    """Lấy các giao dịch gần đây"""
    conn = sqlite3.connect('spending.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT type, amount, category, description, date 
        FROM transactions 
        WHERE user_id = ? 
        ORDER BY date DESC 
        LIMIT ?
    ''', (user_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    return results

def delete_last_transaction(user_id):
    """Xóa giao dịch cuối cùng"""
    conn = sqlite3.connect('spending.db')
    cursor = conn.cursor()
    
    # Get the last transaction
    cursor.execute('''
        SELECT id, type, amount, category, description, date
        FROM transactions 
        WHERE user_id = ? 
        ORDER BY date DESC 
        LIMIT 1
    ''', (user_id,))
    
    result = cursor.fetchone()
    if result:
        # Delete the transaction
        cursor.execute('DELETE FROM transactions WHERE id = ?', (result[0],))
        conn.commit()
    
    conn.close()
    return result

def clear_all_data(user_id):
    """Xóa toàn bộ dữ liệu của người dùng"""
    conn = sqlite3.connect('spending.db')
    cursor = conn.cursor()
    
    # Count data before deletion
    cursor.execute('SELECT COUNT(*) FROM transactions WHERE user_id = ?', (user_id,))
    transaction_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM budgets WHERE user_id = ?', (user_id,))
    budget_count = cursor.fetchone()[0]
    
    # Delete all transactions
    cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
    
    # Delete all budgets
    cursor.execute('DELETE FROM budgets WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    
    return transaction_count, budget_count

# Bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("💰 Thêm Thu"), KeyboardButton("💸 Thêm Chi")],
        [KeyboardButton("📊 Xem Tháng Này"), KeyboardButton("🎯 Đặt Ngân Sách")],
        [KeyboardButton("📈 Tình Trạng NS"), KeyboardButton("📋 Danh Mục")],
        [KeyboardButton("📝 Lịch Sử"), KeyboardButton("ℹ️ Hướng Dẫn")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Chào mừng đến với Bot Quản Lý Chi Tiêu! 💰\n\n"
        "Tôi sẽ giúp bạn theo dõi thu chi và quản lý ngân sách.\n"
        "Sử dụng các nút bên dưới hoặc gõ lệnh trực tiếp.",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🔹 *Lệnh chính:*
/in <số tiền> <danh mục> [mô tả] - Thêm thu nhập
/out <số tiền> <danh mục> [mô tả] - Thêm chi tiêu
/summary - Xem tổng kết thu chi tháng này
/budget <danh mục> <số tiền> - Đặt ngân sách tháng
/status - Kiểm tra tình trạng ngân sách
/history - Xem lịch sử giao dịch gần đây
/delete - Xóa giao dịch cuối cùng
/clear <password> - Xóa toàn bộ dữ liệu (cẩn thận!)
/categories - Xem danh mục thu chi

🔹 *Ví dụ:*
/in 5m wrk Lương tháng 5
/in 200k ano Tiền thưởng
/out 50k eat Cafe sáng
/budget eat 1m

🔹 *Đơn vị số tiền:*
• Không đơn vị = k (50 = 50,000)
• k = 1,000 VND (50k = 50,000)
• m = 1,000,000 VND (5m = 5,000,000)

🔹 *Danh mục THU:*
• wrk - 💼 Công việc
• ano - 💰 Khác

🔹 *Danh mục CHI:*
• shp - 🛍️ Mua sắm
• eat - 🍽️ Ăn uống
• ser - 🔧 Dịch vụ
• ent - 🎬 Giải trí
• inv - 📈 Đầu tư
• wrk - 💼 Công việc
• ano - 📦 Khác
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def add_income_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Thêm thu nhập"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "Cách dùng: /in <số tiền> <danh mục> [mô tả]\n"
                "Ví dụ: /in 5m wrk Lương tháng 5\n"
                "Hoặc: /in 200 ano Tiền thưởng (tự động = 200k)"
            )
            return
            
        amount = parse_amount(context.args[0])
        category = context.args[1].lower()
        description = " ".join(context.args[2:]) if len(context.args) > 2 else ""
        
        # Validate income category
        if category not in INCOME_CATEGORIES:
            cats = "\n".join([f"• {k} - {v}" for k, v in INCOME_CATEGORIES.items()])
            await update.message.reply_text(f"❌ Danh mục thu không hợp lệ. Chọn:\n{cats}")
            return
        
        user_id = update.effective_user.id
        add_transaction(user_id, 'thu', amount, category, description)
        
        cat_display = INCOME_CATEGORIES.get(category)
        
        await update.message.reply_text(
            f"✅ Đã thêm Thu nhập: {amount:,.0f} VND\n"
            f"Danh mục: {cat_display}\n"
            f"Mô tả: {description if description else 'Không có'}"
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi thêm thu nhập: {str(e)}")

async def add_expense_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Thêm chi tiêu"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "Cách dùng: /out <số tiền> <danh mục> [mô tả]\n"
                "Ví dụ: /out 50 eat Cafe sáng (tự động = 50k)\n"
                "Hoặc: /out 15k ser Cắt tóc"
            )
            return
            
        amount = parse_amount(context.args[0])
        category = context.args[1].lower()
        description = " ".join(context.args[2:]) if len(context.args) > 2 else ""
        
        # Validate expense category
        if category not in EXPENSE_CATEGORIES:
            cats = "\n".join([f"• {k} - {v}" for k, v in EXPENSE_CATEGORIES.items()])
            await update.message.reply_text(f"❌ Danh mục chi không hợp lệ. Chọn:\n{cats}")
            return
        
        user_id = update.effective_user.id
        add_transaction(user_id, 'chi', amount, category, description)
        
        cat_display = EXPENSE_CATEGORIES.get(category)
        
        await update.message.reply_text(
            f"✅ Đã thêm Chi tiêu: {amount:,.0f} VND\n"
            f"Danh mục: {cat_display}\n"
            f"Mô tả: {description if description else 'Không có'}"
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi thêm chi tiêu: {str(e)}")

async def view_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    income, expenses = get_monthly_summary(user_id)
    
    if not income and not expenses:
        await update.message.reply_text("📊 Chưa có giao dịch nào trong tháng này.")
        return
    
    message = "📊 *Tổng kết tháng này:*\n\n"
    
    # Income section
    total_income = 0
    if income:
        message += "💰 *THU NHẬP:*\n"
        for category, amount in income:
            cat_display = INCOME_CATEGORIES.get(category, category.title())
            message += f"• {cat_display}: {amount:,.0f} VND\n"
            total_income += amount
        message += f"📈 Tổng thu: *{total_income:,.0f} VND*\n\n"
    
    # Expenses section
    total_expenses = 0
    if expenses:
        message += "💸 *CHI TIÊU:*\n"
        for category, amount in expenses:
            cat_display = EXPENSE_CATEGORIES.get(category, category.title())
            message += f"• {cat_display}: {amount:,.0f} VND\n"
            total_expenses += amount
        message += f"📉 Tổng chi: *{total_expenses:,.0f} VND*\n\n"
    
    # Balance
    balance = total_income - total_expenses
    balance_emoji = "💚" if balance >= 0 else "❤️"
    message += f"{balance_emoji} *Số dư: {balance:,.0f} VND*"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def set_budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 2:
            await update.message.reply_text(
                "Cách dùng: /budget <danh mục> <số tiền>\n"
                "Ví dụ: /budget eat 1m\n"
                "Hoặc: /budget eat 1000k"
            )
            return
        
        category = context.args[0].lower()
        amount = parse_amount(context.args[1])
        
        # Validate expense category
        if category not in EXPENSE_CATEGORIES:
            cats = "\n".join([f"• {k} - {v}" for k, v in EXPENSE_CATEGORIES.items()])
            await update.message.reply_text(f"❌ Danh mục không hợp lệ. Chọn:\n{cats}")
            return
        
        user_id = update.effective_user.id
        set_budget(user_id, category, amount)
        
        cat_display = EXPENSE_CATEGORIES.get(category)
        await update.message.reply_text(
            f"🎯 Đã đặt ngân sách: {amount:,.0f} VND cho {cat_display} tháng này"
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi đặt ngân sách: {str(e)}")

async def budget_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    status = get_budget_status(user_id)
    
    if not status:
        await update.message.reply_text("🎯 Chưa đặt ngân sách nào cho tháng này.")
        return
    
    message = "📈 *Tình trạng ngân sách:*\n\n"
    
    for item in status:
        category = item['category']
        cat_display = EXPENSE_CATEGORIES.get(category, category.title())
        budget = item['budget']
        spent = item['spent']
        remaining = item['remaining']
        percentage = item['percentage']
        
        status_emoji = "🟢" if percentage < 80 else "🟡" if percentage < 100 else "🔴"
        
        message += f"{status_emoji} *{cat_display}*\n"
        message += f"   Ngân sách: {budget:,.0f} VND\n"
        message += f"   Đã chi: {spent:,.0f} VND ({percentage:.1f}%)\n"
        message += f"   Còn lại: {remaining:,.0f} VND\n\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def view_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xem lịch sử giao dịch gần đây"""
    user_id = update.effective_user.id
    transactions = get_recent_transactions(user_id, 15)
    
    if not transactions:
        await update.message.reply_text("📝 Chưa có giao dịch nào được ghi nhận.")
        return
    
    message = "📝 *Lịch sử giao dịch gần đây:*\n\n"
    
    for trans_type, amount, category, description, date in transactions:
        # Format date to Hanoi timezone
        date_str = format_hanoi_datetime(date)
        
        # Get category display
        if trans_type == 'thu':
            cat_display = INCOME_CATEGORIES.get(category, category)
            type_emoji = "💰"
        else:
            cat_display = EXPENSE_CATEGORIES.get(category, category)
            type_emoji = "💸"
        
        message += f"{type_emoji} *{amount:,.0f} VND* - {cat_display}\n"
        if description:
            message += f"   📄 {description}\n"
        message += f"   🕒 {date_str}\n\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def delete_last_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xóa giao dịch cuối cùng"""
    user_id = update.effective_user.id
    deleted = delete_last_transaction(user_id)
    
    if deleted:
        trans_id, trans_type, amount, category, description, date = deleted
        type_text = "thu nhập" if trans_type == 'thu' else "chi tiêu"
        cat_display = INCOME_CATEGORIES.get(category) if trans_type == 'thu' else EXPENSE_CATEGORIES.get(category)
        
        await update.message.reply_text(
            f"🗑️ Đã xóa giao dịch:\n"
            f"• Loại: {type_text}\n"
            f"• Số tiền: {amount:,.0f} VND\n"
            f"• Danh mục: {cat_display}\n"
            f"• Mô tả: {description if description else 'Không có'}"
        )
    else:
        await update.message.reply_text("❌ Không tìm thấy giao dịch nào để xóa.")

async def clear_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xóa toàn bộ dữ liệu với password bảo vệ"""
    try:
        if len(context.args) != 1:
            await update.message.reply_text(
                "⚠️ *Xóa toàn bộ dữ liệu*\n\n"
                "Cách dùng: `/clear <password>`\n"
                "Password: `deleteall`\n\n"
                "🚨 *CẢNH BÁO:* Lệnh này sẽ xóa:\n"
                "• Toàn bộ giao dịch thu chi\n"
                "• Toàn bộ ngân sách đã đặt\n"
                "• Không thể khôi phục!\n\n"
                "Chỉ sử dụng khi chắc chắn muốn bắt đầu lại.",
                parse_mode='Markdown'
            )
            return
        
        password = context.args[0]
        if password != "deleteall":
            await update.message.reply_text(
                "❌ Password không đúng!\n"
                "Để bảo vệ dữ liệu, vui lòng nhập đúng password."
            )
            return
        
        user_id = update.effective_user.id
        transaction_count, budget_count = clear_all_data(user_id)
        
        if transaction_count > 0 or budget_count > 0:
            await update.message.reply_text(
                f"🗑️ *Đã xóa toàn bộ dữ liệu!*\n\n"
                f"• {transaction_count} giao dịch\n"
                f"• {budget_count} ngân sách\n\n"
                f"✨ Bạn có thể bắt đầu lại từ đầu.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("📭 Tài khoản của bạn đã trống rồi.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi xóa dữ liệu: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "💰 Thêm Thu":
        await update.message.reply_text(
            "💰 *Thêm thu nhập nhanh:*\n\n"
            "Gõ: `/in <số tiền> <danh mục> [mô tả]`\n\n"
            "*Ví dụ:*\n"
            "`/in 5m wrk Lương tháng 5`\n"
            "`/in 200 ano Tiền thưởng` (= 200k)\n"
            "`/in 50 wrk Làm thêm` (= 50k)\n\n"
            "*Danh mục THU:*\n• wrk - 💼 Công việc\n• ano - 💰 Khác",
            parse_mode='Markdown'
        )
    elif text == "💸 Thêm Chi":
        await update.message.reply_text(
            "💸 *Thêm chi tiêu nhanh:*\n\n"
            "Gõ: `/out <số tiền> <danh mục> [mô tả]`\n\n"
            "*Ví dụ:*\n"
            "`/out 50 eat Cafe sáng` (= 50k)\n"
            "`/out 15k ser Xe ôm`\n"
            "`/out 100 ent Xem phim` (= 100k)\n\n"
            "*Danh mục CHI phổ biến:*\n• eat - 🍽️ Ăn uống\n• ser - 🔧 Dịch vụ\n• ent - 🎬 Giải trí\n• shp - 🛍️ Mua sắm",
            parse_mode='Markdown'
        )
    elif text == "📊 Xem Tháng Này":
        await view_summary(update, context)
    elif text == "🎯 Đặt Ngân Sách":
        await update.message.reply_text(
            "Để đặt ngân sách, sử dụng:\n"
            "/budget <danh mục> <số tiền>\n\n"
            "Ví dụ: /budget eat 1m"
        )
    elif text == "📈 Tình Trạng NS":
        await budget_status(update, context)
    elif text == "📋 Danh Mục":
        await update.message.reply_text(
            "📋 *Danh mục Thu Chi:*\n\n"
            "💰 *THU NHẬP:*\n"
            "• wrk - 💼 Công việc\n"
            "• ano - 💰 Khác\n\n"
            "💸 *CHI TIÊU:*\n"
            "• shp - 🛍️ Mua sắm\n"
            "• eat - 🍽️ Ăn uống\n"
            "• ser - 🔧 Dịch vụ\n"
            "• ent - 🎬 Giải trí\n"
            "• inv - 📈 Đầu tư\n"
            "• wrk - 💼 Công việc\n"
            "• ano - 📦 Khác",
            parse_mode='Markdown'
        )
    elif text == "📝 Lịch Sử":
        await view_history(update, context)
    elif text == "ℹ️ Hướng Dẫn":
        await help_command(update, context)

async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hiển thị danh mục thu chi"""
    await update.message.reply_text(
        "📋 *Danh mục Thu Chi:*\n\n"
        "💰 *THU NHẬP:*\n"
        "• wrk - 💼 Công việc\n"
        "• ano - 💰 Khác\n\n"
        "💸 *CHI TIÊU:*\n"
        "• shp - 🛍️ Mua sắm\n"
        "• eat - 🍽️ Ăn uống\n"
        "• ser - 🔧 Dịch vụ\n"
        "• ent - 🎬 Giải trí\n"
        "• inv - 📈 Đầu tư\n"
        "• wrk - 💼 Công việc\n"
        "• ano - 📦 Khác",
        parse_mode='Markdown'
    )

def main():
    # Initialize database
    init_db()
    
    # Get bot token from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("in", add_income_command))
    application.add_handler(CommandHandler("out", add_expense_command))
    application.add_handler(CommandHandler("summary", view_summary))
    application.add_handler(CommandHandler("budget", set_budget_command))
    application.add_handler(CommandHandler("status", budget_status))
    application.add_handler(CommandHandler("history", view_history))
    application.add_handler(CommandHandler("delete", delete_last_command))
    application.add_handler(CommandHandler("clear", clear_data_command))
    application.add_handler(CommandHandler("categories", categories_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    print("Starting Spending Manager Bot...")
    
    # Set up bot commands
    async def post_init(application):
        commands = [
            BotCommand("start", "🏠 Khởi động bot"),
            BotCommand("in", "💰 Thêm thu nhập"),
            BotCommand("out", "💸 Thêm chi tiêu"),
            BotCommand("summary", "📊 Tổng kết tháng"),
            BotCommand("budget", "🎯 Đặt ngân sách"),
            BotCommand("status", "📈 Tình trạng ngân sách"),
            BotCommand("history", "📝 Lịch sử giao dịch"),
            BotCommand("delete", "🗑️ Xóa giao dịch cuối"),
            BotCommand("clear", "⚠️ Xóa toàn bộ dữ liệu"),
            BotCommand("categories", "📋 Xem danh mục"),
            BotCommand("help", "ℹ️ Hướng dẫn sử dụng")
        ]
        await application.bot.set_my_commands(commands)
        print("Bot commands set successfully!")
    
    application.post_init = post_init
    application.run_polling()

if __name__ == '__main__':
    main()