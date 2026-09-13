import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from requests import get
from pymax import Client, Message
from PIL import Image

# ========== КОНФИГУРАЦИЯ ==========
PHONE = "+79990000000"          # Ваш номер в формате +7XXXXXXXXXX
WORK_DIR = "instance"
SESSION_NAME = "Max.db"
MAX_CHATS = 'max_chats.json'
TRANPORT_FILE = "max.helpfile"
MAX_MESSAGES = 'max_messages.json'
DEFAULT = open('default.helpfile').readlines()[0][:-1]
MESSAGES: dict[str, list[dict[str, str | int]]] = json.load(
    open(MAX_MESSAGES, encoding='utf-8'))
LIM = 75

logging.disable()

# ========== ИНИЦИАЛИЗАЦИЯ КЛИЕНТА ==========
client = Client(
    phone=PHONE,
    work_dir=WORK_DIR,
    session_name=SESSION_NAME,
)

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
                name = user.get('firstname') or user.get('first_name') or user.get(
                    'display_name') or user.get('name') or user.get('username')
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
        title = getattr(chat, 'title', None) or getattr(
            chat, 'name', None) or str(chat_id)
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

    title = getattr(chat, 'title', None) or getattr(
        chat, 'name', None) or str(chat_id)
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
    asyncio.create_task(interactive_menu(client))

# ========== ИНТЕРАКТИВНОЕ МЕНЮ ==========


