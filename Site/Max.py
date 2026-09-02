import asyncio
import json
import inspect
from datetime import datetime
from pathlib import Path

from pymax import Client, Message

# ========== КОНФИГУРАЦИЯ ==========
PHONE = "+79990000000"          # Ваш номер в формате +7XXXXXXXXXX
WORK_DIR = "instance"
SESSION_NAME = "Max.db"
MESSAGES_FILE = "messages.json"

# ========== ИНИЦИАЛИЗАЦИЯ КЛИЕНТА ==========
client = Client(
    phone=PHONE,
    work_dir=WORK_DIR,
    session_name=SESSION_NAME,
)

# ========== РАБОТА С JSON (сохранение входящих) ==========
def load_messages() -> list:
    file_path = Path(WORK_DIR) / MESSAGES_FILE
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_messages(messages: list) -> None:
    file_path = Path(WORK_DIR) / MESSAGES_FILE
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

saved_messages = load_messages()

# ========== КЕШ ИМЁН ==========
_name_cache = {}
_user_name_cache = {}  # для имён по ID пользователя

async def get_user_name_by_id(client: Client, user_id: int) -> str:
    """Возвращает имя пользователя по его ID с кешированием."""
    if user_id is None:
        return "Неизвестный"
    if user_id in _user_name_cache:
        return _user_name_cache[user_id]

    # Проверяем, может быть это наш собственный ID
    if client.me and user_id == client.me.contact.id:
        # Имя самого себя можно взять из client.me
        name = None
        if hasattr(client.me.contact, 'firstname'):
            name = client.me.contact.firstname
            if hasattr(client.me.contact, 'lastname') and client.me.contact.lastname:
                name += " " + client.me.contact.lastname
        if name:
            _user_name_cache[user_id] = name
            return name
        else:
            _user_name_cache[user_id] = "Я"
            return "Я"

    # Пытаемся получить пользователя через get_user
    user = None
    if hasattr(client, 'get_user'):
        try:
            user = await client.get_user(user_id)
        except Exception:
            pass
    if user is None and hasattr(client, 'get_cached_user'):
        try:
            user = client.get_cached_user(user_id)
        except Exception:
            pass
    if user is None and hasattr(client, 'contacts'):
        contacts = client.contacts
        if isinstance(contacts, dict) and user_id in contacts:
            user = contacts[user_id]
        elif isinstance(contacts, list):
            for c in contacts:
                if getattr(c, 'id', None) == user_id:
                    user = c
                    break

    if user is not None:
        name = None
        if hasattr(user, 'names') and user.names and len(user.names) > 0:
            name_obj = user.names[0]
            if hasattr(name_obj, 'first_name') and name_obj.first_name:
                name = name_obj.first_name
                if hasattr(name_obj, 'last_name') and name_obj.last_name:
                    name += " " + name_obj.last_name
            elif hasattr(name_obj, 'name') and name_obj.name:
                name = name_obj.name
        if name is None:
            if hasattr(user, 'firstname'):
                name = user.firstname
                if hasattr(user, 'lastname') and user.lastname:
                    name += " " + user.lastname
            elif hasattr(user, 'first_name'):
                name = user.first_name
                if hasattr(user, 'last_name') and user.last_name:
                    name += " " + user.last_name
            elif hasattr(user, 'display_name'):
                name = user.display_name
            elif hasattr(user, 'name'):
                name = user.name
            elif hasattr(user, 'username'):
                name = user.username
            elif isinstance(user, dict):
                name = user.get('firstname') or user.get('first_name') or user.get('display_name') or user.get('name') or user.get('username')
        if name:
            _user_name_cache[user_id] = name
            return name

    # Если не удалось получить имя, возвращаем ID как строку
    _user_name_cache[user_id] = str(user_id)
    return str(user_id)

