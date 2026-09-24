#!/usr/bin/env python3
from __future__ import annotations
import html,http.server,json,os,re,socketserver,sys,threading,time,urllib.error,urllib.parse,urllib.request,uuid
from dataclasses import dataclass
from typing import Any

TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN","")
TG_LION_API_KEY=os.getenv("TG_LION_API_KEY","")
TG_LION_USER_ID=os.getenv("TG_LION_USER_ID","")
WORKER_URL=os.getenv("WORKER_URL","")
WORKER_TOKEN=os.getenv("WORKER_TOKEN","")
NOWPAYMENTS_API_KEY=os.getenv("NOWPAYMENTS_API_KEY","")
NOWPAYMENTS_PAYOUT_ADDRESS=os.getenv("NOWPAYMENTS_PAYOUT_ADDRESS","")
NOWPAYMENTS_PAYOUT_CURRENCY=os.getenv("NOWPAYMENTS_PAYOUT_CURRENCY","usdtbsc")
NOWPAYMENTS_FEE_BUFFER=float(os.getenv("NOWPAYMENTS_FEE_BUFFER","0.06"))
ADMIN_IDS=[int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip().isdigit()]
MIN_DEPOSIT=float(os.getenv("MIN_DEPOSIT","5.00"))
POLL_INTERVAL=int(os.getenv("POLL_INTERVAL","30"))
INVOICE_CLEANUP_INTERVAL=int(os.getenv("INVOICE_CLEANUP_INTERVAL","600"))
SUPPORT_URL=os.getenv("SUPPORT_URL","https://t.me/YourSupportHandle")

