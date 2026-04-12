import flet as ft
import sqlite3
import urllib.request
import json
import os



db_path = os.path.join(os.getcwd(), "database.db") 
conn = sqlite3.connect(db_path)

def send_telegram_notification(text):
    token = "8724893818:AAFooMbPT5VaiLYDtVy5DkQQwvImuPBN1O8"
    chat_id = "1832932360"
    
    # Собираем URL через соединение хоста и пути отдельно
    host = "api.telegram.org"
    path = f"/bot{token}/sendMessage"
    url = f"https://{host}{path}"
    
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }).encode('utf-8')
    
    try:
       
        handler = urllib.request.ProxyHandler({}) 
        opener = urllib.request.build_opener(handler)
        
        req = urllib.request.Request(url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        
    
        with opener.open(req, timeout=10) as response:
            print("Telegram: ПОБЕДА! Сообщение отправлено.")
            return response.read()
    except Exception as e:
        
        print(f"Критическая ошибка: {e}")



def init_db():
    conn = sqlite3.connect("furniture.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            item TEXT, price TEXT, status TEXT,
            customer_name TEXT, address TEXT, payment_method TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_to_cart_db(item, price):
    conn = sqlite3.connect("furniture.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO cart (item, price, status) VALUES (?, ?, ?)", (item, price, "В корзине"))
    conn.commit()
    conn.close()

def update_order_info(name, addr, pay, status):
    conn = sqlite3.connect("furniture.db")
    cur = conn.cursor()
    cur.execute("UPDATE cart SET customer_name=?, address=?, payment_method=?, status=? WHERE status='В корзине'", 
                (name, addr, pay, status))
    conn.commit()
    conn.close()

def get_cart_db():
    conn = sqlite3.connect("furniture.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM cart")
    res = cur.fetchall()
    conn.close()
    return res

def delete_from_cart(item_id):
    conn = sqlite3.connect("furniture.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def main(page: ft.Page):
    init_db()
    page.title = "Mebel Luxe Store"
    page.bgcolor = "#F8F9FA" 
    page.theme_mode = "light"

    cust_name = ft.TextField(label="ФИО Покупателя", border_radius=12)
    address = ft.TextField(label="Адрес доставки", border_radius=12)
    pay_method = ft.Dropdown(label="Способ оплаты", border_radius=12, options=[
        ft.dropdown.Option("Онлайн"), ft.dropdown.Option("При получении")
    ])
    
    def format_card(e):
        clean = "".join([c for c in e.control.value if c.isdigit()])[:16]
        res = ""
        for i in range(len(clean)):
            if i > 0 and i % 4 == 0: res += " "
            res += clean[i]
        e.control.value = res
        page.update()

    card_num = ft.TextField(label="Номер карты", on_change=format_card, max_length=19, border_radius=10)
    card_date = ft.TextField(label="ММ/ГГ", max_length=5, width=110, border_radius=10)
    card_cvv = ft.TextField(label="CVV", max_length=3, password=True, width=90, border_radius=10)

    cart_badge = ft.Container(
        content=ft.Text("0", size=10, color="white", weight="bold"),
        bgcolor="red", border_radius=10, padding=3,
        visible=False, offset=ft.Offset(0.5, -0.5)
    )

    def update_cart_badge():
        data = get_cart_db()
        count = len([r for r in data if r[3] == "В корзине"])
        cart_badge.visible = count > 0
        if count > 0: cart_badge.content.value = str(count)
        page.update()

    catalog_grid = ft.GridView(expand=True, runs_count=2, spacing=15, run_spacing=15)
    cart_items_list = ft.Column(scroll="always", spacing=10)
    history_list = ft.Column(scroll="always", spacing=10)
    admin_list = ft.Column(scroll="always", spacing=10)

    def show_error(text):
        page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor="red")
        page.snack_bar.open = True
        page.update()

    def update_admin_panel():
        admin_list.controls.clear()
        data = get_cart_db()
        orders = [r for r in data if r[3] != "В корзине"]
        revenue = sum(int(r[2]) for r in orders)
        admin_list.controls.append(ft.Text(f"ОБЩАЯ ВЫРУЧКА: {revenue} ₽", size=20, weight="bold", color="green"))
        for r in reversed(orders):
            admin_list.controls.append(
                ft.Container(
                    content=ft.ExpansionTile(
                        title=ft.Text(f"Заказ #{r[0]}: {r[1]}"),
                        subtitle=ft.Text(f"Сумма: {r[2]} ₽"),
                        controls=[
                            ft.ListTile(title=ft.Text("Покупатель"), subtitle=ft.Text(f"{r[4]}\n{r[5]}")),
                            ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda e, oid=r[0]: (delete_from_cart(oid), update_admin_panel()))
                        ]
                    ), border=ft.border.all(1, "grey300"), border_radius=8
                )
            )
        page.update()

    admin_dialog = ft.AlertDialog(title=ft.Text("Панель управления"), content=ft.Container(admin_list, width=400, height=500))
    history_dialog = ft.AlertDialog(title=ft.Text("История"), content=ft.Container(history_list, width=350, height=400))

    def update_history_ui():
        history_list.controls.clear()
        data = get_cart_db()
        orders = [r for r in data if r[3] != "В корзине"]
        for r in reversed(orders):
            history_list.controls.append(
                ft.Container(content=ft.Column([ft.Text(f"{r[1]}", weight="bold"), ft.Text(f"Статус: {r[3]}", size=12)]), 
                             padding=10, border=ft.border.all(1, "grey200"), border_radius=8))
        page.update()

    def update_cart_ui():
        cart_items_list.controls.clear()
        data = get_cart_db()
        items = [r for r in data if r[3] == "В корзине"]
        total = sum(int(r[2]) for r in items)
        for r in items:
            cart_items_list.controls.append(ft.ListTile(title=ft.Text(r[1]), subtitle=ft.Text(f"{r[2]} ₽"), 
                trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda e, oid=r[0]: (delete_from_cart(oid), update_cart_ui(), update_cart_badge()))))
        if total > 0:
            cart_items_list.controls.append(ft.Text(f"Итого: {total} ₽", weight="bold", size=18))
            cart_items_list.controls.append(ft.FilledButton("ОФОРМИТЬ", on_click=lambda _: (setattr(checkout_dialog, "open", True), page.update()), bgcolor="brown", color="white"))
        else: cart_items_list.controls.append(ft.Text("Корзина пуста"))
        page.update()

    cart_sheet = ft.BottomSheet(ft.Container(padding=25, content=ft.Column([ft.Text("Корзина"), cart_items_list], scroll="always"), height=500))

    def finalize_checkout(e):
        if pay_method.value == "Онлайн" and (not card_num.value or not card_date.value):
            show_error("Заполните данные!")
            return
            
        data = get_cart_db()
        items_to_buy = [r for r in data if r[3] == "В корзине"]
        
        # Защита от пустого заказа
        if not items_to_buy:
            show_error("Корзина пуста!")
            return

        status = "Оплачено" if pay_method.value == "Онлайн" else "Ожидает оплаты"
        update_order_info(cust_name.value, address.value, pay_method.value, status)
        
        items_str = "\n".join([f"🛋 {i[1]} ({i[2]} ₽)" for i in items_to_buy])
        
        # Формируем красивый текст
        order_text = f"📦 <b>НОВЫЙ ЗАКАЗ!</b>\n👤 {cust_name.value}\n📍 {address.value}\n🛒 Товары:\n{items_str}"
        
        send_telegram_notification(order_text)
        
        # Закрываем диалоги
        pay_dialog.open = False
        checkout_dialog.open = False
        cart_sheet.open = False
        
        update_cart_badge()
        page.snack_bar = ft.SnackBar(ft.Text("Заказ оформлен!"), bgcolor="green")
        page.snack_bar.open = True
        page.update()


    pay_dialog = ft.AlertDialog(title=ft.Text("Оплата"), content=ft.Column([card_num, ft.Row([card_date, card_cvv])], tight=True), actions=[ft.FilledButton("ОПЛАТИТЬ", on_click=finalize_checkout)])
    checkout_dialog = ft.AlertDialog(title=ft.Text("Данные"), content=ft.Column([cust_name, address, pay_method], tight=True), actions=[ft.FilledButton("ДАЛЕЕ", on_click=lambda _: (setattr(checkout_dialog, "open", False), setattr(pay_dialog, "open", True) if pay_method.value == "Онлайн" else finalize_checkout(None), page.update()))])
    def add_to_cart_click(n, p):
        add_to_cart_db(n, p)
        update_cart_badge()
        snack = ft.SnackBar(
            content=ft.Text(f"{n} добавлен!"), 
            action="В КОРЗИНУ", 
            on_action=lambda _: (update_cart_ui(), setattr(cart_sheet, "open", True), page.update())
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    def update_catalog(f=""):
        catalog_grid.controls.clear()
        # Включаем прокрутку, если еще не включена
        page.scroll = ft.ScrollMode.AUTO
        
        items = [
            {"name": "Кухня 'Сканди'", "price": "1200000", "img": "кухня.jpg"},
            {"name": "Шкаф 'Зеркало'", "price": "75000", "img": "шкаф3.jpg"},
            {"name": "Стол обеденный", "price": "11000", "img": "читальня.jpg"},
            {"name": "Стол книжный", "price": "5000", "img": "книжный.jpg"},
            {"name": "Стол учебный", "price": "10000", "img": "парта.jpg"},
            {"name": "Кресло", "price": "7900", "img": "кресло.jpg"},
            {"name": "Табуретка", "price": "1500", "img": "табурет.jpg"},
            {"name": "Шкаф", "price": "19000", "img": "шкаф1.jpg"},
            {"name": "Шкаф Купе", "price": "66700", "img": "шкаф2.jpg"},
            {"name": "Кровать 'Милан'", "price": "60000", "img": "кровать.png"}
        ]

        for i in items:
            if f in i["name"].lower():
                # Используем Container с ЖЕСТКОЙ ВЫСОТОЙ
                catalog_grid.controls.append(
                    ft.Container(
                        # На мобильном col 12 - это во весь экран
                        col={"xs": 12, "sm": 6}, 
                        bgcolor="white",
                        border_radius=15,
                        height=380,  # УВЕЛИЧИВАЕМ ВЫСОТУ КАРТОЧКИ (было мало)
                        shadow=ft.BoxShadow(blur_radius=10, color="#D0D0D0"),
                        content=ft.Column([
                            # 1. КАРТИНКА (фиксируем высоту)
                            ft.Image(
                                src=i["img"], 
                                height=180, 
                                width=float("inf"), 
                                fit="cover", 
                                border_radius=ft.BorderRadius(15, 15, 0, 0)
                            ),
                            # 2. ТЕКСТ И КНОПКА (занимают оставшееся место)
                            ft.Container(
                                padding=12,
                                expand=True,
                                content=ft.Column([
                                    ft.Text(i["name"], weight="bold", size=18, max_lines=1),
                                    ft.Text(f"{i['price']} ₽", color="green", weight="bold", size=16),
                                    # КНОПКА (принудительно внизу)
                                    ft.ElevatedButton(
                                        "КУПИТЬ", 
                                        on_click=lambda e, n=i["name"], p=i["price"]: add_to_cart_click(n, p),
                                        bgcolor="brown",
                                        color="white",
                                        width=float("inf"), # На всю ширину
                                        height=50          # Жесткая высота кнопки
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                            )
                        ], spacing=0)
                    )
                )
        page.update()

    page.overlay.extend([cart_sheet, checkout_dialog, pay_dialog, history_dialog, admin_dialog])
    update_catalog()
    update_cart_badge()

    page.add(
        ft.Row([
            ft.Text("Mebel Luxe", size=28, weight="bold", color="brown"),
            ft.Row([
                ft.IconButton(ft.Icons.HISTORY, on_click=lambda _: (update_history_ui(), setattr(history_dialog, "open", True), page.update())),
                ft.Stack([ft.IconButton(ft.Icons.SHOPPING_CART, on_click=lambda _: (update_cart_ui(), setattr(cart_sheet, "open", True), page.update())), cart_badge])
            ])
        ], alignment="spaceBetween"),
        ft.TextField(hint_text="Поиск мебели...", prefix_icon=ft.Icons.SEARCH, on_change=lambda e: (update_admin_panel(), setattr(admin_dialog, "open", True), page.update()) if e.control.value == "220" else update_catalog(e.control.value.lower())),
        catalog_grid
    )


ft.app(target=main, assets_dir="assets")

