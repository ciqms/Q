import requests, uuid, random, string, hashlib, json, time, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# ===== ثوابت =====
uu = str(uuid.uuid4())
timestamp = str(int(time.time()))

# ===== حالات البوت =====
LOGIN_USER, LOGIN_PASS, CHECKPOINT_CHOICE, ENTER_CODE, TARGET, REPORT_TYPE = range(6)

# ===== توليد القيم العشوائية =====
def RandomString(n=10):
    return ''.join(random.choice(string.ascii_lowercase + '1234567890') for _ in range(n))

def RandomStringChars(n=1):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(n))

def randomStringWithChar(stringLength=10):
    result = ''.join(random.choice(string.ascii_lowercase + '1234567890') for _ in range(stringLength - 1))
    return RandomStringChars(1) + result

def generateUSER_AGENT():
    Devices_menu = ['HUAWEI', 'Xiaomi', 'samsung', 'OnePlus']
    DPIs = ['480', '320', '640', '515', '120', '160', '240', '800']
    randResolution = random.randrange(2, 9) * 180
    lowerResolution = randResolution - 180
    DEVICE_SETTINTS = {
        'system': "Android",
        'Host': "Instagram",
        'manufacturer': random.choice(Devices_menu),
        'model': f"{random.choice(Devices_menu)}-{randomStringWithChar(4).upper()}",
        'android_version': random.randint(18, 25),
        'android_release': f"{random.randint(1, 7)}.{random.randint(0, 7)}",
        "cpu": f"{RandomStringChars(2)}{random.randrange(1000, 9999)}",
        'resolution': f'{randResolution}x{lowerResolution}',
        'randomL': RandomString(6),
        'dpi': random.choice(DPIs)
    }
    return '{Host} 155.0.0.37.107 {system} ({android_version}/{android_release}; {dpi}dpi; {resolution}; {manufacturer}; {model}; {cpu}; {randomL}; en_US)'.format(**DEVICE_SETTINTS)

def generate_DeviceId(ID):
    volatile_ID = "12345"
    m = hashlib.md5()
    m.update(ID.encode('utf-8') + volatile_ID.encode('utf-8'))
    return 'android-' + m.hexdigest()[:16]

def headers_login(user_agent):
    return {
        'User-Agent': user_agent,
        'Host': 'i.instagram.com',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'accept-encoding': 'gzip, deflate',
        'x-fb-http-engine': 'Liger',
        'Connection': 'close'
    }

# ===== المتغيرات العالمية =====
bot_data = {}

# ===== تسجيل الدخول =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 مرحبا! أرسل اسم المستخدم لتسجيل الدخول:")
    return LOGIN_USER

async def login_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_data['username'] = update.message.text
    await update.message.reply_text("أرسل كلمة المرور:")
    return LOGIN_PASS

async def login_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    username = bot_data['username']
    device_id = generate_DeviceId(username)
    user_agent = generateUSER_AGENT()
    bot_data['user_agent'] = user_agent
    data = {
        'guid': uu,
        'enc_password': f"#PWD_INSTAGRAM:0:{timestamp}:{password}",
        'username': username,
        'device_id': device_id,
        'login_attempt_count': '0'
    }
    req = requests.post("https://i.instagram.com/api/v1/accounts/login/", headers=headers_login(user_agent), data=data)
    cookies = req.cookies
    csrftoken = cookies.get("csrftoken", "missing")
    bot_data['csrftoken'] = csrftoken
    bot_data['cookies'] = cookies

    if "logged_in_user" in req.text:
        sessionid = cookies.get("sessionid")
        bot_data['sessionid'] = sessionid
        await update.message.reply_text(f"✅ تم تسجيل الدخول بنجاح كـ @{username}\nأرسل أسماء المستخدمين المستهدفين (مفصولة بمسافة أو فاصلة):")
        return TARGET
    elif 'checkpoint_challenge_required' in req.text:
        bot_data['req'] = req
        await update.message.reply_text("🔒 تحقق أمني مطلوب. اختر الطريقة للتحقق (0: هاتف, 1: بريد):")
        return CHECKPOINT_CHOICE
    else:
        await update.message.reply_text("❌ فشل تسجيل الدخول")
        return ConversationHandler.END

# ===== التحقق الأمني =====
async def checkpoint_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    req = bot_data['req']
    cookies = bot_data['cookies']
    user_agent = bot_data['user_agent']
    csrftoken = bot_data['csrftoken']
    data = {'choice': str(choice), '_uuid': uu, '_uid': uu, '_csrftoken': csrftoken}
    path = req.json()['challenge']['api_path']
    send = requests.post(f"https://i.instagram.com/api/v1{path}", headers=headers_login(user_agent), data=data, cookies=cookies)
    contact_point = send.json()["step_data"]["contact_point"]
    await update.message.reply_text(f"تم إرسال الكود إلى: {contact_point}\nأرسل الكود هنا:")
    return ENTER_CODE