LANGUAGES={
"en":{"name":"English","flag":"🇬🇧","welcome":"Your Balance","select_option":"Select an option from the menu below:","browse_desc":"Browse and purchase verified Telegram accounts.","features":"Instant delivery · Secure checkout · 24/7 support","browse_accounts":"Browse Accounts","wallet":"Wallet","my_orders":"My Orders","profile":"Profile","language":"Language","support":"Support","admin_panel":"🛠 Admin Panel","back_home":"Back to Home","back_avail":"Back to availability","back_admin":"🛠 Back to Admin","available_inventory":"Available inventory","select_country":"Select a country to view live quantity and submit a request.","showing_page":"Page {page} of {total} · Showing {shown} of {total_c} countries","enter_qty":"Enter Custom Quantity","price_per_account":"Price per account","available_stock":"Available stock","tap_qty":"Tap below to enter your desired quantity.","send_qty":"Send the quantity you want to purchase as a number.","example_3":"Example: 3","your_wallet":"Your Wallet","balance":"Balance","tap_deposit":"Tap Deposit Funds to add balance.","deposit_funds":"Deposit Funds","enter_amount":"Enter the amount you want to deposit as a number.","minimum":"Minimum","example_5":"Example: 5","select_network":"Select your network:","amount":"Amount","you_deposit":"You deposit","total_to_send":"Total to send","send_exactly":"Send exactly","address":"Address","payment_id":"Payment ID","fee_notice":"Includes ~{pct}% processing fee (covers network + conversion costs).","send_correct_network":"Send on the correct network only.","invoice_valid":"Invoice valid for 60 minutes.","credit_notice":"Your balance will be credited automatically within 1–3 minutes.","copy_address":"Copy Address","check_status":"Check Status","your_orders":"Your orders","no_orders":"No orders yet","no_orders_desc":"Browse availability to start a request.","status":"Status","profile_title":"Profile","name":"Name","id":"ID","user_status":"Status","active":"✅ Active","banned":"🚫 Banned","order_summary":"🛒 Order Summary","country":"Country","quantity":"Quantity","total_price":"Total Price","your_balance":"Your Wallet Balance","sufficient":"✅ Sufficient","insufficient":"❌ Insufficient","confirm_purchase":"✅ Confirm Purchase","change_quantity":"Change Quantity","account_s":"account(s)","click_confirm":"Click 'Confirm Purchase' to complete your order.","not_enough":"You don't have enough balance. Please deposit funds first.","purchasing":"Purchasing {qty} number(s) from {country}...","please_wait":"Please wait.","numbers_purchased":"✅ Numbers Purchased","order_id":"Order ID","total_paid":"Total Paid","your_numbers":"Your Numbers","click_get_code":"Click '📩 Get Code' to fetch the login code for each number.","get_code":"📩 Get Code","get_code_n":"📩 Get Code for #{n}","view_my_orders":"View my orders","fetching_code":"Fetching code for","code_received":"✅ Code Received for Account #{n}","number":"Number","code":"Code","password":"Password","code_login":"Login to Telegram with this number, then use the code and password above.","retry":"🔄 Retry","failed":"Failed","language_title":"🌍 Select your language","language_set":"✅ Language changed to {name}","deposit_confirmed":"✅ Deposit Confirmed!","new_balance":"New Balance","admin_title":"🛠 Admin Panel","total_users":"Total Users","banned_users":"Banned Users","total_orders":"Total Orders","total_deposits":"Total Deposits","total_spent":"Total Spent","total_profit":"Total Profit","user_balances":"User Balances (owed)","profit_margin":"Profit Margin","select_action":"Select an action below:","admin_users":"👥 Users","admin_orders":"📦 Orders","credit_user":"💳 Credit User","debit_user":"💸 Debit User","ban_user":"🚫 Ban User","unban_user":"✅ Unban User","set_margin":"📊 Set Profit Margin","broadcast":"Broadcast","credit_prompt":"Send in format:\n<code>user_id amount</code>\n\nExample: <code>123456789 5</code>","debit_prompt":"Send in format:\n<code>user_id amount</code>\n\nExample: <code>123456789 2</code>","ban_prompt":"Send the user ID to ban.","unban_prompt":"Send the user ID to unban.","margin_prompt":"Current: <b>{pct}%</b>\n\nSend the new margin as a percentage.\nExample: <code>50</code> for 50%","broadcast_prompt":"Send the message to broadcast.\n\nUse <code>&lt;emoji:ID&gt;</code> to embed a premium emoji.","invalid_input":"Invalid input.","invalid_amount":"Invalid amount.","invalid_quantity":"Invalid quantity.","min_deposit_err":"Minimum deposit is {amount}.","session_expired":"Session expired. Start over.","unauthorized":"❌ Unauthorized.","banned_msg":"🚫 You are banned from using this bot.","code_failed":"Failed to fetch code","error_service":"The service is temporarily unavailable.","invoice_expired":"Your deposit invoice expired","start_over":"Tap 'Deposit Funds' in the Wallet to start a new one."},
"hi":{"name":"हिन्दी","flag":"🇮🇳","welcome":"आपका बैलेंस","select_option":"नीचे दिए गए मेनू से एक विकल्प चुनें:","browse_desc":"सत्यापित Telegram खाते ब्राउज़ करें और खरीदें।","features":"तत्काल डिलीवरी · सुरक्षित चेकआउट · 24/7 सहायता","browse_accounts":"खाते ब्राउज़ करें","wallet":"वॉलेट","my_orders":"मेरे ऑर्डर","profile":"प्रोफ़ाइल","language":"भाषा","support":"सहायता","admin_panel":"🛠 एडमिन पैनल","back_home":"होम पर वापस","back_avail":"उपलब्धता पर वापस","back_admin":"🛠 एडमिन पर वापस","available_inventory":"उपलब्ध इन्वेंटरी","select_country":"लाइव मात्रा देखने और अनुरोध सबमिट करने के लिए एक देश चुनें।","showing_page":"पृष्ठ {page} / {total} · {shown} / {total_c} देश","enter_qty":"कस्टम मात्रा दर्ज करें","price_per_account":"प्रति खाता मूल्य","available_stock":"उपलब्ध स्टॉक","tap_qty":"अपनी इच्छित मात्रा दर्ज करने के लिए नीचे टैप करें।","send_qty":"खरीदने की मात्रा एक संख्या के रूप में भेजें।","example_3":"उदाहरण: 3","your_wallet":"आपका वॉलेट","balance":"बैलेंस","tap_deposit":"बैलेंस जोड़ने के लिए डिपॉज़िट फंड्स टैप करें।","deposit_funds":"फंड्स जमा करें","enter_amount":"जमा करने की राशि एक संख्या के रूप में दर्ज करें।","minimum":"न्यूनतम","example_5":"उदाहरण: 5","select_network":"अपना नेटवर्क चुनें:","amount":"राशि","you_deposit":"आप जमा करते हैं","total_to_send":"कुल भेजें","send_exactly":"ठीक इतना भेजें","address":"पता","payment_id":"भुगतान आईडी","fee_notice":"~{pct}% प्रोसेसिंग शुल्क शामिल।","send_correct_network":"केवल सही नेटवर्क पर भेजें।","invoice_valid":"इनवॉइस 60 मिनट के लिए मान्य।","credit_notice":"आपका बैलेंस 1–3 मिनट में स्वतः जमा हो जाएगा।","copy_address":"पता कॉपी करें","check_status":"स्थिति जांचें","your_orders":"आपके ऑर्डर","no_orders":"अभी कोई ऑर्डर नहीं","no_orders_desc":"अनुरोध शुरू करने के लिए उपलब्धता ब्राउज़ करें।","status":"स्थिति","profile_title":"प्रोफ़ाइल","name":"नाम","id":"आईडी","user_status":"स्थिति","active":"✅ सक्रिय","banned":"🚫 प्रतिबंधित","order_summary":"🛒 ऑर्डर सारांश","country":"देश","quantity":"मात्रा","total_price":"कुल कीमत","your_balance":"आपका वॉलेट बैलेंस","sufficient":"✅ पर्याप्त","insufficient":"❌ अपर्याप्त","confirm_purchase":"✅ खरीद की पुष्टि करें","change_quantity":"मात्रा बदलें","account_s":"खाता/खाते","click_confirm":"ऑर्डर पूरा करने के लिए 'खरीद की पुष्टि करें' पर क्लिक करें।","not_enough":"आपके पास पर्याप्त बैलेंस नहीं है। कृपया पहले फंड्स जमा करें।","purchasing":"{country} से {qty} नंबर खरीद रहे हैं...","please_wait":"कृपया प्रतीक्षा करें।","numbers_purchased":"✅ नंबर खरीदे गए","order_id":"ऑर्डर आईडी","total_paid":"कुल भुगतान","your_numbers":"आपके नंबर","click_get_code":"प्रत्येक नंबर का लॉगिन कोड प्राप्त करने के लिए '📩 कोड प्राप्त करें' पर क्लिक करें।","get_code":"📩 कोड प्राप्त करें","get_code_n":"📩 नंबर #{n} के लिए कोड प्राप्त करें","view_my_orders":"मेरे ऑर्डर देखें","fetching_code":"कोड प्राप्त कर रहे हैं","code_received":"✅ खाता #{n} के लिए कोड प्राप्त हुआ","number":"नंबर","code":"कोड","password":"पासवर्ड","code_login":"इस नंबर से Telegram में लॉगिन करें, फिर कोड और पासवर्ड उपयोग करें।","retry":"🔄 पुनः प्रयास","failed":"विफल","language_title":"🌍 अपनी भाषा चुनें","language_set":"✅ भाषा बदलकर {name} कर दी गई","deposit_confirmed":"✅ जमा की पुष्टि हुई!","new_balance":"नया बैलेंस","admin_title":"🛠 एडमिन पैनल","total_users":"कुल उपयोगकर्ता","banned_users":"प्रतिबंधित उपयोगकर्ता","total_orders":"कुल ऑर्डर","total_deposits":"कुल जमा","total_spent":"कुल खर्च","total_profit":"कुल लाभ","user_balances":"उपयोगकर्ता बैलेंस (बकाया)","profit_margin":"लाभ मार्जिन","select_action":"नीचे एक क्रिया चुनें:","admin_users":"👥 उपयोगकर्ता","admin_orders":"📦 ऑर्डर","credit_user":"💳 उपयोगकर्ता को क्रेडिट करें","debit_user":"💸 उपयोगकर्ता से डेबिट करें","ban_user":"🚫 उपयोगकर्ता को प्रतिबंधित करें","unban_user":"✅ प्रतिबंध हटाएं","set_margin":"📊 लाभ मार्जिन सेट करें","broadcast":"प्रसारण","credit_prompt":"प्रारूप:\n<code>user_id amount</code>\n\nउदाहरण: <code>123456789 5</code>","debit_prompt":"प्रारूप:\n<code>user_id amount</code>\n\nउदाहरण: <code>123456789 2</code>","ban_prompt":"प्रतिबंधित करने के लिए उपयोगकर्ता आईडी भेजें।","unban_prompt":"प्रतिबंध हटाने के लिए उपयोगकर्ता आईडी भेजें।","margin_prompt":"वर्तमान: <b>{pct}%</b>\n\nनया मार्जिन प्रतिशत के रूप में भेजें।\nउदाहरण: <code>50</code>","broadcast_prompt":"प्रसारित करने के लिए संदेश भेजें।\n\nप्रीमियम इमोजी के लिए <code>&lt;emoji:ID&gt;</code> का उपयोग करें।","invalid_input":"अमान्य इनपुट।","invalid_amount":"अमान्य राशि।","invalid_quantity":"अमान्य मात्रा।","min_deposit_err":"न्यूनतम जमा {amount} है।","session_expired":"सत्र समाप्त। फिर से शुरू करें।","unauthorized":"❌ अनधिकृत।","banned_msg":"🚫 आप इस बॉट का उपयोग करने से प्रतिबंधित हैं।","code_failed":"कोड प्राप्त करने में विफल","error_service":"सेवा अस्थायी रूप से अनुपलब्ध है।","invoice_expired":"आपका जमा इनवॉइस समाप्त हो गया","start_over":"नया शुरू करने के लिए वॉलेट में 'फंड्स जमा करें' टैप करें।"},
"ru":{"name":"Русский","flag":"🇷🇺","welcome":"Ваш баланс","select_option":"Выберите пункт меню ниже:","browse_desc":"Просматривайте и покупайте проверенные аккаунты Telegram.","features":"Мгновенная доставка · Безопасная оплата · Поддержка 24/7","browse_accounts":"Аккаунты","wallet":"Кошелёк","my_orders":"Мои заказы","profile":"Профиль","language":"Язык","support":"Поддержка","admin_panel":"🛠 Админ-панель","back_home":"На главную","back_avail":"Назад к наличию","back_admin":"🛠 Назад к админу","available_inventory":"Доступный запас","select_country":"Выберите страну, чтобы увидеть количество и подать заявку.","showing_page":"Стр. {page} из {total} · {shown} из {total_c} стран","enter_qty":"Введите количество","price_per_account":"Цена за аккаунт","available_stock":"Доступно","tap_qty":"Нажмите ниже, чтобы ввести количество.","send_qty":"Отправьте количество числом.","example_3":"Пример: 3","your_wallet":"Ваш кошелёк","balance":"Баланс","tap_deposit":"Нажмите «Пополнить», чтобы добавить баланс.","deposit_funds":"Пополнить","enter_amount":"Введите сумму пополнения числом.","minimum":"Минимум","example_5":"Пример: 5","select_network":"Выберите сеть:","amount":"Сумма","you_deposit":"Вы пополняете","total_to_send":"Всего к отправке","send_exactly":"Отправьте ровно","address":"Адрес","payment_id":"ID платежа","fee_notice":"Включает ~{pct}% комиссии за обработку.","send_correct_network":"Отправляйте только в правильной сети.","invoice_valid":"Счёт действителен 60 минут.","credit_notice":"Баланс зачислится автоматически в течение 1–3 минут.","copy_address":"Копировать адрес","check_status":"Проверить статус","your_orders":"Ваши заказы","no_orders":"Заказов пока нет","no_orders_desc":"Просмотрите наличие, чтобы начать.","status":"Статус","profile_title":"Профиль","name":"Имя","id":"ID","user_status":"Статус","active":"✅ Активен","banned":"🚫 Заблокирован","order_summary":"🛒 Сводка заказа","country":"Страна","quantity":"Количество","total_price":"Итоговая цена","your_balance":"Ваш баланс","sufficient":"✅ Достаточно","insufficient":"❌ Недостаточно","confirm_purchase":"✅ Подтвердить покупку","change_quantity":"Изменить количество","account_s":"аккаунт(ов)","click_confirm":"Нажмите «Подтвердить покупку» для завершения.","not_enough":"Недостаточно средств. Пополните баланс.","purchasing":"Покупка {qty} номер(ов) из {country}...","please_wait":"Подождите.","numbers_purchased":"✅ Номера куплены","order_id":"ID заказа","total_paid":"Всего оплачено","your_numbers":"Ваши номера","click_get_code":"Нажмите «📩 Получить код» для каждого номера.","get_code":"📩 Получить код","get_code_n":"📩 Код для #{n}","view_my_orders":"Мои заказы","fetching_code":"Получение кода для","code_received":"✅ Код получен для аккаунта #{n}","number":"Номер","code":"Код","password":"Пароль","code_login":"Войдите в Telegram с этим номером, затем используйте код и пароль.","retry":"🔄 Повторить","failed":"Ошибка","language_title":"🌍 Выберите язык","language_set":"✅ Язык изменён на {name}","deposit_confirmed":"✅ Депозит подтверждён!","new_balance":"Новый баланс","admin_title":"🛠 Админ-панель","total_users":"Всего пользователей","banned_users":"Заблокировано","total_orders":"Всего заказов","total_deposits":"Всего депозитов","total_spent":"Всего потрачено","total_profit":"Всего прибыли","user_balances":"Балансы пользователей","profit_margin":"Маржа","select_action":"Выберите действие:","admin_users":"👥 Пользователи","admin_orders":"📦 Заказы","credit_user":"💳 Пополнить","debit_user":"💸 Списать","ban_user":"🚫 Заблокировать","unban_user":"✅ Разблокировать","set_margin":"📊 Установить маржу","broadcast":"Рассылка","credit_prompt":"Формат:\n<code>user_id amount</code>\n\nПример: <code>123456789 5</code>","debit_prompt":"Формат:\n<code>user_id amount</code>\n\nПример: <code>123456789 2</code>","ban_prompt":"Отправьте ID для блокировки.","unban_prompt":"Отправьте ID для разблокировки.","margin_prompt":"Текущая: <b>{pct}%</b>\n\nОтправьте новую маржу в %.\nПример: <code>50</code>","broadcast_prompt":"Отправьте сообщение для рассылки.\n\nИспользуйте <code>&lt;emoji:ID&gt;</code> для премиум-эмодзи.","invalid_input":"Неверный ввод.","invalid_amount":"Неверная сумма.","invalid_quantity":"Неверное количество.","min_deposit_err":"Минимум {amount}.","session_expired":"Сессия истекла.","unauthorized":"❌ Не авторизован.","banned_msg":"🚫 Вы заблокированы.","code_failed":"Ошибка получения кода","error_service":"Сервис временно недоступен.","invoice_expired":"Счёт на депозит истёк","start_over":"Нажмите «Пополнить» в Кошельке, чтобы создать новый."},
"ar":{"name":"العربية","flag":"🇸🇦","welcome":"رصيدك","select_option":"اختر خياراً من القائمة أدناه:","browse_desc":"تصفح واشترِ حسابات Telegram الموثّقة.","features":"تسليم فوري · دفع آمن · دعم 24/7","browse_accounts":"تصفح الحسابات","wallet":"المحفظة","my_orders":"طلباتي","profile":"الملف","language":"اللغة","support":"الدعم","admin_panel":"🛠 لوحة الإدارة","back_home":"العودة للرئيسية","back_avail":"العودة للتوفر","back_admin":"🛠 العودة للإدارة","available_inventory":"المخزون المتاح","select_country":"اختر دولة لعرض الكمية وتقديم الطلب.","showing_page":"صفحة {page} من {total} · {shown} من {total_c}","enter_qty":"أدخل الكمية","price_per_account":"السعر لكل حساب","available_stock":"المخزون","tap_qty":"انقر أدناه لإدخال الكمية.","send_qty":"أرسل الكمية كرقم.","example_3":"مثال: 3","your_wallet":"محفظتك","balance":"الرصيد","tap_deposit":"انقر «إيداع» لإضافة رصيد.","deposit_funds":"إيداع","enter_amount":"أدخل المبلغ كرقم.","minimum":"الحد الأدنى","example_5":"مثال: 5","select_network":"اختر الشبكة:","amount":"المبلغ","you_deposit":"أنت تودع","total_to_send":"الإجمالي","send_exactly":"أرسل بالضبط","address":"العنوان","payment_id":"معرّف الدفع","fee_notice":"يشمل ~{pct}% رسوم معالجة.","send_correct_network":"أرسل على الشبكة الصحيحة فقط.","invoice_valid":"الفاتورة صالحة 60 دقيقة.","credit_notice":"سيُضاف رصيدك تلقائياً خلال 1–3 دقائق.","copy_address":"نسخ العنوان","check_status":"تحقق من الحالة","your_orders":"طلباتك","no_orders":"لا طلبات بعد","no_orders_desc":"تصفح التوفر لبدء طلب.","status":"الحالة","profile_title":"الملف","name":"الاسم","id":"المعرّف","user_status":"الحالة","active":"✅ نشط","banned":"🚫 محظور","order_summary":"🛒 ملخص الطلب","country":"الدولة","quantity":"الكمية","total_price":"الإجمالي","your_balance":"رصيدك","sufficient":"✅ كافٍ","insufficient":"❌ غير كافٍ","confirm_purchase":"✅ تأكيد الشراء","change_quantity":"تغيير الكمية","account_s":"حساب/حسابات","click_confirm":"انقر «تأكيد الشراء» لإتمام الطلب.","not_enough":"رصيدك غير كافٍ. أودع أولاً.","purchasing":"جارٍ شراء {qty} من {country}...","please_wait":"يرجى الانتظار.","numbers_purchased":"✅ تم شراء الأرقام","order_id":"معرّف الطلب","total_paid":"المدفوع","your_numbers":"أرقامك","click_get_code":"انقر «📩 الحصول على الرمز» لكل رقم.","get_code":"📩 الحصول على الرمز","get_code_n":"📩 الرمز لـ #{n}","view_my_orders":"طلباتي","fetching_code":"جارٍ إحضار الرمز لـ","code_received":"✅ تم استلام الرمز للحساب #{n}","number":"الرقم","code":"الرمز","password":"كلمة المرور","code_login":"سجّل في Telegram بهذا الرقم ثم استخدم الرمز وكلمة المرور.","retry":"🔄 إعادة","failed":"فشل","language_title":"🌍 اختر لغتك","language_set":"✅ تم تغيير اللغة إلى {name}","deposit_confirmed":"✅ تم تأكيد الإيداع!","new_balance":"الرصيد الجديد","admin_title":"🛠 لوحة الإدارة","total_users":"إجمالي المستخدمين","banned_users":"المحظورون","total_orders":"إجمالي الطلبات","total_deposits":"إجمالي الإيداعات","total_spent":"إجمالي المصروف","total_profit":"إجمالي الربح","user_balances":"أرصدة المستخدمين","profit_margin":"هامش الربح","select_action":"اختر إجراءً:","admin_users":"👥 المستخدمون","admin_orders":"📦 الطلبات","credit_user":"💳 إضافة رصيد","debit_user":"💸 خصم رصيد","ban_user":"🚫 حظر","unban_user":"✅ إلغاء الحظر","set_margin":"📊 تعيين الهامش","broadcast":"بث","credit_prompt":"أرسل بالصيغة:\n<code>user_id amount</code>\n\nمثال: <code>123456789 5</code>","debit_prompt":"أرسل بالصيغة:\n<code>user_id amount</code>\n\nمثال: <code>123456789 2</code>","ban_prompt":"أرسل معرّف المستخدم للحظر.","unban_prompt":"أرسل معرّف المستخدم لإلغاء الحظر.","margin_prompt":"الحالي: <b>{pct}%</b>\n\nأرسل الهامش الجديد بنسبة مئوية.\nمثال: <code>50</code>","broadcast_prompt":"أرسل الرسالة للبث.\n\nاستخدم <code>&lt;emoji:ID&gt;</code> لإيموجي مميز.","invalid_input":"إدخال غير صالح.","invalid_amount":"مبلغ غير صالح.","invalid_quantity":"كمية غير صالحة.","min_deposit_err":"الحد الأدنى {amount}.","session_expired":"انتهت الجلسة.","unauthorized":"❌ غير مصرح.","banned_msg":"🚫 أنت محظور.","code_failed":"فشل جلب الرمز","error_service":"الخدمة غير متاحة مؤقتاً.","invoice_expired":"انتهت صلاحية فاتورة الإيداع","start_over":"انقر «إيداع» في المحفظة لبدء واحدة جديدة."},
"es":{"name":"Español","flag":"🇪🇸","welcome":"Tu saldo","select_option":"Selecciona una opción del menú:","browse_desc":"Explora y compra cuentas de Telegram verificadas.","features":"Entrega instantánea · Pago seguro · Soporte 24/7","browse_accounts":"Explorar cuentas","wallet":"Cartera","my_orders":"Mis pedidos","profile":"Perfil","language":"Idioma","support":"Soporte","admin_panel":"🛠 Panel de admin","back_home":"Volver al inicio","back_avail":"Volver a disponibilidad","back_admin":"🛠 Volver a admin","available_inventory":"Inventario disponible","select_country":"Selecciona un país para ver cantidad y enviar una solicitud.","showing_page":"Página {page} de {total} · {shown} de {total_c} países","enter_qty":"Ingresar cantidad","price_per_account":"Precio por cuenta","available_stock":"Stock disponible","tap_qty":"Toca abajo para ingresar la cantidad.","send_qty":"Envía la cantidad como número.","example_3":"Ejemplo: 3","your_wallet":"Tu cartera","balance":"Saldo","tap_deposit":"Toca «Depositar» para añadir saldo.","deposit_funds":"Depositar","enter_amount":"Ingresa el monto como número.","minimum":"Mínimo","example_5":"Ejemplo: 5","select_network":"Selecciona tu red:","amount":"Monto","you_deposit":"Depositas","total_to_send":"Total a enviar","send_exactly":"Envía exactamente","address":"Dirección","payment_id":"ID de pago","fee_notice":"Incluye ~{pct}% de comisión.","send_correct_network":"Envía solo en la red correcta.","invoice_valid":"Factura válida 60 minutos.","credit_notice":"El saldo se acreditará en 1–3 minutos.","copy_address":"Copiar dirección","check_status":"Ver estado","your_orders":"Tus pedidos","no_orders":"Sin pedidos aún","no_orders_desc":"Explora disponibilidad para empezar.","status":"Estado","profile_title":"Perfil","name":"Nombre","id":"ID","user_status":"Estado","active":"✅ Activo","banned":"🚫 Bloqueado","order_summary":"🛒 Resumen del pedido","country":"País","quantity":"Cantidad","total_price":"Precio total","your_balance":"Tu saldo","sufficient":"✅ Suficiente","insufficient":"❌ Insuficiente","confirm_purchase":"✅ Confirmar compra","change_quantity":"Cambiar cantidad","account_s":"cuenta(s)","click_confirm":"Toca «Confirmar compra» para completar.","not_enough":"Saldo insuficiente. Deposita primero.","purchasing":"Comprando {qty} de {country}...","please_wait":"Espera por favor.","numbers_purchased":"✅ Números comprados","order_id":"ID de pedido","total_paid":"Total pagado","your_numbers":"Tus números","click_get_code":"Toca «📩 Obtener código» para cada número.","get_code":"📩 Obtener código","get_code_n":"📩 Código para #{n}","view_my_orders":"Ver mis pedidos","fetching_code":"Obteniendo código para","code_received":"✅ Código recibido para cuenta #{n}","number":"Número","code":"Código","password":"Contraseña","code_login":"Inicia sesión en Telegram con este número y usa el código y la contraseña.","retry":"🔄 Reintentar","failed":"Falló","language_title":"🌍 Elige tu idioma","language_set":"✅ Idioma cambiado a {name}","deposit_confirmed":"✅ ¡Depósito confirmado!","new_balance":"Nuevo saldo","admin_title":"🛠 Panel de admin","total_users":"Total de usuarios","banned_users":"Usuarios bloqueados","total_orders":"Total de pedidos","total_deposits":"Total de depósitos","total_spent":"Total gastado","total_profit":"Total ganado","user_balances":"Saldos de usuarios","profit_margin":"Margen de ganancia","select_action":"Selecciona una acción:","admin_users":"👥 Usuarios","admin_orders":"📦 Pedidos","credit_user":"💳 Acreditar","debit_user":"💸 Debitar","ban_user":"🚫 Bloquear","unban_user":"✅ Desbloquear","set_margin":"📊 Establecer margen","broadcast":"Difusión","credit_prompt":"Formato:\n<code>user_id amount</code>\n\nEjemplo: <code>123456789 5</code>","debit_prompt":"Formato:\n<code>user_id amount</code>\n\nEjemplo: <code>123456789 2</code>","ban_prompt":"Envía el ID a bloquear.","unban_prompt":"Envía el ID a desbloquear.","margin_prompt":"Actual: <b>{pct}%</b>\n\nEnvía el nuevo margen en %.\nEjemplo: <code>50</code>","broadcast_prompt":"Envía el mensaje para difundir.\n\nUsa <code>&lt;emoji:ID&gt;</code> para emoji premium.","invalid_input":"Entrada inválida.","invalid_amount":"Monto inválido.","invalid_quantity":"Cantidad inválida.","min_deposit_err":"El mínimo es {amount}.","session_expired":"Sesión expirada.","unauthorized":"❌ No autorizado.","banned_msg":"🚫 Estás bloqueado.","code_failed":"Error al obtener código","error_service":"Servicio temporalmente no disponible.","invoice_expired":"Tu factura de depósito expiró","start_over":"Toca «Depositar» en la Cartera para iniciar una nueva."},
"fr":{"name":"Français","flag":"🇫🇷","welcome":"Votre solde","select_option":"Sélectionnez une option du menu :","browse_desc":"Parcourez et achetez des comptes Telegram vérifiés.","features":"Livraison instantanée · Paiement sécurisé · Support 24/7","browse_accounts":"Parcourir les comptes","wallet":"Portefeuille","my_orders":"Mes commandes","profile":"Profil","language":"Langue","support":"Support","admin_panel":"🛠 Panneau admin","back_home":"Retour à l'accueil","back_avail":"Retour aux disponibilités","back_admin":"🛠 Retour admin","available_inventory":"Inventaire disponible","select_country":"Sélectionnez un pays pour voir la quantité et faire une demande.","showing_page":"Page {page} sur {total} · {shown} sur {total_c} pays","enter_qty":"Entrer la quantité","price_per_account":"Prix par compte","available_stock":"Stock disponible","tap_qty":"Touchez ci-dessous pour entrer la quantité.","send_qty":"Envoyez la quantité sous forme de nombre.","example_3":"Exemple : 3","your_wallet":"Votre portefeuille","balance":"Solde","tap_deposit":"Touchez « Déposer » pour ajouter du solde.","deposit_funds":"Déposer","enter_amount":"Entrez le montant sous forme de nombre.","minimum":"Minimum","example_5":"Exemple : 5","select_network":"Sélectionnez votre réseau :","amount":"Montant","you_deposit":"Vous déposez","total_to_send":"Total à envoyer","send_exactly":"Envoyez exactement","address":"Adresse","payment_id":"ID de paiement","fee_notice":"Inclut ~{pct}% de frais de traitement.","send_correct_network":"Envoyez uniquement sur le bon réseau.","invoice_valid":"Facture valable 60 minutes.","credit_notice":"Le solde sera crédité en 1–3 minutes.","copy_address":"Copier l'adresse","check_status":"Vérifier le statut","your_orders":"Vos commandes","no_orders":"Aucune commande","no_orders_desc":"Parcourez les disponibilités pour commencer.","status":"Statut","profile_title":"Profil","name":"Nom","id":"ID","user_status":"Statut","active":"✅ Actif","banned":"🚫 Banni","order_summary":"🛒 Résumé de la commande","country":"Pays","quantity":"Quantité","total_price":"Prix total","your_balance":"Votre solde","sufficient":"✅ Suffisant","insufficient":"❌ Insuffisant","confirm_purchase":"✅ Confirmer l'achat","change_quantity":"Changer la quantité","account_s":"compte(s)","click_confirm":"Touchez « Confirmer l'achat » pour finaliser.","not_enough":"Solde insuffisant. Déposez d'abord.","purchasing":"Achat de {qty} de {country}...","please_wait":"Veuillez patienter.","numbers_purchased":"✅ Numéros achetés","order_id":"ID de commande","total_paid":"Total payé","your_numbers":"Vos numéros","click_get_code":"Touchez « 📩 Obtenir le code » pour chaque numéro.","get_code":"📩 Obtenir le code","get_code_n":"📩 Code pour #{n}","view_my_orders":"Voir mes commandes","fetching_code":"Récupération du code pour","code_received":"✅ Code reçu pour le compte #{n}","number":"Numéro","code":"Code","password":"Mot de passe","code_login":"Connectez-vous à Telegram avec ce numéro puis utilisez le code et le mot de passe.","retry":"🔄 Réessayer","failed":"Échec","language_title":"🌍 Choisissez votre langue","language_set":"✅ Langue changée en {name}","deposit_confirmed":"✅ Dépôt confirmé !","new_balance":"Nouveau solde","admin_title":"🛠 Panneau admin","total_users":"Total des utilisateurs","banned_users":"Utilisateurs bannis","total_orders":"Total des commandes","total_deposits":"Total des dépôts","total_spent":"Total dépensé","total_profit":"Total des bénéfices","user_balances":"Soldes des utilisateurs","profit_margin":"Marge bénéficiaire","select_action":"Sélectionnez une action :","admin_users":"👥 Utilisateurs","admin_orders":"📦 Commandes","credit_user":"💳 Créditer","debit_user":"💸 Débiter","ban_user":"🚫 Bannir","unban_user":"✅ Débannir","set_margin":"📊 Définir la marge","broadcast":"Diffusion","credit_prompt":"Format :\n<code>user_id amount</code>\n\nExemple : <code>123456789 5</code>","debit_prompt":"Format :\n<code>user_id amount</code>\n\nExemple : <code>123456789 2</code>","ban_prompt":"Envoyez l'ID à bannir.","unban_prompt":"Envoyez l'ID à débannir.","margin_prompt":"Actuelle : <b>{pct}%</b>\n\nEnvoyez la nouvelle marge en %.\nExemple : <code>50</code>","broadcast_prompt":"Envoyez le message à diffuser.\n\nUtilisez <code>&lt;emoji:ID&gt;</code> pour un emoji premium.","invalid_input":"Entrée invalide.","invalid_amount":"Montant invalide.","invalid_quantity":"Quantité invalide.","min_deposit_err":"Le minimum est {amount}.","session_expired":"Session expirée.","unauthorized":"❌ Non autorisé.","banned_msg":"🚫 Vous êtes banni.","code_failed":"Échec de récupération du code","error_service":"Service temporairement indisponible.","invoice_expired":"Votre facture de dépôt a expiré","start_over":"Touchez « Déposer » dans le Portefeuille pour en créer une nouvelle."},
}