async def get_contact_name(client: Client, chat) -> str:
    """Асинхронно возвращает отображаемое имя для чата."""
    chat_id = getattr(chat, 'id', None) or getattr(chat, 'chat_id', None)
    if chat_id is None:
        return "Без ID"

    if chat_id in _name_cache:
        return _name_cache[chat_id]

    is_group = getattr(chat, 'is_group', False)
    is_channel = getattr(chat, 'is_channel', False)

    if is_group or is_channel:
        title = getattr(chat, 'title', None) or getattr(chat, 'name', None) or str(chat_id)
        _name_cache[chat_id] = title
        return title

    participants = getattr(chat, 'participants', None)
    if participants and isinstance(participants, dict):
        my_id = client.me.contact.id if client.me else None
        partner_id = None
        for uid in participants.keys():
            if my_id is not None and uid == my_id:
                continue
            partner_id = uid
            break

        if partner_id is not None:
            # Используем get_user_name_by_id для получения имени
            name = await get_user_name_by_id(client, partner_id)
            _name_cache[chat_id] = name
            return name

    title = getattr(chat, 'title', None) or getattr(chat, 'name', None) or str(chat_id)
    _name_cache[chat_id] = title
    return title

# ========== ОБРАБОТЧИК ЗАПУСКА ==========
@client.on_start()
async def on_start(client: Client) -> None:
    print("✅ Клиент MAX успешно запущен")
    if client.me:
        print(f"👤 Ваш ID: {client.me.contact.id}")
        print(f"📱 Ваш номер: {client.me.contact.phone}")
    print(f"📁 Сессия сохранена в: {WORK_DIR}/{SESSION_NAME}")
    print(f"📄 Входящие сообщения сохраняются в: {WORK_DIR}/{MESSAGES_FILE}")
    asyncio.create_task(interactive_menu(client))
    print("⏳ Ожидание входящих сообщений... (для меню используйте консоль)\n")

# ========== ИНТЕРАКТИВНОЕ МЕНЮ ==========
async def interactive_menu(client: Client) -> None:
    await asyncio.sleep(1)
    while True:
        print("\n" + "-" * 40)
        print("МЕНЮ:")
        print("  1. Список чатов")
        print("  2. История сообщений в чате")
        print("  3. Выйти из меню (продолжить прослушку)")
        choice = input("Выберите действие (1/2/3): ").strip()
        if choice == "1":
            await show_dialogs(client)
        elif choice == "2":
            await show_chat_history(client)
        elif choice == "3":
            print("⏳ Возврат к прослушке...")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

# ========== ПОКАЗ СПИСКА ЧАТОВ ==========
async def show_dialogs(client: Client) -> None:
    try:
        if hasattr(client, 'fetch_chats'):
            print("📥 Загрузка списка чатов...")
            await client.fetch_chats()
        elif hasattr(client, 'get_chats'):
            dialogs = await client.get_chats()
            if dialogs:
                client.chats = dialogs

        dialogs = getattr(client, 'chats', None)
        if not dialogs:
            if hasattr(client, 'get_chats'):
                dialogs = await client.get_chats()
                if dialogs:
                    client.chats = dialogs

        if not dialogs:
            print("📭 Чатов не найдено.")
            return

        print("\n--- СПИСОК ЧАТОВ ---")
        for i, dialog in enumerate(dialogs, 1):
            chat_id = getattr(dialog, 'id', None) or getattr(dialog, 'chat_id', None)
            display_name = await get_contact_name(client, dialog)

            last_msg = getattr(dialog, 'last_message', None)
            last_text = last_msg.text if last_msg and hasattr(last_msg, 'text') else "Нет сообщений"
            chat_type = "Группа" if (getattr(dialog, 'is_group', False) or getattr(dialog, 'is_channel', False)) else "Личный"
            print(f"{i}. {display_name} ({chat_type}, ID: {chat_id}) — последнее: {last_text[:20].split('\n')[0]}")
    except Exception as e:
        print(f"⚠️ Ошибка получения чатов: {e}")

# ========== УНИВЕРСАЛЬНЫЙ ВЫЗОВ МЕТОДА С АВТОПОДБОРОМ ПАРАМЕТРОВ ==========
async def call_method_with_limit(obj, method_name, chat_id, limit=20):
    method = getattr(obj, method_name, None)
    if method is None:
        return None
    sig = inspect.signature(method)
    params = sig.parameters
    kwargs = {}
    if 'limit' in params:
        kwargs['limit'] = limit
    elif 'count' in params:
        kwargs['count'] = limit
    elif 'num' in params:
        kwargs['num'] = limit
    elif 'size' in params:
        kwargs['size'] = limit
    try:
        if kwargs:
            return await method(chat_id, **kwargs)
        else:
            # пробуем вызвать с chat_id
            try:
                return await method(chat_id)
            except TypeError:
                # если не принимает chat_id, вызываем без аргументов
                return await method()
    except TypeError as e:
        # пробуем без аргументов
        try:
            return await method()
        except:
            raise

