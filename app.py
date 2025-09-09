# -*- coding: utf-8 -*-
"""
Fully Automated Telegram Bot Script for Heroku Deployment

This script is designed to be run by Heroku Scheduler (e.g., every 10 minutes).
It calculates the current day based on a start date, checks for messages
scheduled within the last interval, sends them, and then exits.
"""

# --- الخطوة 1: استيراد المكتبات المطلوبة ---
import pandas as pd
import os
import asyncio
import datetime
import random
from telegram import Bot

print("تم استيراد المكتبات بنجاح.")

# --- الخطوة 2: إعداد المتغيرات الأساسية ---

# !!! هام جداً: قم بتعيين تاريخ بدء الحملة هنا !!!
# غيّر هذا التاريخ إلى اليوم الذي ستقوم فيه بتشغيل البوت لأول مرة
# على سبيل المثال، إذا كان اليوم هو 10 سبتمبر 2025
START_DATE = datetime.date(2025, 9, 10) # السنة، الشهر، اليوم

# الفاصل الزمني الذي سيقوم فيه Heroku Scheduler بتشغيل السكريبت (بالدقائق)
# يجب أن يتطابق هذا الرقم مع الإعداد الذي ستضعه في Heroku
RUN_INTERVAL_MINUTES = 10

# معلومات بوت تيليجرام الخاصة بك
TELEGRAM_TOKEN = "8212477973:AAElSpCamzjLLuA9X94V9DG8LCSVbH-oGVw"
TELEGRAM_CHANNEL = "@DailyHealth_tips"

# تحديد مسار ملف البيانات
# This code finds the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
CSV_FILENAME = os.path.join(script_dir, "telegram_schedule_100_days.csv")


# --- الخطوة 3: دالة إرسال الرسائل ---

async def send_messages(bot, messages_to_send):
    """Asynchronously sends a list of messages."""
    if not messages_to_send:
        print("لا توجد رسائل لإرسالها في هذا الفاصل الزمني.")
        return

    print(f"تم العثور على {len(messages_to_send)} رسالة. جار الإرسال...")
    tasks = [bot.send_message(chat_id=TELEGRAM_CHANNEL, text=msg) for msg in messages_to_send]
    try:
        await asyncio.gather(*tasks)
        print("✔️ تم إرسال جميع الرسائل المجدولة بنجاح.")
    except Exception as e:
        print(f"⚠️ حدث خطأ أثناء إرسال مجموعة الرسائل: {e}")


# --- الخطوة 4: المنطق الرئيسي للسكريبت ---

def main():
    """
    The main logic to be executed by the scheduler.
    """
    print("\n" + "="*50)
    print(f"🤖 [{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] بدء تشغيل السكريبت...")

    # 1. التحقق من وجود ملف البيانات
    if not os.path.exists(CSV_FILENAME):
        print(f"❌ خطأ فادح: ملف البيانات '{os.path.basename(CSV_FILENAME)}' غير موجود.")
        return

    # 2. حساب اليوم الحالي وتحديد أي محتوى سيتم استخدامه
    current_time_utc = datetime.datetime.now(datetime.timezone.utc)
    current_date_utc = current_time_utc.date()
    
    # Calculate the number of days passed since the start date
    day_number_seq = (current_date_utc - START_DATE).days + 1
    
    day_to_schedule = 0
    
    if 1 <= day_number_seq <= 100:
        # الوضع التسلسلي: استخدام اليوم المحسوب
        day_to_schedule = day_number_seq
        print(f"حالة التشغيل: تسلسلي. اليوم هو اليوم رقم {day_to_schedule} منذ تاريخ البدء.")
    else:
        # الوضع العشوائي: اختيار يوم عشوائي بعد انتهاء 100 يوم
        # نستخدم تاريخ اليوم كبذرة (seed) لضمان اختيار نفس اليوم العشوائي طوال اليوم
        random.seed(current_date_utc.strftime('%Y%m%d'))
        day_to_schedule = random.randint(1, 100)
        print(f"🎉 اكتملت المئة يوم! حالة التشغيل: عشوائي. محتوى اليوم مأخوذ من اليوم رقم {day_to_schedule}.")

    # 3. قراءة وفلترة الرسائل التي حان وقتها
    df = pd.read_csv(CSV_FILENAME)
    day_schedule = df[df['day'] == day_to_schedule]

    if day_schedule.empty:
        print(f"⚠️ تحذير: لا توجد بيانات لليوم رقم {day_to_schedule}.")
        return

    messages_to_send_now = []
    # Define the time window to check for messages
    start_of_window = current_time_utc - datetime.timedelta(minutes=RUN_INTERVAL_MINUTES)

    for _, row in day_schedule.iterrows():
        try:
            # Combine the current date with the message time to create a full datetime object
            msg_time_obj = datetime.datetime.strptime(row['time'], '%H:%M').time()
            msg_datetime_utc = current_time_utc.replace(hour=msg_time_obj.hour, minute=msg_time_obj.minute, second=0, microsecond=0)

            # Check if the message's scheduled time falls within the current window
            if start_of_window < msg_datetime_utc <= current_time_utc:
                messages_to_send_now.append(row['message'])
        except (ValueError, TypeError):
            print(f"⚠️ تحذير: تم تخطي وقت غير صالح في الجدول: {row['time']}")
            continue
            
    # 4. إرسال الرسائل التي تم العثور عليها
    bot = Bot(token=TELEGRAM_TOKEN)
    asyncio.run(send_messages(bot, messages_to_send_now))
    
    print("🏁 انتهى عمل السكريبت. سيعمل مرة أخرى حسب جدولة Heroku.")
    print("="*50)


if __name__ == "__main__":
    main()