user_languages:dict[int,str]={}
def get_user_lang(user_id):return user_languages.get(user_id,"en")
def set_user_lang(user_id,lang):user_languages[user_id]=lang
def t(key,lang="en",**kwargs):
    pack=LANGUAGES.get(lang,LANGUAGES["en"]);text=pack.get(key) or LANGUAGES["en"].get(key) or key
    if kwargs:
        try:return text.format(**kwargs)
        except Exception:return text
    return text

PREMIUM_CART_ID="5330237710655306682";PREMIUM_WALLET_ID="6321327299975193112";PREMIUM_ORDERS_ID="6323577059679411036";PREMIUM_PROFILE_ID="6321081949968408088";PREMIUM_SUPPORT_ID="6321290835702848605";PREMIUM_BACK_ID="5346230992044574063";PREMIUM_LANGUAGE_ID="5440790690920518829";PREMIUM_TRC20_ID="5249397011576285879";PREMIUM_ERC20_ID="5249397011576285879";PREMIUM_BEP20_ID="5249397011576285879";PREMIUM_ETH_ID="5253656592636733661";PREMIUM_SOL_ID="5251414920355931519";PREMIUM_BALANCE_ID="6321023044491944284";PREMIUM_SEARCH_ID="6320891313550008431";PREMIUM_ORDERS_HEADER_ID="6321311215322669245";PREMIUM_DEPOSIT_ID="5343777479091831702";PREMIUM_PRICE_ID="6321327299975193112";PREMIUM_STOCK_ID="5350291836378307462";PREMIUM_ADMIN_HEADER_ID="6321147508349216659";PREMIUM_USERS_ID="6321311215322669245";PREMIUM_BAN_ID="6320947418707794947";PREMIUM_BROADCAST_ID="6320924792820081741"
PAGE_PREMIUM_EMOJIS={1:"5235776368905562305",2:"5237704680372447424",3:"5238044171767393675",4:"5235533321001250232",5:"5238171599152097811",6:"5235500881113263583",7:"5237875542761417785",8:"5238067300166281132",9:"5237872922831367023",10:""}
COUNTRY_PREMIUM_EMOJIS={"IN":"","US":"","NG":"","BD":"","CO":"","ID":"","NE":"","ET":"","AF":"","PH":"","KE":"","CL":"","ZA":"","GB":"","MA":"","PK":"","UG":"","NA":"","YE":""}
NETWORK_TO_CURRENCY={"trc20":("TRC20 (Tron) — USDT","usdttrc20"),"bep20":("BEP20 (BNB Chain) — USDT","usdtbsc"),"erc20":("ERC20 (Ethereum) — USDT","usdterc20"),"eth":("ETH (Ethereum) — Native","eth"),"sol":("SOL (Solana) — Native","sol")}
LANG_TO_USER_PICK={"en":("English","🇬🇧"),"hi":("हिन्दी","🇮🇳"),"ru":("Русский","🇷🇺"),"ar":("العربية","🇸🇦"),"es":("Español","🇪🇸"),"fr":("Français","🇫🇷")}
pending_custom_quantity={};pending_custom_deposit={};pending_admin_input={};pending_deposit_selection={};last_message_id={}
profit_margin=0.50
@dataclass(frozen=True)
class Country:
    code:str;name:str;quantity:int;price_usd:float