# ========== ПОКАЗ ИСТОРИИ СООБЩЕНИЙ ==========
async def show_chat_history(client: Client) -> None:
    chat_id_input = input("Введите ID чата (число): ").strip()
    if not chat_id_input.isdigit():
        print("❌ ID должен быть числом.")
        return
    chat_id = int(chat_id_input)

    try:
        messages = None
        for method_name in ['get_messages', 'fetch_history', 'get_history']:
            if hasattr(client, method_name):
                try:
                    messages = await call_method_with_limit(client, method_name, chat_id, 20)
                    if messages is not None:
                        break
                except Exception:
                    continue

        if messages is None:
            print("❌ Не удалось получить историю сообщений.")
            return

        if not messages:
            print(f"📭 В чате {chat_id} сообщений нет.")
            return

        if len(messages) > 20:
            messages = messages[:20]

        print(f"\n--- ПОСЛЕДНИЕ {len(messages)} СООБЩЕНИЙ В ЧАТЕ {chat_id} ---")
        for msg in messages:
            # Определяем ID отправителя
            sender_id = None
            if hasattr(msg, 'sender_id'):
                sender_id = msg.sender_id
            elif hasattr(msg, 'sender'):
                if isinstance(msg.sender, int):
                    sender_id = msg.sender
                elif hasattr(msg.sender, 'id'):
                    sender_id = msg.sender.id

            # Получаем имя отправителя
            sender_name = await get_user_name_by_id(client, sender_id)

            text = getattr(msg, 'text', '') or ''
            date = getattr(msg, 'date', None)
            if date is None:
                date = getattr(msg, 'timestamp', datetime.now())
            if hasattr(date, 'isoformat'):
                time_str = date.strftime('%Y.%m.%d %H:%M:%S')
            else:
                time_str = str(date)

            print(f"[{time_str}] {sender_name}: {text[:100]}")
    except Exception as e:
        print(f"⚠️ Ошибка получения истории: {e}")

# ========== ОБРАБОТЧИК ВХОДЯЩИХ СООБЩЕНИЙ ==========
@client.on_message()
async def on_message(message: Message, client: Client) -> None:
    try:
        sender_id = None
        if hasattr(message, 'sender_id'):
            sender_id = message.sender_id
        elif hasattr(message, 'sender'):
            if isinstance(message.sender, int):
                sender_id = message.sender
            elif hasattr(message.sender, 'id'):
                sender_id = message.sender.id

        if client.me and sender_id is not None:
            if sender_id == client.me.contact.id:
                return

        sender_name = None
        if hasattr(message, 'sender') and hasattr(message.sender, 'firstname'):
            sender_name = message.sender.firstname
        elif hasattr(message, 'sender_name'):
            sender_name = message.sender_name

        message_data = {
            "id": message.id,
            "chat_id": message.chat_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "text": message.text,
            "timestamp": datetime.now().strftime('%Y.%m.%d %H:%M:%S'),
        }
        saved_messages.append(message_data)
        save_messages(saved_messages)

        print(f"\n📨 Новое сообщение от {sender_name or sender_id}:")
        print(f"   Текст: {message_data['text']}")
        print(f"   Чат ID: {message_data['chat_id']}")

        if message.chat_id is not None and message.text:
            reply_text = "✅ Ваше сообщение получено и сохранено в JSON!"
            if hasattr(message, 'answer'):
                await message.answer(reply_text)
            else:
                await client.send_message(chat_id=message.chat_id, text=reply_text)
            print(f"   ✅ Отправлен ответ: {reply_text}")

    except Exception as e:
        print(f"⚠️ Ошибка при обработке сообщения: {e}")

# ========== ЗАПУСК ==========
async def main() -> None:
    try:
        await client.start()
    except KeyboardInterrupt:
        print("\n🛑 Клиент остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
