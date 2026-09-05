import asyncio
import json
import inspect
import os
from datetime import datetime, timedelta
from pathlib import Path
from requests import get
from pymax import Client, Message

# ========== КОНФИГУРАЦИЯ ==========
PHONE = "+79990000000"          # Ваш номер в формате +7XXXXXXXXXX
WORK_DIR = "instance"
SESSION_NAME = "Max.db"
MAX_CHATS = 'max_chats.json'
MESSAGES_FILE = "messages.json"
TRANPORT_FILE = "max.helpfile"
MAX_MESSAGES  = 'max_messages.json'
DEFAULT = open('default.helpfile').readlines()[0][:-1]
MESSAGES: dict[str, list[dict[str, str]]] = json.load(open(MAX_MESSAGES, encoding='utf-8'))
LIM = 75

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

# ========== ИНТЕРАКТИВНОЕ МЕНЮ ==========
async def interactive_menu(client: Client) -> None:
    await asyncio.sleep(1)
    i = 0
    
    c: list[dict[str, str]] = await show_dialogs(client)
    if c:
        open(MAX_CHATS, 'w', encoding='utf-8').write(json.dumps(c, ensure_ascii=False).replace('{', '\n\t{'))
    while True:
        await asyncio.sleep(10)
        i += 10
        h: list[dict[str, str]] = await show_chat_history(client, DEFAULT)
        if h:
            MESSAGES[DEFAULT] = h
            json.dump(MESSAGES, open(MAX_MESSAGES, 'w', encoding='utf-8'), ensure_ascii=False)
        if 'DONE' != open(TRANPORT_FILE).read():
            h: list[dict[str, str]] = await show_chat_history(client, open(TRANPORT_FILE).read())
            if h:
                MESSAGES[open(TRANPORT_FILE).read()] = h
                json.dump(MESSAGES, open(MAX_MESSAGES, 'w', encoding='utf-8'), ensure_ascii=False)
                open(TRANPORT_FILE,'w').write('DONE')
        if i == 300:
            c: list[dict[str, str]] = await show_dialogs(client)
            if c:
                open(MAX_CHATS, 'w', encoding='utf-8').write(json.dumps(c, ensure_ascii=False).replace('{', '\n\t{'))
            i = 0

# ========== ПОКАЗ СПИСКА ЧАТОВ ==========
async def show_dialogs(client: Client):
    try:
        if hasattr(client, 'fetch_chats'):
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

        if not dialogs: return

        chats = []

        for dialog in dialogs:
            chat_id = getattr(dialog, 'id', None) or getattr(dialog, 'chat_id', None)
            display_name = await get_contact_name(client, dialog)

            last_msg = getattr(dialog, 'last_message', None)
            chat_type = "Группа" if (getattr(dialog, 'is_group', False) or getattr(dialog, 'is_channel', False)) else "Личный"
            chats.append({
                "name": display_name,
                "id": chat_id,
                "type": chat_type
            })
        return chats
    except Exception as e:
        print(f"⚠️ Ошибка получения чатов: {e}")

# ========== ПОКАЗ ИСТОРИИ СООБЩЕНИЙ ==========
async def show_chat_history(client: Client, id: str | int):
        chat_id = int(id)

        messages = await client.fetch_history(chat_id, backward=LIM)
        if not messages: return

        messes = []

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
            date = msg.time
            files: list[dict[str, str]] = []
            type = None
            for attachment in msg.attaches:
                info = [k for k in attachment.__dict__]
                try:
                    base_url = attachment.__dict__[[k for k in info if 'url' in k][0]]
                    media_id = attachment.__dict__[[k for k in info if  'id' in k][0]]
                except:
                    # print(attachment.__dict__)
                    continue
                file = f'{msg.id}_{media_id}'
                type = str(attachment.type).lower()
                type = type[type.find('.')+1:]
                type = 'img' if type[type.find('.')+1:] in ('photo', 'sticker') else type
                files.append({"file": file, "type": type})
                # print(type)
                if file not in [f[:-5] for f in os.listdir('static/max')]:
                    open(f'static/max/{file}.file', 'wb').write(get(base_url).content)
            time_str = (datetime(1970, 1, 1)+timedelta(days=date/1000/3600/24)+timedelta(hours=3)).strftime('%Y.%m.%d %H:%M:%S')

            messes.append({"time": time_str, "sender": sender_name, "text": text, "files": files})
        return messes

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

    except Exception as e:
        print(f"⚠️ Ошибка при обработке сообщения: {e}")

# ========== ЗАПУСК ==========
async def main() -> None:
    while True:
        try:
            await client.start()
        except KeyboardInterrupt:
            print("\n🛑 Клиент остановлен пользователем")
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