@dataclass
class Order:
    order_id:str;telegram_user_id:int;country_code:str;country_name:str;quantity:int;amount_usd:float;base_cost:float;profit:float;status:str;payment_method:str;created_at:str

def start_health_server():
    port=int(os.getenv("PORT","10000"))
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):self.send_response(200);self.send_header("Content-Type","text/plain");self.end_headers();self.wfile.write(b"Bot is running")
        def log_message(self,*args):pass
    try:
        with socketserver.TCPServer(("0.0.0.0",port),Handler) as httpd:print(f"[Health] Listening on port {port}",flush=True);httpd.serve_forever()
    except Exception as e:print(f"[Health] Server error: {e}",flush=True)

def db_call(path,payload=None,timeout=15):
    url=f"{WORKER_URL}/{path}";body=json.dumps(payload or {}).encode("utf-8")
    req=urllib.request.Request(url,data=body,headers={"Authorization":f"Bearer {WORKER_TOKEN}","Content-Type":"application/json","Accept":"application/json","User-Agent":"TG-Lion-Bot/2.0"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:print(f"[DB] {path} HTTP {e.code}",flush=True);return {"error":str(e)}
    except Exception as e:print(f"[DB] {path} error: {e}",flush=True);return {"error":str(e)}

def db_user_upsert(user_id,first_name=None):db_call("user/upsert",{"user_id":user_id,"first_name":first_name or ""})
def db_user_get(user_id):return db_call("user/get",{"user_id":user_id}).get("user")
def db_user_add_balance(user_id,delta):return db_call("user/add_balance",{"user_id":user_id,"delta":delta}).get("balance",0.0)
def db_user_set_balance(user_id,balance):db_call("user/set_balance",{"user_id":user_id,"balance":balance})
def db_user_ban(user_id,banned):db_call("user/ban" if banned else "user/unban",{"user_id":user_id})
def db_user_all():return db_call("user/all",{}).get("users",[])
def db_order_create(order):db_call("order/create",{"order_id":order.order_id,"user_id":order.telegram_user_id,"country_code":order.country_code,"country_name":order.country_name,"quantity":order.quantity,"amount_usd":order.amount_usd,"base_cost":order.base_cost,"profit":order.profit,"status":order.status,"payment_method":order.payment_method,"created_at":int(order.created_at)})
def db_order_update_status(order_id,status):db_call("order/update",{"order_id":order_id,"status":status})
def db_order_list(user_id,limit=8):return db_call("order/list",{"user_id":user_id,"limit":limit}).get("orders",[])
def db_order_recent():return db_call("order/recent",{}).get("orders",[])
def db_order_count():return db_call("order/count",{}).get("count",0)
def db_number_save(order_id,phone,code=None,password=None):db_call("number/save",{"order_id":order_id,"phone":phone,"code":code,"password":password})
def db_number_list(order_id):return db_call("number/list",{"order_id":order_id}).get("numbers",[])
def db_number_mark(number_id,code,password):db_call("number/mark",{"id":number_id,"code":code,"password":password})
def db_payment_create(payment_id,order_id,user_id,amount_usd,status,pay_address="",pay_amount=0.0,pay_currency=""):db_call("payment/create",{"payment_id":payment_id,"order_id":order_id,"user_id":user_id,"amount_usd":amount_usd,"status":status,"pay_address":pay_address,"pay_amount":pay_amount,"pay_currency":pay_currency,"created_at":int(time.time())})
def db_payment_get(payment_id):return db_call("payment/get",{"payment_id":payment_id}).get("payment")
def db_payment_pending_notify():return db_call("payment/pending_notify",{}).get("payments",[])
def db_payment_mark_notified(payment_id):db_call("payment/mark_notified",{"payment_id":payment_id})
def db_settings_get(key):return db_call("settings/get",{"key":key}).get("value")
def db_settings_set(key,value):db_call("settings/set",{"key":key,"value":value})
def db_stats_get():return db_call("stats/get",{}).get("stats",{})
def db_stats_incr(key,delta):db_call("stats/incr",{"key":key,"delta":delta})

def request_json(url,*,payload=None,headers=None,timeout=35,context="request"):
    body=None;h={"Accept":"application/json","User-Agent":"TG-Lion-Bot/1.0"}
    if headers:h.update(headers)
    if payload is not None:body=json.dumps(payload).encode("utf-8");h["Content-Type"]="application/json"
    request=urllib.request.Request(url,data=body,headers=h,method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response:return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail=""
        try:
            b=json.loads(error.read().decode("utf-8"))
            if isinstance(b,dict):
                m=b.get("description") or b.get("message") or b.get("error") or b.get("detail")
                if m:detail=f" {m}"
        except Exception:pass
        print(f"[HTTP {error.code}] {context}:{detail}",flush=True)
        raise RuntimeError(f"{context} failed: HTTP {error.code}.{detail}") from error
    except urllib.error.URLError as error:raise RuntimeError(f"{context} network error: {getattr(error,'reason','unknown')}") from error
    except Exception as error:raise RuntimeError(f"{context} error: {error}") from error

def telegram(method,payload=None):
    response=request_json(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}",payload=payload or {},timeout=40,context=f"Telegram {method}")
    if not response.get("ok"):raise RuntimeError(f"Telegram API request failed for {method}.")
    return response.get("result")

def tg_lion(action,extra=None):
    params={"action":action,"apiKey":TG_LION_API_KEY,"YourID":TG_LION_USER_ID};params.update(extra or {})
    return request_json(f"https://tg-lion.net/?{urllib.parse.urlencode(params)}",timeout=25,context=f"TG-Lion {action}")

def escape(value):return html.escape(str(value),quote=False)
def money(value):return f"${value:.2f}"
def pemoji(emoji_id,fallback):
    if not emoji_id or not str(emoji_id).isdigit():return fallback
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'
def get_flag_emoji(code):
    c=code.upper()
    if len(c)!=2:return ""
    return chr(0x1F1E6+ord(c[0])-ord("A"))+chr(0x1F1E6+ord(c[1])-ord("A"))
def error_text(error):return str(error) or "The service is temporarily unavailable."
def is_admin(user_id):return user_id in ADMIN_IDS
def apply_margin(base_price):return round(base_price*(1+profit_margin),2)
def register_user(user_id,first_name):
    try:db_user_upsert(user_id,first_name)
    except Exception as e:print(f"[DB] register_user error: {e}",flush=True)
def get_balance(user_id):
    u=db_user_get(user_id);return float(u.get("balance",0.0)) if u else 0.0
def is_banned(user_id):
    u=db_user_get(user_id);return bool(u and u.get("banned"))
def add_balance(user_id,delta):return float(db_user_add_balance(user_id,delta))

def nowpayments_create_payment(user_id,amount_usd,network):
    if network not in NETWORK_TO_CURRENCY:raise RuntimeError(f"Unsupported network: {network}")
    _,pay_currency=NETWORK_TO_CURRENCY[network];order_id=f"TL-{uuid.uuid4().hex[:8].upper()}"
    charged_amount=round(amount_usd*(1+NOWPAYMENTS_FEE_BUFFER),2)
    payload={"price_amount":charged_amount,"price_currency":"usd","pay_currency":pay_currency,"order_id":order_id,"order_description":f"Deposit for user {user_id}","ipn_callback_url":f"{WORKER_URL}/payment/webhook","payout_address":NOWPAYMENTS_PAYOUT_ADDRESS,"payout_currency":NOWPAYMENTS_PAYOUT_CURRENCY,"is_fixed_rate":False,"is_fee_paid_by_user":False}
    resp=request_json("https://api.nowpayments.io/v1/payment",payload=payload,headers={"x-api-key":NOWPAYMENTS_API_KEY},timeout=25,context="NOWPayments create_payment")
    return {"order_id":order_id,"payment_id":str(resp.get("payment_id","")),"pay_address":resp.get("pay_address",""),"pay_amount":float(resp.get("pay_amount",0)),"pay_currency":resp.get("pay_currency",pay_currency),"price_amount":charged_amount,"credit_amount":amount_usd,"payment_status":resp.get("payment_status","waiting")}

def nowpayments_get_status(payment_id):
    return request_json(f"https://api.nowpayments.io/v1/payment/{payment_id}",headers={"x-api-key":NOWPAYMENTS_API_KEY},timeout=15,context="NOWPayments get_status")

def payment_notifier_worker():
    print("[Notify Worker] Started.",flush=True)
    while True:
        try:
            for p in db_payment_pending_notify():
                pid=p.get("payment_id");uid=p.get("user_id");amount=float(p.get("amount_usd",0))
                if not pid or not uid:continue
                try:
                    lang=get_user_lang(int(uid));new_bal=get_balance(int(uid))
                    send_message(int(uid),f"{t('deposit_confirmed',lang)}\n\n<b>{t('amount',lang)}:</b> {money(amount)}\n<b>{t('new_balance',lang)}:</b> {money(new_bal)}\n\n<i>{t('payment_id',lang)}: {escape(pid)}</i>")
                    db_payment_mark_notified(pid);print(f"[Notify Worker] Notified user {uid} of ${amount:.2f}",flush=True)
                except Exception as e:print(f"[Notify Worker] Failed for {uid}: {e}",flush=True)
        except Exception as e:print(f"[Notify Worker] Error: {e}",flush=True)
        time.sleep(POLL_INTERVAL)

def invoice_cleanup_worker():
    print("[Cleanup Worker] Started.",flush=True)
    while True:
        try:
            resp=db_call("payment/expire_old",{});expired=resp.get("expired",[])
            for p in expired:
                uid=p.get("user_id");amount=float(p.get("amount_usd",0) or 0)
                if not uid:continue
                try:
                    lang=get_user_lang(int(uid))
                    send_message(int(uid),f"⏰ <b>{t('invoice_expired',lang)}</b>\n\n<b>{t('amount',lang)}:</b> {money(amount)}\n\n<i>{t('start_over',lang)}</i>")
                    print(f"[Cleanup Worker] Notified user {uid} of expired invoice",flush=True)
                except Exception as e:print(f"[Cleanup Worker] Failed to notify {uid}: {e}",flush=True)
            if expired:print(f"[Cleanup Worker] Expired {len(expired)} unpaid invoices",flush=True)
        except Exception as e:print(f"[Cleanup Worker] Error: {e}",flush=True)
        time.sleep(INVOICE_CLEANUP_INTERVAL)

def send_message(chat_id,text,reply_markup=None):
    payload={"chat_id":chat_id,"text":text,"parse_mode":"HTML"}
    if reply_markup:payload["reply_markup"]=reply_markup
    telegram("sendMessage",payload)

def edit_message(chat_id,message_id,text,reply_markup=None):
    payload={"chat_id":chat_id,"message_id":message_id,"text":text,"parse_mode":"HTML"}
    if reply_markup:payload["reply_markup"]=reply_markup
    telegram("editMessageText",payload)

def send_or_edit(chat_id,text,reply_markup=None,force_new=False):
    mid=last_message_id.get(chat_id)
    if mid and not force_new:
        try:edit_message(chat_id,mid,text,reply_markup);return mid
        except Exception as e:print(f"[UI] edit failed: {e}",flush=True)
    try:
        result=telegram("sendMessage",{"chat_id":chat_id,"text":text,"parse_mode":"HTML","reply_markup":reply_markup} if reply_markup else {"chat_id":chat_id,"text":text,"parse_mode":"HTML"})
        if isinstance(result,dict) and result.get("message_id"):last_message_id[chat_id]=result["message_id"]
    except Exception as e:print(f"[UI] send failed: {e}",flush=True)
    return last_message_id.get(chat_id)

def get_countries():
    response=tg_lion("available_countries");raw=response.get("countries",{});countries=[]
    if not isinstance(raw,dict):return countries
    for fallback,val in raw.items():
        if not isinstance(val,dict):continue
        code=str(val.get("code") or fallback).strip().upper();name=str(val.get("name") or fallback).strip()
        try:qty,price=int(val["qty"]),float(val["price"])
        except (KeyError,TypeError,ValueError):continue
        if code and name and qty>=0 and price>=0:countries.append(Country(code,name,qty,price))
    return sorted(countries,key=lambda c:c.price_usd)

def find_country(code):return next((c for c in get_countries() if c.code==code.upper()),None)

def buy_number(country_code):
    resp=tg_lion("getNumber",{"country_code":country_code.lower()})
    if resp.get("status")!="ok":raise RuntimeError(f"TG-Lion rejected: {resp.get('message','Unknown')}")
    if not resp.get("Number"):raise RuntimeError("TG-Lion did not return a phone number.")
    if "new_balance" in resp:print(f"[TG-Lion] Owner balance: {resp['new_balance']}",flush=True)
    return {"status":resp["status"],"name":resp.get("name"),"Number":resp["Number"],"price":resp.get("price")}

def fetch_code(phone,max_attempts=20,delay=5):
    for _ in range(max_attempts):
        resp=tg_lion("getCode",{"number":phone});status=resp.get("status")
        if status=="ok" and resp.get("code"):return {"status":"ok","Number":resp.get("Number",phone),"code":resp["code"],"pass":resp.get("pass","N/A")}
        if status in ("wait","pending","waiting"):time.sleep(delay);continue
        if status=="error":raise RuntimeError(f"TG-Lion getCode error: {resp.get('message','Unknown')}")
        time.sleep(delay)
    raise RuntimeError(f"Code not received for {phone} after {max_attempts*delay}s.")

def main_menu_keyboard(user_id=None,lang="en"):
    rows=[[{"text":f" {t('browse_accounts',lang)}","callback_data":"menu:countries","icon_custom_emoji_id":PREMIUM_CART_ID}],
          [{"text":f" {t('wallet',lang)}","callback_data":"menu:wallet","icon_custom_emoji_id":PREMIUM_WALLET_ID},{"text":f" {t('my_orders',lang)}","callback_data":"menu:orders","icon_custom_emoji_id":PREMIUM_ORDERS_ID}],
          [{"text":f" {t('profile',lang)}","callback_data":"menu:profile","icon_custom_emoji_id":PREMIUM_PROFILE_ID},{"text":f" {t('language',lang)}","callback_data":"menu:language","icon_custom_emoji_id":PREMIUM_LANGUAGE_ID}],
          [{"text":f" {t('support',lang)}","url":SUPPORT_URL,"icon_custom_emoji_id":PREMIUM_SUPPORT_ID}]]
    if user_id and is_admin(user_id):rows.append([{"text":t('admin_panel',lang),"callback_data":"admin:panel"}])
    return {"inline_keyboard":rows}

def back_keyboard(lang="en"):return {"inline_keyboard":[[{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}]]}
def back_to_countries_keyboard(lang="en"):return {"inline_keyboard":[[{"text":t('back_avail',lang),"callback_data":"menu:countries","icon_custom_emoji_id":PREMIUM_BACK_ID}]]}
def admin_back_keyboard(lang="en"):return {"inline_keyboard":[[{"text":t('back_admin',lang),"callback_data":"admin:panel"}],[{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}]]}

def send_home(chat_id,first_name=None,user_id=None,force_new=False):
    lang=get_user_lang(user_id) if user_id else "en";bal=get_balance(user_id) if user_id else 0.0
    text="\n".join([f"{pemoji(PREMIUM_BALANCE_ID,'💰')} <b>{t('welcome',lang)}:</b> {money(bal)}",f"👇 {t('select_option',lang)}","",f"{pemoji(PREMIUM_SEARCH_ID,'✅')} {t('browse_desc',lang)}",f"⚡️ {t('features',lang)}"])
    send_or_edit(chat_id,text,main_menu_keyboard(user_id,lang),force_new=force_new)

def send_countries(chat_id,page=1,message_id=None,lang="en"):
    try:
        all_c=get_countries()
        if not all_c:raise RuntimeError("TG-Lion returned no available countries.")
        PER=18;total_pages=(len(all_c)+PER-1)//PER;page=max(1,min(page,total_pages))
        start=(page-1)*PER;page_c=all_c[start:start+PER];rows=[]
        for i in range(0,len(page_c),2):
            row=[]
            for c in page_c[i:i+2]:
                sp=apply_margin(c.price_usd);btn={"text":f"{get_flag_emoji(c.code)} {c.code} · {money(sp)}","callback_data":f"country:{c.code}"}
                if COUNTRY_PREMIUM_EMOJIS.get(c.code):btn["icon_custom_emoji_id"]=COUNTRY_PREMIUM_EMOJIS[c.code]
                row.append(btn)
            rows.append(row)
        pag=[]
        for p in range(1,total_pages+1):
            btn={"text":f"• {p} •" if p==page else str(p),"callback_data":f"page:{p}"}
            if PAGE_PREMIUM_EMOJIS.get(p):btn["icon_custom_emoji_id"]=PAGE_PREMIUM_EMOJIS[p]
            pag.append(btn)
        if pag:rows.append(pag)
        rows.append([{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}])
        text="\n".join([f"{pemoji(PREMIUM_SEARCH_ID,'📦')} <b>{t('available_inventory',lang)}</b>","",t('select_country',lang),"",f"<i>{t('showing_page',lang,page=page,total=total_pages,shown=len(page_c),total_c=len(all_c))}</i>"])
        send_or_edit(chat_id,text,{"inline_keyboard":rows})
    except Exception as e:send_or_edit(chat_id,error_text(e),back_keyboard(lang))

def send_country(chat_id,code,lang="en"):
    try:
        c=find_country(code)
        if not c:raise RuntimeError("That option is no longer available.")
        sp=apply_margin(c.price_usd)
        rows=[[{"text":t('enter_qty',lang),"callback_data":f"customqty:{c.code}"}],[{"text":t('back_avail',lang),"callback_data":"menu:countries","icon_custom_emoji_id":PREMIUM_BACK_ID}],[{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}]]
        text="\n".join([f"<b>{escape(c.name)} {get_flag_emoji(c.code)}</b>","",f"{pemoji(PREMIUM_PRICE_ID,'💵')} <b>{t('price_per_account',lang)}:</b> {money(sp)}",f"{pemoji(PREMIUM_STOCK_ID,'📦')} <b>{t('available_stock',lang)}:</b> {c.quantity:,}","",f"👇 {t('tap_qty',lang)}"])
        send_or_edit(chat_id,text,{"inline_keyboard":rows})
    except Exception as e:send_or_edit(chat_id,error_text(e),back_keyboard(lang))

def prompt_custom_quantity(chat_id,user_id,code,lang="en"):
    try:
        c=find_country(code)
        if not c:raise RuntimeError("That option is no longer available.")
        pending_custom_quantity[user_id]=code;sp=apply_margin(c.price_usd)
        text="\n".join([f"<b>{escape(c.name)} {get_flag_emoji(c.code)}</b>","",f"<b>{t('price_per_account',lang)}:</b> {money(sp)}",f"<b>{t('available_stock',lang)}:</b> {c.quantity:,}","",f"✏️ <b>{t('send_qty',lang)}</b>","",f"<i>{t('example_3',lang)}</i>"])
        send_or_edit(chat_id,text,back_to_countries_keyboard(lang))
    except Exception as e:send_or_edit(chat_id,error_text(e),back_keyboard(lang))

def send_wallet(chat_id,user_id,lang="en"):
    bal=get_balance(user_id)
    rows=[[{"text":t('deposit_funds',lang),"callback_data":"deposit:prompt","icon_custom_emoji_id":PREMIUM_WALLET_ID}],[{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}]]
    text="\n".join([f"{pemoji(PREMIUM_BALANCE_ID,'💳')} <b>{t('your_wallet',lang)}</b>","",f"<b>{t('balance',lang)}:</b> {money(bal)}","",t('tap_deposit',lang)])
    send_or_edit(chat_id,text,{"inline_keyboard":rows})

def prompt_deposit_amount(chat_id,lang="en"):
    text="\n".join([f"{pemoji(PREMIUM_DEPOSIT_ID,'💳')} <b>{t('deposit_funds',lang)}</b>","",f"✏️ <b>{t('enter_amount',lang)}</b>","",f"<i>{t('minimum',lang)}: {money(MIN_DEPOSIT)}</i>",f"<i>{t('example_5',lang)}</i>"])
    send_or_edit(chat_id,text,back_keyboard(lang))

def send_deposit_network_menu(chat_id,amount,lang="en"):
    rows=[[{"text":"TRC20 (Tron) — USDT","callback_data":"chain:trc20","icon_custom_emoji_id":PREMIUM_TRC20_ID}],[{"text":"BEP20 (BNB Chain) — USDT","callback_data":"chain:bep20","icon_custom_emoji_id":PREMIUM_BEP20_ID}],[{"text":"ERC20 (Ethereum) — USDT","callback_data":"chain:erc20","icon_custom_emoji_id":PREMIUM_ERC20_ID}],[{"text":"ETH (Ethereum) — Native","callback_data":"chain:eth","icon_custom_emoji_id":PREMIUM_ETH_ID}],[{"text":"SOL (Solana) — Native","callback_data":"chain:sol","icon_custom_emoji_id":PREMIUM_SOL_ID}],[{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}]]
    text="\n".join([f"{pemoji(PREMIUM_DEPOSIT_ID,'💳')} <b>{t('deposit_funds',lang)}</b>","",f"{t('amount',lang)}: <b>${amount:.2f}</b>","",f"👇 {t('select_network',lang)}"])
    send_or_edit(chat_id,text,{"inline_keyboard":rows})

def send_deposit_address(chat_id,user_id,amount,network,lang="en"):
    try:
        label,pay_currency=NETWORK_TO_CURRENCY.get(network,("Unknown",""))
        if not pay_currency:raise RuntimeError("Unknown network.")
        invoice=nowpayments_create_payment(user_id,amount,network)
        db_payment_create(payment_id=invoice["payment_id"],order_id=invoice["order_id"],user_id=user_id,amount_usd=invoice["credit_amount"],status=invoice["payment_status"],pay_address=invoice["pay_address"],pay_amount=invoice["pay_amount"],pay_currency=invoice["pay_currency"])
        fee_pct=NOWPAYMENTS_FEE_BUFFER*100
        text="\n".join([f"{pemoji(PREMIUM_DEPOSIT_ID,'💳')} <b>{label}</b>","",f"<b>{t('you_deposit',lang)}:</b> ${invoice['credit_amount']:.2f}",f"<b>{t('total_to_send',lang)}:</b> ${invoice['price_amount']:.2f}","",f"<b>{t('send_exactly',lang)}:</b>",f"<code>{invoice['pay_amount']} {pay_currency.upper()}</code>","",f"<b>{t('address',lang)}:</b>",f"<code>{invoice['pay_address']}</code>","",f"<b>{t('payment_id',lang)}:</b> <code>{invoice['payment_id']}</code>","",f"<i>{t('fee_notice',lang,pct=f'{fee_pct:.0f}')}</i>","",f"⚠️ {t('send_correct_network',lang)}",f"⚠️ {t('invoice_valid',lang)}","",f"<i>{t('credit_notice',lang)}</i>"])
        rows=[[{"text":t('copy_address',lang),"callback_data":f"copydep:{invoice['pay_address']}"}],[{"text":t('check_status',lang),"callback_data":f"checkpay:{invoice['payment_id']}"}],[{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}]]
        send_or_edit(chat_id,text,{"inline_keyboard":rows})
    except Exception as e:send_or_edit(chat_id,error_text(e),back_keyboard(lang))

def send_orders(chat_id,user_id,lang="en"):
    rows=db_order_list(user_id,limit=8)
    if not rows:send_or_edit(chat_id,f"{pemoji(PREMIUM_ORDERS_HEADER_ID,'📦')} <b>{t('no_orders',lang)}</b>\n\n{t('no_orders_desc',lang)}",back_keyboard(lang));return
    lines=[]
    for r in rows:lines.append(f"<b>{escape(r['order_id'])}</b>\n{escape(r['country_name'])} · {r['quantity']} pc · {money(r['amount_usd'])}\n{t('status',lang)}: {r['status']}")
    send_or_edit(chat_id,f"{pemoji(PREMIUM_ORDERS_HEADER_ID,'📦')} <b>{t('your_orders',lang)}</b>\n\n"+"\n\n".join(lines),back_keyboard(lang))

def send_profile(chat_id,user_id,first_name=None,lang="en"):
    u=db_user_get(user_id) or {};bs=t('banned',lang) if u.get("banned") else t('active',lang);bal=float(u.get("balance",0.0))
    text="\n".join([f"{pemoji(PREMIUM_PROFILE_ID,'👤')} <b>{t('profile_title',lang)}</b>","",f"<b>{t('name',lang)}:</b> {escape(first_name or 'User')}",f"<b>{t('id',lang)}:</b> <code>{user_id}</code>",f"<b>{t('user_status',lang)}:</b> {bs}",f"<b>{t('balance',lang)}:</b> {money(bal)}"])
    send_or_edit(chat_id,text,back_keyboard(lang))

def send_language_menu(chat_id,lang="en"):
    rows=[];row=[]
    for code,(name,flag) in LANG_TO_USER_PICK.items():
        mark="✓ " if code==lang else ""
        row.append({"text":f"{mark}{flag} {name}","callback_data":f"setlang:{code}"})
        if len(row)==2:rows.append(row);row=[]
    if row:rows.append(row)
    rows.append([{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}])
    send_or_edit(chat_id,f"{pemoji(PREMIUM_LANGUAGE_ID,'🌍')} <b>{t('language_title',lang)}</b>",{"inline_keyboard":rows})

def send_help(chat_id,lang="en"):send_or_edit(chat_id,f"<b>How it works</b>\n\n1. Browse the live catalog.\n2. Select the country and quantity.\n3. Confirm your order using your wallet balance.\n4. Click 'Get Code' to receive the login code.\n5. Use the code and password to log in to Telegram.\n\nThis bot does not request Telegram passwords or login codes.",back_keyboard(lang))

def confirm_order(chat_id,user_id,code,quantity,lang="en"):
    try:
        c=find_country(code)
        if not c:raise RuntimeError("That option is no longer available.")
        if quantity<1:raise RuntimeError("Quantity must be at least 1.")
        if quantity>c.quantity:raise RuntimeError(f"Only {c.quantity} accounts are available.")
        if quantity>5:raise RuntimeError("Maximum 5 accounts per order.")
        shown_total=apply_margin(c.price_usd)*quantity;bal=get_balance(user_id);rows=[]
        if bal>=shown_total:rows.append([{"text":t('confirm_purchase',lang),"callback_data":f"confirm:{c.code}:{quantity}"}])
        else:rows.append([{"text":t('deposit_funds',lang),"callback_data":"deposit:prompt","icon_custom_emoji_id":PREMIUM_WALLET_ID}])
        rows.append([{"text":t('change_quantity',lang),"callback_data":f"customqty:{c.code}","icon_custom_emoji_id":PREMIUM_BACK_ID}])
        rows.append([{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}])
        text="\n".join([f"<b>{t('order_summary',lang)}</b>","",f"<b>{t('country',lang)}:</b> {escape(c.name)} {get_flag_emoji(c.code)} ({c.code})",f"<b>{t('quantity',lang)}:</b> {quantity} {t('account_s',lang)}",f"<b>{t('price_per_account',lang)}:</b> {money(apply_margin(c.price_usd))}","",f"<b>{t('total_price',lang)}:</b> {money(shown_total)}","",f"<b>{t('your_balance',lang)}:</b> {money(bal)} ({t('sufficient',lang) if bal>=shown_total else t('insufficient',lang)})","",f"<i>{t('click_confirm',lang) if bal>=shown_total else t('not_enough',lang)}</i>"])
        send_or_edit(chat_id,text,{"inline_keyboard":rows})
    except Exception as e:send_or_edit(chat_id,error_text(e),back_keyboard(lang))

def create_order(chat_id,user_id,code,quantity=1,lang="en"):
    try:
        c=find_country(code)
        if not c:raise RuntimeError("That option is no longer available.")
        if quantity<1 or quantity>5:raise RuntimeError("Quantity must be between 1 and 5.")
        if quantity>c.quantity:raise RuntimeError(f"Only {c.quantity} accounts are available.")
        base_total=c.price_usd*quantity;shown_total=apply_margin(c.price_usd)*quantity;profit=round(shown_total-base_total,2)
        bal=get_balance(user_id)
        if bal<shown_total:raise RuntimeError(f"Insufficient balance. Need {money(shown_total)}, have {money(bal)}.")
        add_balance(user_id,-shown_total)
        order=Order(order_id=f"TL-{uuid.uuid4().hex[:8].upper()}",telegram_user_id=user_id,country_code=c.code,country_name=c.name,quantity=quantity,amount_usd=shown_total,base_cost=base_total,profit=profit,status="purchasing",payment_method="wallet",created_at=str(int(time.time())))
        db_order_create(order);db_stats_incr("total_spent",shown_total);db_stats_incr("total_profit",profit)
        send_or_edit(chat_id,f"⏳ <b>{t('purchasing',lang,qty=quantity,country=escape(c.name))}</b>\n\n<i>{t('please_wait',lang)}</i>")
        nums=[]
        try:
            for _ in range(quantity):
                n=buy_number(c.code);nums.append(n);db_number_save(order.order_id,n.get("Number","N/A"))
        except Exception as be:
            add_balance(user_id,shown_total);db_stats_incr("total_spent",-shown_total);db_stats_incr("total_profit",-profit);db_order_update_status(order.order_id,"refunded")
            raise RuntimeError(f"Purchase failed. Refunded {money(shown_total)}.\nReason: {be}")
        db_order_update_status(order.order_id,"awaiting_code")
        details=[f"<b>{i}.</b> <code>{escape(n.get('Number','N/A'))}</code>" for i,n in enumerate(nums,1)]
        rows=[[{"text":t('get_code',lang),"callback_data":f"getcode:{order.order_id}:0"}],[{"text":t('view_my_orders',lang),"callback_data":"menu:orders"}],[{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}]]
        text="\n".join([f"<b>{t('numbers_purchased',lang)}</b>","",f"<b>{t('order_id',lang)}:</b> <code>{order.order_id}</code>",f"<b>{t('country',lang)}:</b> {escape(c.name)}",f"<b>{t('quantity',lang)}:</b> {quantity}",f"<b>{t('total_paid',lang)}:</b> {money(shown_total)}",f"<b>{t('your_balance',lang)}:</b> {money(get_balance(user_id))}","",f"<b>{t('your_numbers',lang)}:</b>",*details,"",f"<i>{t('click_get_code',lang)}</i>"])
        send_or_edit(chat_id,text,{"inline_keyboard":rows})
    except Exception as e:send_or_edit(chat_id,error_text(e),back_keyboard(lang))

def send_admin_panel(chat_id,lang="en"):
    users=db_user_all();tu=len(users);tb=sum(1 for u in users if u.get("banned"));to=db_order_count();tbal=sum(float(u.get("balance",0)) for u in users)
    stats=db_stats_get();td=stats.get("total_deposits",0.0);ts=stats.get("total_spent",0.0);tp=stats.get("total_profit",0.0)
    text="\n".join([f"{pemoji(PREMIUM_ADMIN_HEADER_ID,'🛠')} <b>{t('admin_title',lang)}</b>","",f"{pemoji(PREMIUM_USERS_ID,'👥')} <b>{t('total_users',lang)}:</b> {tu}",f"{pemoji(PREMIUM_BAN_ID,'🚫')} <b>{t('banned_users',lang)}:</b> {tb}",f"{pemoji(PREMIUM_ORDERS_ID,'📦')} <b>{t('total_orders',lang)}:</b> {to}","",f"💰 <b>{t('total_deposits',lang)}:</b> {money(td)}",f"🛒 <b>{t('total_spent',lang)}:</b> {money(ts)}",f"📈 <b>{t('total_profit',lang)}:</b> {money(tp)}",f"🏦 <b>{t('user_balances',lang)}:</b> {money(tbal)}","",f"⚙️ <b>{t('profit_margin',lang)}:</b> {profit_margin*100:.0f}%","",f"<i>{t('select_action',lang)}</i>"])
    rows=[[{"text":t('admin_users',lang),"callback_data":"admin:users"},{"text":t('admin_orders',lang),"callback_data":"admin:orders"}],[{"text":t('credit_user',lang),"callback_data":"admin:credit"},{"text":t('debit_user',lang),"callback_data":"admin:debit"}],[{"text":t('ban_user',lang),"callback_data":"admin:ban"},{"text":t('unban_user',lang),"callback_data":"admin:unban"}],[{"text":t('set_margin',lang),"callback_data":"admin:margin"}],[{"text":t('broadcast',lang),"callback_data":"admin:broadcast","icon_custom_emoji_id":PREMIUM_BROADCAST_ID}],[{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}]]
    send_or_edit(chat_id,text,{"inline_keyboard":rows})

def send_admin_users(chat_id,lang="en"):
    users=db_user_all()
    if not users:send_or_edit(chat_id,f"<b>{t('no_orders',lang)}</b>",admin_back_keyboard(lang));return
    lines=[]
    for u in users[:30]:
        uid=u["user_id"];name=u.get("first_name") or "Unknown";bal=float(u.get("balance",0));banned="🚫" if u.get("banned") else "✅"
        lines.append(f"{banned} <code>{uid}</code> — {escape(name)} — {money(bal)}")
    send_or_edit(chat_id,f"<b>{t('admin_users',lang)} (30)</b>\n\n"+"\n".join(lines),admin_back_keyboard(lang))

def send_admin_orders(chat_id,lang="en"):
    rows=db_order_recent()
    if not rows:send_or_edit(chat_id,f"<b>{t('no_orders',lang)}</b>",admin_back_keyboard(lang));return
    lines=[]
    for o in rows:lines.append(f"<b>{escape(o['order_id'])}</b>\nUser: <code>{o['user_id']}</code>\n{escape(o['country_name'])} · {o['quantity']} pc\nPaid: {money(o['amount_usd'])} · Cost: {money(o['base_cost'])} · Profit: {money(o['profit'])}\n{t('status',lang)}: {o['status']}")
    send_or_edit(chat_id,f"<b>{t('admin_orders',lang)}</b>\n\n"+"\n\n".join(lines),admin_back_keyboard(lang))

def prompt_admin_credit(chat_id,admin_id,lang="en"):
    pending_admin_input[admin_id]={"action":"credit"};send_or_edit(chat_id,f"💳 <b>{t('credit_user',lang)}</b>\n\n{t('credit_prompt',lang)}",admin_back_keyboard(lang))
def prompt_admin_debit(chat_id,admin_id,lang="en"):
    pending_admin_input[admin_id]={"action":"debit"};send_or_edit(chat_id,f"💸 <b>{t('debit_user',lang)}</b>\n\n{t('debit_prompt',lang)}",admin_back_keyboard(lang))
def prompt_admin_ban(chat_id,admin_id,lang="en"):
    pending_admin_input[admin_id]={"action":"ban"};send_or_edit(chat_id,f"🚫 <b>{t('ban_user',lang)}</b>\n\n{t('ban_prompt',lang)}",admin_back_keyboard(lang))
def prompt_admin_unban(chat_id,admin_id,lang="en"):
    pending_admin_input[admin_id]={"action":"unban"};send_or_edit(chat_id,f"✅ <b>{t('unban_user',lang)}</b>\n\n{t('unban_prompt',lang)}",admin_back_keyboard(lang))
def prompt_admin_margin(chat_id,admin_id,lang="en"):
    pending_admin_input[admin_id]={"action":"margin"};send_or_edit(chat_id,f"📊 <b>{t('set_margin',lang)}</b>\n\n{t('margin_prompt',lang,pct=f'{profit_margin*100:.0f}')}",admin_back_keyboard(lang))
def prompt_admin_broadcast(chat_id,admin_id,lang="en"):
    pending_admin_input[admin_id]={"action":"broadcast"};send_or_edit(chat_id,f"📢 <b>{t('broadcast',lang)}</b>\n\n{t('broadcast_prompt',lang)}",admin_back_keyboard(lang))

def do_broadcast(chat_id,text):
    def replace_emoji(match):return f'<tg-emoji emoji-id="{match.group(1)}">⭐</tg-emoji>'
    formatted=re.sub(r"<emoji:(\d+)>",replace_emoji,text)
    users=db_user_all();sent=0;failed=0
    for u in users:
        uid=u["user_id"]
        try:send_message(uid,formatted);sent+=1;time.sleep(0.05)
        except Exception:failed+=1
    send_or_edit(chat_id,f"✅ {sent} sent, {failed} failed.",admin_back_keyboard())

def handle_update(update):
    global profit_margin
    cb=update.get("callback_query")
    if cb:
        try:telegram("answerCallbackQuery",{"callback_query_id":cb["id"]})
        except Exception as e:print(f"[UI] answerCallbackQuery failed (ignored): {e}",flush=True)
        msg=cb.get("message") or {};chat_id=(msg.get("chat") or {}).get("id");message_id=msg.get("message_id");data=cb.get("data")
        if not chat_id or not data:return
        if message_id:last_message_id[chat_id]=message_id
        parts=data.split(":",2);action=parts[0];value=parts[1] if len(parts)>1 else "";extra=parts[2] if len(parts)>2 else ""
        user=cb.get("from") or {};user_id=int(user.get("id",chat_id))
        register_user(user_id,user.get("first_name"))
        lang=get_user_lang(user_id)
        u=db_user_get(user_id)
        if u and u.get("banned") and not is_admin(user_id):send_message(chat_id,t('banned_msg',lang));return
        if action=="admin":
            if not is_admin(user_id):send_or_edit(chat_id,t('unauthorized',lang),back_keyboard(lang));return
            if value=="panel":send_admin_panel(chat_id,lang)
            elif value=="users":send_admin_users(chat_id,lang)
            elif value=="orders":send_admin_orders(chat_id,lang)
            elif value=="credit":prompt_admin_credit(chat_id,user_id,lang)
            elif value=="debit":prompt_admin_debit(chat_id,user_id,lang)
            elif value=="ban":prompt_admin_ban(chat_id,user_id,lang)
            elif value=="unban":prompt_admin_unban(chat_id,user_id,lang)
            elif value=="margin":prompt_admin_margin(chat_id,user_id,lang)
            elif value=="broadcast":prompt_admin_broadcast(chat_id,user_id,lang)
            return
        if action=="menu" and value=="home":send_home(chat_id,user.get("first_name"),user_id)
        elif action=="menu" and value=="countries":send_countries(chat_id,page=1,lang=lang)
        elif action=="page":
            try:send_countries(chat_id,page=int(value),lang=lang)
            except ValueError:send_countries(chat_id,page=1,lang=lang)
        elif action=="menu" and value=="orders":send_orders(chat_id,user_id,lang)
        elif action=="menu" and value=="wallet":send_wallet(chat_id,user_id,lang)
        elif action=="menu" and value=="profile":send_profile(chat_id,user_id,user.get("first_name"),lang)
        elif action=="menu" and value=="language":send_language_menu(chat_id,lang)
        elif action=="setlang" and value:
            set_user_lang(user_id,value);new_lang=value;name=LANG_TO_USER_PICK.get(value,("English",))[0]
            send_or_edit(chat_id,f"<b>{t('language_set',new_lang,name=name)}</b>",main_menu_keyboard(user_id,new_lang))
        elif action=="deposit" and value=="prompt":pending_custom_deposit[user_id]=True;prompt_deposit_amount(chat_id,lang)
        elif action=="chain" and value:
            sel=pending_deposit_selection.get(user_id,{});amt=sel.get("amount")
            if not amt:send_or_edit(chat_id,t('session_expired',lang),back_keyboard(lang));return
            send_deposit_address(chat_id,user_id,amt,value,lang)
        elif action=="copydep" and value:send_or_edit(chat_id,f"📋 <b>{t('address',lang)}:</b>\n<code>{escape(value)}</code>",back_keyboard(lang))
        elif action=="checkpay" and value:
            try:
                status=nowpayments_get_status(value);send_or_edit(chat_id,f"📊 <b>{t('status',lang)}</b>\n\n<b>{t('payment_id',lang)}:</b> <code>{escape(value)}</code>\n<b>{t('status',lang)}:</b> {status.get('payment_status','unknown')}",back_keyboard(lang))
            except Exception as e:send_or_edit(chat_id,error_text(e),back_keyboard(lang))
        elif action=="country" and value:send_country(chat_id,value,lang)
        elif action=="customqty" and value:prompt_custom_quantity(chat_id,user_id,value,lang)
        elif action=="confirm" and value and extra:
            try:create_order(chat_id,user_id,value,int(extra),lang)
            except ValueError:send_country(chat_id,value,lang)
        elif action=="getcode" and value and extra:
            try:
                idx=int(extra);nums=db_number_list(value)
                if idx>=len(nums):raise RuntimeError("All codes delivered.")
                row=nums[idx];phone=row.get("phone");send_or_edit(chat_id,f"⏳ <b>{t('fetching_code',lang)}</b> <code>{escape(phone)}</code>...")
                try:code_result=fetch_code(phone)
                except Exception as fe:
                    retry={"inline_keyboard":[[{"text":t('retry',lang),"callback_data":f"getcode:{value}:{idx}"}],[{"text":t('view_my_orders',lang),"callback_data":"menu:orders"}]]}
                    send_or_edit(chat_id,f"❌ {t('failed',lang)}: {escape(str(fe))}",retry);return
                db_number_mark(row["id"],code_result.get("code",""),code_result.get("pass",""))
                next_idx=idx+1;has_more=next_idx<len(nums)
                if has_more:btns=[[{"text":t('get_code_n',lang,n=next_idx+1),"callback_data":f"getcode:{value}:{next_idx}"}],[{"text":t('view_my_orders',lang),"callback_data":"menu:orders"}],[{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}]]
                else:
                    db_order_update_status(value,"completed");btns=[[{"text":t('view_my_orders',lang),"callback_data":"menu:orders"}],[{"text":t('back_home',lang),"callback_data":"menu:home","icon_custom_emoji_id":PREMIUM_BACK_ID}]]
                text="\n".join([f"<b>{t('code_received',lang,n=idx+1)}</b>","",f"<b>📱 {t('number',lang)}:</b> <code>{escape(phone)}</code>",f"<b>🔑 {t('code',lang)}:</b> <code>{escape(str(code_result.get('code')))}</code>",f"<b>🔒 {t('password',lang)}:</b> <code>{escape(str(code_result.get('pass')))}</code>","",f"<i>{t('code_login',lang)}</i>"])
                send_or_edit(chat_id,text,{"inline_keyboard":btns})
            except Exception as e:send_or_edit(chat_id,error_text(e),back_keyboard(lang))
        return
    message=update.get("message") or {};text=message.get("text")
    if not text:return
    chat_id=int((message.get("chat") or {})["id"]);user=message.get("from") or {};user_id=int(user.get("id",chat_id));command=text.strip().split()[0].lower()
    register_user(user_id,user.get("first_name"));lang=get_user_lang(user_id)
    u=db_user_get(user_id)
    if u and u.get("banned") and not is_admin(user_id):send_message(chat_id,t('banned_msg',lang));return
    if is_admin(user_id) and user_id in pending_admin_input:
        pending=pending_admin_input.pop(user_id);act=pending.get("action")
        if act=="credit":
            try:
                p=text.strip().split();target,amt=int(p[0]),float(p[1]);new_bal=add_balance(target,amt)
                send_or_edit(chat_id,f"✅ {money(amt)} → <code>{target}</code>. {t('balance',lang)}: {money(new_bal)}",admin_back_keyboard(lang))
                try:send_message(target,f"💳 <b>{t('balance',lang)}</b>\n\n+{money(amt)}\n{t('new_balance',lang)}: {money(new_bal)}")
                except Exception:pass
            except Exception as e:send_or_edit(chat_id,f"❌ {t('invalid_input',lang)} {e}",admin_back_keyboard(lang))
            return
        if act=="debit":
            try:
                p=text.strip().split();target,amt=int(p[0]),float(p[1]);new_bal=add_balance(target,-amt)
                if new_bal<0:db_user_set_balance(target,0.0);new_bal=0.0
                send_or_edit(chat_id,f"✅ {money(amt)} ← <code>{target}</code>. {t('balance',lang)}: {money(new_bal)}",admin_back_keyboard(lang))
            except Exception as e:send_or_edit(chat_id,f"❌ {t('invalid_input',lang)} {e}",admin_back_keyboard(lang))
            return
        if act=="ban":
            try:target=int(text.strip());db_user_ban(target,True);send_or_edit(chat_id,f"🚫 {target}",admin_back_keyboard(lang))
            except Exception as e:send_or_edit(chat_id,f"❌ {e}",admin_back_keyboard(lang))
            return
        if act=="unban":
            try:target=int(text.strip());db_user_ban(target,False);send_or_edit(chat_id,f"✅ {target}",admin_back_keyboard(lang))
            except Exception as e:send_or_edit(chat_id,f"❌ {e}",admin_back_keyboard(lang))
            return
        if act=="margin":
            try:
                pct=float(text.strip())
                if pct<0 or pct>500:raise ValueError("0-500")
                profit_margin=pct/100.0;db_settings_set("profit_margin",str(profit_margin));send_or_edit(chat_id,f"✅ {t('profit_margin',lang)}: {pct:.0f}%",admin_back_keyboard(lang))
            except Exception as e:send_or_edit(chat_id,f"❌ {e}",admin_back_keyboard(lang))
            return
        if act=="broadcast":do_broadcast(chat_id,text);return
    if command=="/admin" and is_admin(user_id):send_admin_panel(chat_id,lang);return
    if user_id in pending_custom_deposit and command not in ("/start","/menu","/wallet","/orders","/help"):
        del pending_custom_deposit[user_id]
        try:
            amt=float(text.strip())
            if amt<MIN_DEPOSIT:raise RuntimeError(t('min_deposit_err',lang,amount=money(MIN_DEPOSIT)))
            pending_deposit_selection[user_id]={"amount":amt};send_deposit_network_menu(chat_id,amt,lang)
        except ValueError:send_or_edit(chat_id,t('invalid_amount',lang),back_keyboard(lang))
        return
    if user_id in pending_custom_quantity and command not in ("/start","/menu","/orders","/help"):
        code=pending_custom_quantity.pop(user_id)
        try:confirm_order(chat_id,user_id,code,int(text.strip()),lang)
        except ValueError:send_or_edit(chat_id,t('invalid_quantity',lang),back_to_countries_keyboard(lang))
        return
    if command in ("/start","/menu"):send_home(chat_id,user.get("first_name"),user_id,force_new=True)
    elif command=="/orders":send_orders(chat_id,user_id,lang)
    elif command=="/language":send_language_menu(chat_id,lang)
    elif command=="/help":send_help(chat_id,lang)
    else:send_home(chat_id,user.get("first_name"),user_id)

def main():
    global profit_margin
    missing=[]
    for name,val in [("TELEGRAM_TOKEN",TELEGRAM_TOKEN),("TG_LION_API_KEY",TG_LION_API_KEY),("TG_LION_USER_ID",TG_LION_USER_ID),("WORKER_URL",WORKER_URL),("WORKER_TOKEN",WORKER_TOKEN),("NOWPAYMENTS_API_KEY",NOWPAYMENTS_API_KEY),("NOWPAYMENTS_PAYOUT_ADDRESS",NOWPAYMENTS_PAYOUT_ADDRESS)]:
        if not val:missing.append(name)
    if missing:print(f"❌ Missing: {', '.join(missing)}",file=sys.stderr,flush=True);sys.exit(1)
    print("TG-Lion Market Bot starting...",flush=True);print("Worker URL:",WORKER_URL,flush=True);print(f"Fee buffer: {NOWPAYMENTS_FEE_BUFFER*100:.0f}%",flush=True)
    threading.Thread(target=start_health_server,daemon=True).start();print("[Startup] Health server started.",flush=True)
    try:
        bot_info=telegram("getMe");print(f"Telegram verified: @{bot_info.get('username','unknown')}",flush=True);print(f"TG-Lion verified: {len(get_countries())} countries",flush=True)
    except Exception as e:print(f"Startup failed: {error_text(e)}",file=sys.stderr,flush=True);sys.exit(1)
    try:
        val=db_settings_get("profit_margin")
        if val:profit_margin=float(val)
        print(f"[Startup] Profit margin: {profit_margin*100:.0f}%",flush=True)
    except Exception as e:print(f"[Startup] Could not load margin: {e}",flush=True)
    threading.Thread(target=payment_notifier_worker,daemon=True).start();print("[Startup] Payment notifier started.",flush=True)
    threading.Thread(target=invoice_cleanup_worker,daemon=True).start();print("[Startup] Invoice cleanup started.",flush=True)
    offset=None
    while True:
        try:
            payload={"timeout":25,"allowed_updates":["message","callback_query"]}
            if offset is not None:payload["offset"]=offset
            for update in telegram("getUpdates",payload) or []:offset=int(update["update_id"])+1;handle_update(update)
        except KeyboardInterrupt:print("\nBot stopped.");return
        except Exception as e:print(error_text(e),file=sys.stderr);time.sleep(3)

if __name__=="__main__":main()