async def interactive_menu(client: Client) -> None:
    await asyncio.sleep(1)
    i = 0

    c: list[dict[str, str]] = await show_dialogs(client)
    if c:
        open(MAX_CHATS, 'w', encoding='utf-8').write(json.dumps(c,
                                                                ensure_ascii=False, indent=4))
    while True:
        await asyncio.sleep(30)
        i += 30
        if DEFAULT not in MESSAGES:
            MESSAGES[DEFAULT] = []
        h: list[dict[str, str]] = await show_chat_history(client, DEFAULT)
        if h:
            for m in h:
                MESSAGES[DEFAULT].append(m)
            json.dump(MESSAGES, open(MAX_MESSAGES, 'w',
                      encoding='utf-8'), ensure_ascii=False, indent=4)
        if 'DONE' != open(TRANPORT_FILE).read():
            if open(TRANPORT_FILE).read() not in MESSAGES:
                MESSAGES[open(TRANPORT_FILE).read()] = []
            h: list[dict[str, str]] = await show_chat_history(client, open(TRANPORT_FILE).read())
            if h:
                for m in h:
                    MESSAGES[open(TRANPORT_FILE).read()].append(m)
                json.dump(MESSAGES, open(MAX_MESSAGES, 'w',
                          encoding='utf-8'), ensure_ascii=False, indent=4)
            open(TRANPORT_FILE, 'w').write('DONE')
        if i == 1800:
            c: list[dict[str, str]] = await show_dialogs(client)
            if c:
                open(MAX_CHATS, 'w', encoding='utf-8').write(json.dumps(c,
                                                                        ensure_ascii=False, indent=4))
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

        if not dialogs:
            return

        chats = []

        for dialog in dialogs:
            chat_id = getattr(dialog, 'id', None) or getattr(
                dialog, 'chat_id', None)
            display_name = await get_contact_name(client, dialog)

            last_msg = getattr(dialog, 'last_message', None)
            chat_type = "Группа" if (getattr(dialog, 'is_group', False) or getattr(
                dialog, 'is_channel', False)) else "Личный"
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

    if not os.path.isdir(f'static/max/{chat_id}'):
        os.mkdir(f'static/max/{chat_id}')

    messages = await client.fetch_history(chat_id, backward=LIM)
    if not messages:
        return

    messes: list[dict[str, str]] = []

    for msg in messages:
        if msg.id not in [m['id'] for m in MESSAGES[str(id)]]:
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

            # Проверка на пересланное сообщение
            forwarded_info = None
            original_text = None
            original_files = []
            if hasattr(msg, 'link') and msg.link and hasattr(msg.link, 'chat_name'):
                original_message = msg.link.message
                forwarded_info = {
                    "original_chat_id": msg.link.chat_id,
                    "original_chat_name": msg.link.chat_name,
                    "original_message_id": original_message.id if hasattr(original_message, 'id') else None,
                }
                # Получаем текст из пересланного сообщения
                original_text = getattr(original_message, 'text', '') or ''

                for attachment in original_message.attaches:
                    file = None
                    ext = None
                    type = str(attachment.type).lower()
                    type = type[type.find('.')+1:]
                    type = 'img' if type[type.find(
                        '.')+1:] == 'photo' else type
                    info = [k for k in attachment.__dict__]
                    try:
                        base_url = attachment.__dict__[
                            [k for k in info if 'url' in k][0]]
                        media_id = attachment.__dict__[
                            [k for k in info if 'id' in k][0]]
                    except:
                        try:
                            if type == 'file':
                                media_id = attachment.file_id
                                file = attachment.name
                                type = 'a'
                                ext = 'file'
                                if file not in [f for f in os.listdir('static/max')]:
                                    base_url = (await client.get_file_by_id(chat_id, msg.id, media_id)).url
                            elif type == 'video':
                                media_id = attachment.video_id
                                ext = 'mp4'
                                file = f'{chat_id}/{msg.id}_{media_id}.{ext}' if not file else file
                                if file not in [f for f in os.listdir('static/max')]:
                                    base_url = (await client.get_video_by_id(chat_id, msg.id, media_id)).url
                            else:
                                continue
                        except:
                            continue
                    ext = ('png' if type == 'img' else ('mp4' if type == 'video' else (
                        'ogg' if type == 'audio' else 'file'))) if ext == None else ext
                    file = f'{chat_id}/{msg.id}_{media_id}.{ext}' if not file else file
                    original_files.append({"file": file, "type": type})
                    if file not in [f for f in os.listdir('static/max')]:
                        open(f'static/max/{file}',
                             'wb').write(get(base_url).content)
                        if type=='img' and 'WEBP' in open(f'static/max/{file}', encoding='ANSI').readlines()[0]:
                            im = Image.open(f'static/max/{file}')
                            im.save(f'static/max/{file}', 'PNG')

            date = msg.time
            files: list[dict[str, str]] = []
            for attachment in msg.attaches:
                file = None
                ext = None
                type = str(attachment.type).lower()
                type = type[type.find('.')+1:]
                type = 'img' if type[type.find('.')+1:] == 'photo' else type
                info = [k for k in attachment.__dict__]
                try:
                    base_url = attachment.__dict__[
                        [k for k in info if 'url' in k][0]]
                    media_id = attachment.__dict__[
                        [k for k in info if 'id' in k][0]]
                except:
                    if type == 'file':
                        media_id = attachment.file_id
                        file = attachment.name
                        type = 'a'
                        ext = 'file'
                        if file not in [f for f in os.listdir('static/max')]:
                            base_url = (await client.get_file_by_id(chat_id, msg.id, media_id)).url
                    elif type == 'video':
                        media_id = attachment.video_id
                        ext = 'mp4'
                        file = f'{chat_id}/{msg.id}_{media_id}.{ext}' if not file else file
                        if file not in [f for f in os.listdir('static/max')]:
                            base_url = (await client.get_video_by_id(chat_id, msg.id, media_id)).url
                    else:
                        continue
                ext = ('png' if type == 'img' else ('mp4' if type == 'video' else (
                    'ogg' if type == 'audio' else 'file'))) if ext == None else ext
                file = f'{chat_id}/{msg.id}_{media_id}.{ext}' if not file else file
                files.append({"file": file, "type": type})
                if file not in [f for f in os.listdir('static/max')]:
                    open(f'static/max/{file}',
                         'wb').write(get(base_url).content)
                    if type=='img' and 'WEBP' in open(f'static/max/{file}', encoding='ANSI').readlines()[0]:
                        im = Image.open(f'static/max/{file}')
                        im.save(f'static/max/{file}', 'PNG')
            time_str = (datetime(1970, 1, 1)+timedelta(days=date/1000 /
                        3600/24)+timedelta(hours=3)).strftime('%Y.%m.%d %H:%M:%S')

            f_info = {'sender': '', 'text': ''}
            if forwarded_info:
                original_sender_id = None
                if hasattr(original_message, 'sender_id'):
                    original_sender_id = original_message.sender_id
                elif hasattr(original_message, 'sender'):
                    if isinstance(original_message.sender, int):
                        original_sender_id = original_message.sender
                    elif hasattr(original_message.sender, 'id'):
                        original_sender_id = original_message.sender.id

                original_sender_name = await get_user_name_by_id(client, original_sender_id) if original_sender_id else "Неизвестный"
                f_info['sender'] = f" (от {original_sender_name})"
                if original_text:
                    f_info['text'] = f"↪️ Переслано из {forwarded_info['original_chat_name']}\n{original_text}\n"
                elif forwarded_info.get('original_chat_name'):
                    f_info['text'] = f"↪️ Переслано из {forwarded_info['original_chat_name']}\n"

            all_files = files + original_files if forwarded_info else files
            if f_info["text"]:
                f_info["text"] = '<i>'+f_info["text"]+'</i>'
            mess: dict[str, str] = {"time": time_str, "sender": sender_name + f_info["sender"],
                                    "text": f_info["text"] + text, "files": all_files, "id": msg.id}
            messes.append(mess)
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

        # Проверка на пересланное сообщение
        forwarded_info = None
        if hasattr(message, 'link') and message.link is not None:
            from pymax.types.domain.message import ForwardLink
            if isinstance(message.link, ForwardLink):
                forwarded_info = {
                    "original_chat_id": message.link.chat_id,
                    "original_chat_name": message.link.chat_name,
                    "original_message_id": message.link.message.id if hasattr(message.link.message, 'id') else None,
                    "original_text": message.link.message.text if hasattr(message.link.message, 'text') else None
                }

        # Проверка на ответ (reply) в том же чате - игнорируем такие сообщения
        if hasattr(message, 'reply_to') and message.reply_to is not None:
            return  # Игнорируем ответы на сообщения в том же чате

        # Дополнительная проверка для reply_to_message_id
        if hasattr(message, 'reply_to_message_id') and message.reply_to_message_id is not None:
            return  # Игнорируем ответы на сообщения в том же чате

        message_data = {
            "id": message.id,
            "chat_id": message.chat_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "text": message.text,
            "timestamp": datetime.now().strftime('%Y.%m.%d %H:%M:%S'),
            "forwarded_from": forwarded_info
        }

        print(f"\n📨 Новое сообщение от {sender_name or sender_id}:")
        print(f"   Текст: {message_data['text']}")
        print(f"   Чат ID: {message_data['chat_id']}")
        if forwarded_info:
            print(
                f"   ↪️ Переслано из: {forwarded_info.get('original_chat_name', 'Unknown')} (ID: {forwarded_info.get('original_chat_id')})")
            print(f'   ↪️ Переслано из: {forwarded_info["original_text"]}')

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