async def enter_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    req = bot_data['req']
    cookies = bot_data['cookies']
    user_agent = bot_data['user_agent']
    csrftoken = bot_data['csrftoken']
    username = bot_data['username']
    data = {'security_code': code, '_uuid': uu, '_uid': uu, '_csrftoken': csrftoken}
    path = req.json()['challenge']['api_path']
    send_code = requests.post(f"https://i.instagram.com/api/v1{path}", headers=headers_login(user_agent), data=data, cookies=cookies)

    if "logged_in_user" in send_code.text:
        sessionid = send_code.cookies.get("sessionid")
        bot_data['sessionid'] = sessionid
        await update.message.reply_text(f"✅ تم تسجيل الدخول كـ @{username}\nأرسل أسماء المستخدمين المستهدفين (مفصولة بمسافة أو فاصلة):")
        return TARGET
    else:
        await update.message.reply_text("❌ الكود غير صحيح أو فشل تسجيل الدخول")
        return ConversationHandler.END

# ===== إدخال الأهداف =====
async def target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    targets = update.message.text.replace(',', ' ').split()
    bot_data['targets'] = targets
    await update.message.reply_text(
        f"تم حفظ الأهداف: {', '.join(targets)}\nاختر أنواع البلاغات (مثال: 1 3 5)\n"
        "1: Spam\n2: Self\n3: Drugs sell\n4: Nudity\n5: Violence\n6: Hate\n7: Harassment\n8: Impersonation"
    )
    return REPORT_TYPE

# ===== البلاغ مع دعم أنواع متعددة =====
async def start_reporting(context: ContextTypes.DEFAULT_TYPE):
    targets = bot_data['targets']
    sessionid = bot_data['sessionid']
    csrftoken = bot_data['csrftoken']
    reportTypes = bot_data['reportTypes']
    chat_id = bot_data['chat_id']

    context.chat_data['reporting'] = True
    count = 0

    while context.chat_data.get('reporting', False):
        for target in targets:
            url = f"https://www.instagram.com/{target}/"
            response = requests.get(url)
            start = response.text.find('"profilePage_') + len('"profilePage_')
            end = response.text.find('"', start)
            user_id = response.text[start:end]

            res = requests.post(
                'https://www.instagram.com/graphql/query',
                cookies={},
                headers={
                    'accept': '*/*',
                    'content-type': 'application/x-www-form-urlencoded',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
                    'x-asbd-id': '359341',
                    'x-csrftoken': 'njXfzdB0S2d5HR-tZJ6Zfm'
                },
                data={
                    'lsd': 'AVooTjceqws',
                    'variables': '{"id":"' + user_id + '","render_surface":"PROFILE"}',
                    'server_timestamps': 'true',
                    'doc_id': '9661599240584790'
                }
            ).json()

            try:
                target_id = res['data']['user']['id']
            except:
                await context.bot.send_message(chat_id=chat_id, text=f"❌ فشل الحصول على معرف @{target}")
                continue

            # إرسال بلاغات متعددة
            for rType in reportTypes:
                r3 = requests.post(
                    f"https://i.instagram.com/users/{target_id}/flag/",
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Host": "i.instagram.com",
                        'cookie': f"sessionid={sessionid}",
                        "X-CSRFToken": csrftoken,
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
                    },
                    data=f'source_name=&reason_id={rType}&frx_context=',
                    allow_redirects=False
                )
                count += 1
                if r3.status_code in [200, 201]:
                    await context.bot.send_message(chat_id=chat_id, text=f"✅ بلاغ ناجح على @{target} | النوع: {rType} | العدد الكلي: {count}")
                else:
                    await context.bot.send_message(chat_id=chat_id, text=f"❌ فشل البلاغ على @{target} | النوع: {rType} | كود: {r3.status_code}")

        await asyncio.sleep(2)

# ===== اختيار أنواع البلاغات =====
async def report_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        reportTypes = [int(x) for x in update.message.text.replace(',', ' ').split()]
        for rt in reportTypes:
            if rt not in range(1, 9):
                await update.message.reply_text("❌ خيار غير صحيح، أرسل أرقام من 1 إلى 8 مفصولة بمسافة أو فاصلة.")
                return REPORT_TYPE
    except:
        await update.message.reply_text("❌ أدخل أرقام صحيحة مفصولة بمسافة أو فاصلة.")
        return REPORT_TYPE

    bot_data['reportTypes'] = reportTypes
    bot_data['chat_id'] = update.effective_chat.id

    await update.message.reply_text(f"🚀 بدأ الإبلاغ التلقائي بالأنواع: {', '.join(map(str, reportTypes))}\nأرسل /stop لإيقاف العملية.")
    asyncio.create_task(start_reporting(context))
    return ConversationHandler.END

# ===== إيقاف البلاغ =====
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.chat_data.get('reporting', False):
        context.chat_data['reporting'] = False
        await update.message.reply_text("⏹️ تم إيقاف الإبلاغ بنجاح")
    else:
        await update.message.reply_text("لا يوجد عملية إبلاغ تعمل الآن")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء")
    return ConversationHandler.END

# ===== تشغيل البوت =====
BOT_TOKEN = '8128622448:AAH_6CVVS0f4LSEIRxhPWa1dNZZ2r-Qj8Tk'

app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        LOGIN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_user)],
        LOGIN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_pass)],
        CHECKPOINT_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkpoint_choice)],
        ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_code)],
        TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, target)],
        REPORT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_type)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

app.add_handler(CommandHandler('stop', stop))
app.add_handler(conv_handler)
app.run_polling()
