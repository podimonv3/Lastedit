# Kanged From @TroJanZheX
# REDIRECT added https://github.com/Joelkb
import asyncio
import re
import ast
import math
import random
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, FILE_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, NOR_IMG, AUTH_GROUPS, P_TTI_SHOW_OFF, IMDB, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE, SPELL_IMG, MSG_ALRT, FILE_FORWARD, MAIN_CHANNEL, LOG_CHANNEL, PM_CHANNEL, NORES_CHANNEL, PICS, SUPPORT_CHAT_ID
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results, get_bad_files
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
from database.gfilters_mdb import (
    find_gfilter,
    get_gfilters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
FILTER_MODE = {}

@Client.on_message(filters.command('autofilterer') & filters.user(ADMINS))
async def fil_mod(client, message): 
      mode_on = ["yes", "on", "true"]
      mode_of = ["no", "off", "false"]

      try: 
         args = message.text.split(None, 1)[1].lower() 
      except: 
         return await message.reply("**𝙸𝙽𝙲𝙾𝙼𝙿𝙴𝚃𝙴𝙽𝚃 𝙲𝙾𝙼𝙼𝙰𝙳...**")
      
      m = await message.reply("**𝚂𝙴𝚃𝚃𝙸𝙽𝙶.../**")

      if args in mode_on:
          FILTER_MODE[str(message.chat.id)] = "True" 
          await m.edit("**𝙰𝚄𝚃𝙾𝙵𝙸𝙻𝚃𝙴𝚁 𝙴𝙽𝙰𝙱𝙻𝙴𝙳**")
      
      elif args in mode_of:
          FILTER_MODE[str(message.chat.id)] = "False"
          await m.edit("**𝙰𝚄𝚃𝙾𝙵𝙸𝙻𝚃𝙴𝚁 𝙳𝙸𝚂𝙰𝙱𝙻𝙴𝙳**")
      else:
          await m.edit("𝚄𝚂𝙴 :- /autofilter on 𝙾𝚁 /autofilter off")

@Client.on_message((filters.group) & filters.text & filters.incoming)
async def give_filter(client,message):
    await global_filters(client, message)
    group_id = message.chat.id
    name = message.text

    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await message.reply_text(reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            await message.reply_text(
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button)
                            )
                    elif btn == "[]":
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or ""
                        )
                    else:
                        button = eval(btn) 
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button)
                        )
                except Exception as e:
                    print(e)
                break 

    else:
        if FILTER_MODE.get(str(message.chat.id)) == "False":
            return
        else:
            await auto_filter(client, message)


@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id
    if content.startswith("/") or content.startswith("#"): return  # ignore commands and hashtags
    if user_id in ADMINS: return # ignore admins
    await message.reply_text("<b>Yᴏᴜʀ ᴍᴇssᴀɢᴇ/ʀᴇQᴜᴇꜱᴛ ʜᴀs ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ᴍʏ ᴛᴇᴀᴍ ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ꜰᴏʀ ʀᴇᴘʟᴀʏ!</b>")
    await bot.send_message(
        chat_id=PM_CHANNEL,
        text=f"<b>#𝐏𝐌_𝐌𝐒𝐆\n\nNᴀᴍᴇ : {user}</b>\n\nID :<code>{user_id}</code>\n\nMᴇssᴀɢᴇ : <code>{content}</code>"
    )

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(f"Nice Try", show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.", show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    settings = await get_settings(query.message.chat.id)
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"📁{get_size(file.file_size)}​⇛{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'files_#{file.file_id}',
                ),
            ]
            for file in files
        ]

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⇚ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"{math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ​ ​⇛", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⇚ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"{math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("ɴᴇxᴛ​ ​⇛", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

# spellcheck error fixing
@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    if not movies:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name),show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movie = movies[(int(movie_))]
    await query.answer(script.TOP_ALRT_MSG)
    search_query = movie.replace(' ', '+')
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:                
            btn = [[                
            InlineKeyboardButton('♻️ Request ♻️', url='http://t.me/Adarfilter_bot')
            ],[   
            InlineKeyboardButton('🌍𝙶𝙾𝙾𝙶𝙻𝙴🌍', url=f"https://google.com/search?q={search_query}+Release+date")
            ]]        
            k=await query.message.edit('<b>✯നിങ്ങൾ ചോദിച്ച മൂവി റിലീസ് ആയിട്ടുണ്ടോ..?\n✯Its Movie Released Or Not Check Imdb\n✯Movie Year ബട്ടൻ ഉള്ളതിൽ ക്ലിക്ക് ചെയ്യരുത്\n✯Dont Click Year Button⚠️\n🍂Or Click Request</b>', reply_markup=InlineKeyboardMarkup(btn))    
            await asyncio.sleep(60)
            await k.delete()


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer(MSG_ALRT)
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer(MSG_ALRT)

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer(MSG_ALRT)

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer(script.ALRT_TXT.format(query.from_user.first_name),show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer(MSG_ALRT)
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer(MSG_ALRT)
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer(MSG_ALRT)
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "gfilteralert" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_gfilter('gfilters', keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        clicked = query.from_user.id #fetching the ID of the user who clicked the button
        try:
            typed = query.message.reply_to_message.from_user.id #fetching user ID of the user who sent the movie request
        except:
            typed = clicked #if failed, uses the clicked user's ID as requested user ID
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        buttons = [[
            InlineKeyboardButton('🍂 ᴜᴘᴅᴀᴛᴇꜱ 🍂', url='https://t.me/+vg2zU33d_1c2YmQ1')
         ]]
        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            elif settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False 
                )
                await query.answer('★彡Hey Bruh..彡★\n\n✯ മൂവിയുടെ ഫയൽ ‍‍ഞാന്‍ pm ഇൽ ഇട്ടിട്ടുണ്ട് പോയി നോക്ക്..🏃\n\n✯ 𝖨 𝗁𝖺𝗏𝖾 𝗉𝗎𝗍 𝗍𝗁𝖾 𝖿𝗂𝗅𝖾 𝗈𝖿 𝗍𝗁𝖾 𝗆𝗈𝗏𝗂𝖾 𝖺𝗌 𝖺 𝗉𝗆. 𝖦𝗈 𝖠𝗇𝖽 𝖲𝖾𝖾', show_alert=True)
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer(f"Hey {query.from_user.first_name} I Like Your Smartness, But Don't Be Oversmart 😒ഒന്ന് ജോയിൻ ചെയ്യടാ ഉവ്വേ.. ഞങ്ങളും ജീവിച്ചു പൊക്കോട്ടെ😒", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        buttons = [[
            InlineKeyboardButton('🍂 ᴜᴘᴅᴀᴛᴇꜱ 🍂', url='https://t.me/+vg2zU33d_1c2YmQ1')
         ]]
        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False
        )
    elif query.data == "pages":
        await query.answer()

    elif query.data == "reqinfo":
        await query.answer("⚠ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ⚠\n\nᴀꜰᴛᴇʀ 10 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ\n\nɪꜰ ʏᴏᴜ ᴅᴏ ɴᴏᴛ ꜱᴇᴇ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴍᴏᴠɪᴇ / sᴇʀɪᴇs ꜰɪʟᴇ, ʟᴏᴏᴋ ᴀᴛ ᴛʜᴇ ɴᴇxᴛ ᴘᴀɢᴇ\n\n❣ ᴘᴏᴡᴇʀᴇᴅ ʙʏ ഉർവശി തീയറ്റേഴ്‌സ്", show_alert=True)

    elif query.data == "eng":
       xd = query.message.reply_to_message.text.replace(" ", "+")
       btn = [
           [
               InlineKeyboardButton("🌍𝙶𝙾𝙾𝙶𝙻𝙴🌍", url=f"https://www.google.com/search?q={xd}"),
               InlineKeyboardButton("back", callback_data="nlang")
           ]
       ]
       await query.message.edit_text(text=f"Hey {query.from_user.mention} 👋<b><u> If you want to get the movie, follow the below…</u>👇\n\n<i>🔹Ask for correct spelling. (English)\n\n🔸Ask for movies in English only.\n\n🔹Don't ask for unreleased movies.\n\n🔸 [Movie Name, Year, Language] Ask this way.\n\n🔹 Don't Use symbols while requesting movies. (+:;'!-`|...etc)\n\n🌏 Use the Google Button below for your movie details</b></i>", reply_markup=InlineKeyboardMarkup(btn))    

    elif query.data == "mal":
       xd = query.message.reply_to_message.text.replace(" ", "+")
       btn = [
           [
               InlineKeyboardButton("🌍𝙶𝙾𝙾𝙶𝙻𝙴🌍", url=f"https://www.google.com/search?q={xd}"),
               InlineKeyboardButton("back", callback_data="nlang")
           ]
       ]
       await query.message.edit_text(text=f"Hey {query.from_user.mention}👋 <b><u>നിങ്ങൾക്ക് സിനിമ കിട്ടണമെങ്കിൽ, താഴെ പറയുന്ന കാര്യങ്ങളിൽ ശ്രദ്ധിക്കുക...👇</u><I>\n\n🔹കറക്റ്റ് സ്പെല്ലിംഗിൽ ചോദിക്കുക. (ഇംഗ്ലീഷിൽ മാത്രം)\n\n🔸സിനിമകൾ ഇംഗ്ലീഷിൽ Type ചെയ്ത് മാത്രം ചോദിക്കുക.\n\n🔹റിലീസ് ആകാത്ത സിനിമകൾ ചോദിക്കരുത്.\n\n🔸[സിനിമയുടെ പേര്, വർഷം, ഭാഷ] ഈ രീതിയിൽ ചോദിക്കുക.\n\n🔹സിനിമ Request ചെയ്യുമ്പോൾ Symbols ഒഴിവാക്കുക. [+:;'*!-`&.. etc]\n\n🌏 നിങ്ങളുടെ സിനിമ വിശദാംശങ്ങൾക്കായി ചുവടെയുള്ള ഗൂഗിൾ ബട്ടൺ ഉപയോഗിക്കുക</b></i>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data == "tam":
       xd = query.message.reply_to_message.text.replace(" ", "+")
       btn = [
           [
               InlineKeyboardButton("🌍𝙶𝙾𝙾𝙶𝙻𝙴🌍", url=f"https://www.google.com/search?q={xd}"),
               InlineKeyboardButton("back", callback_data="nlang")
           ]
       ]    
       await query.message.edit_text(text=f"Hey {query.from_user.mention}👋 <b><u>நீங்கள் திரைப்படத்தைப் பெற விரும்பினால், கீழே குறிப்பிடப்பட்டுள்ள விஷயங்களைப் பின்பற்றவும்...👇</u><i>\n\n🔹சரியான எழுத்துப்பிழை கேட்கவும். (ஆங்கிலத்தில் மட்டும்)\n\n🔸திரைப்படங்களை ஆங்கிலத்தில் டைப் செய்து மட்டும் கேட்கவும்.\n\n🔹வெளியாத திரைப்படங்களைக் கேட்காதீர்கள்.\n\n🔸 [திரைப்படத்தின் பெயர், ஆண்டு, மொழி] இந்த வழியில் கேளுங்கள்.\n\n🔹திரைப்படங்களைக் கோரும் போது சின்னங்களைத் தவிர்க்கவும். [+:;'*!-&.. etc]\n\n🌎 உங்கள் திரைப்பட விவரங்களுக்கு கீழே உள்ள Google பட்டனைப் பயன்படுத்தவும்</b></i>", reply_markup=InlineKeyboardMarkup(btn))
     
    elif query.data == "tel":
       xd = query.message.reply_to_message.text.replace(" ", "+")
       btn = [
           [
               InlineKeyboardButton("🌍𝙶𝙾𝙾𝙶𝙻𝙴🌍", url=f"https://www.google.com/search?q={xd}"),
               InlineKeyboardButton("back", callback_data="nlang")
           ]
       ]
       await query.message.edit_text(text=f"Hey {query.from_user.mention}👋 <b><u>రు సినిమాని పొందాలనుకుంటే, క్రింద పేర్కొన్న విషయాలను అనుసరించండి...👇</u><i>\n\n🔹సరైన స్పెల్లింగ్ కోసం అడగండి. (ఇంగ్లీష్‌లో మాత్రమే)\n\n🔸సినిమాలను ఆంగ్లంలో టైప్ చేసి మాత్రమే అడగండి.\n\n🔹విడుదల కాని సినిమాలను అడగవద్దు.\n\n🔸 [సినిమా పేరు, సంవత్సరం, భాష] ఈ విధంగా అడగండి.\n\n🔹సినిమాలను అభ్యర్థించేటప్పుడు చిహ్నాలను నివారించండి. [+:;'*!-&.. etc]\n\n🌎 మీ సినిమా వివరాల కోసం దిగువన ఉన్న Google బటన్‌ని ఉపయోగించండి</b></i>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data == "hin":
       xd = query.message.reply_to_message.text.replace(" ", "+")
       btn = [
           [
               InlineKeyboardButton("🌍𝙶𝙾𝙾𝙶𝙻𝙴🌍", url=f"https://www.google.com/search?q={xd}"),
               InlineKeyboardButton("back", callback_data="nlang")
           ]
       ]
       await query.message.edit_text(text=f"Hey {query.from_user.mention}👋 <b><u>यदि आप मूवी प्राप्त करना चाहते हैं, तो नीचे दिए गए चरणों का पालन करें...</u><i>👇\n\n🔹सही वर्तनी के लिए पूछें। (केवल अंग्रेज़ी में)\n\n🔸फिल्में अंग्रेजी में टाइप करें और केवल पूछें।\n\n🔹अप्रकाशित फिल्मों के लिए न पूछें।\n\n🔸 [मूवी का नाम, वर्ष, भाषा] इस तरह पूछें।\n\n🔹फिल्मों का अनुरोध करते समय प्रतीकों से बचें। [+:;'*!-&.. आदि]\n\n🌎अपनी मूवी के विवरण के लिए नीचे दिए गए Google बटन का उपयोग करें</b></i>", reply_markup=InlineKeyboardMarkup(btn))
    
    elif query.data == "nlang":
       btn_duction = InlineKeyboardButton("📖𝐌𝐮𝐬𝐭 𝐑𝐞𝐚𝐝📖", callback_data="minfo")

       intro_row = [btn_duction]
       btn_eng = InlineKeyboardButton("ᴇɴɢ", callback_data="eng")
       btn_mal = InlineKeyboardButton("ᴍᴀʟ", callback_data="mal")
       btn_hin = InlineKeyboardButton("ʜɪɴ", callback_data="hin")
       btn_tam = InlineKeyboardButton("ᴛᴀᴍ", callback_data="tam")
       btn_tel = InlineKeyboardButton("ᴛᴇʟ", callback_data="tel")

       language_row = [btn_eng, btn_mal, btn_hin, btn_tam, btn_tel]
       btn_google = InlineKeyboardButton("⚠️ Request ⚠️", url="http://t.me/Adarfilter_bot")

       google_row = [btn_google]

       keyboard = InlineKeyboardMarkup(inline_keyboard=[intro_row, language_row, google_row])
 
       await query.message.edit_text(text=f"<b>{query.from_user.mention}\nI couldn't find anything related to your request 🧞‍♀️ \nYou can find the way to get the movie from the buttons below\n🧞‍♀️Click the below buttons for more Information</b>", reply_markup=keyboard)
        
    elif query.data == "minfo":
       await query.answer(
       text=(
            "🥇𝐆𝐨 𝐓𝐨 𝐆𝐨𝐨𝐠𝐥𝐞 𝐂𝐨𝐩𝐲 𝐂𝐨𝐫𝐫𝐞𝐜𝐭 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠 𝐢𝐧 𝗢𝗻𝗹𝘆 𝗘𝗻𝗴𝗹𝗶𝘀𝗵 𝗟𝗲𝘁𝘁𝗲𝗿𝘀 𝐀𝐧𝐝 𝐒𝐞𝐧𝐭 𝐢𝐭🎯\n\n"
            "𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐅𝐨𝐫𝐦𝐚𝐭:-\n"
            "Movies - Varisu 2023\n"
            "Series - Dark S01 E01\n\n"
            "𝗠𝗼𝗿𝗲 𝗜𝗻𝗳𝗼𝗿𝗺𝗮𝘁𝗶𝗼𝗻 :- 𝖢𝗅𝗂𝖼𝗄 𝖮𝗇 𝖳𝗁𝖾 𝖡𝗎𝗍𝗍𝗈𝗇 𝖨𝗇 𝖸𝗈𝗎𝗋 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾 𝖻𝖾𝗅𝗈𝗐🪝"
        ),
        show_alert=True
    )
    
    elif query.data == "sinfo":
        await query.answer("⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯\nꜱᴇʀɪᴇꜱ ʀᴇǫᴜᴇꜱᴛ ꜰᴏʀᴍᴀᴛ\n⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯\n\nɢᴏ ᴛᴏ ɢᴏᴏɢʟᴇ ➠ ᴛʏᴘᴇ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ➠ ᴄᴏᴘʏ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ➠ ᴘᴀꜱᴛᴇ ᴛʜɪꜱ ɢʀᴏᴜᴘ\n\nᴇxᴀᴍᴘʟᴇ : ᴍᴏɴᴇʏ ʜᴇɪsᴛ S01E01\n\n🚯 ᴅᴏɴᴛ ᴜꜱᴇ ➠ ':(!,./)\n\n©️ ᴄɪɴᴇᴍᴀʟᴀ.ᴄᴏᴍ", show_alert=True)      

    elif query.data == "tinfo":
        await query.answer("▣ ᴛɪᴘs ▣\n\n★ ᴛʏᴘᴇ ᴄᴏʀʀᴇᴄᴛ sᴘᴇʟʟɪɴɢ (ɢᴏᴏɢʟᴇ)\n\n★ ɪғ ʏᴏᴜ ɴᴏᴛ ɢᴇᴛ ʏᴏᴜʀ ғɪʟᴇ ɪɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴛʜᴇɴ ᴛʜᴇ ɴᴇxᴛ sᴛᴇᴘ ɪs ᴄʟɪᴄᴋ ɴᴇxᴛ ʙᴜᴛᴛᴏɴ.\n\n★ ᴄᴏɴᴛɪɴᴜᴇ ᴛʜɪs ᴍᴇᴛʜᴏᴅ ᴛᴏ ɢᴇᴛᴛɪɴɢ ʏᴏᴜ ғɪʟᴇ\n\n❣ ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴄɪɴᴇᴍᴀʟᴀ. ᴄᴏᴍ", show_alert=True)

    elif query.data == "neosub": 
        await query.answer(f"✯ താഴെയുള്ള ബട്ടണിൽ വേണ്ട ക്വാളിറ്റി യിൽ ക്ലിക്ക് ചെയ്താൽ കിട്ടും⚡\n\n✯ 𝖢𝗅𝗂𝖼𝗄 𝗈𝗇 𝗍𝗁𝖾 𝗙𝗶𝗹𝗲 𝗡𝗮𝗺𝗲 𝖻𝖾𝗅𝗈𝗐 𝖻𝗎𝗍𝗍𝗈𝗇 🌈 𝖠𝗇𝖽 𝖲𝗍𝖺𝗋𝗍 𝖳𝗁𝖾 𝖡𝗈𝗍 🎯",show_alert=True)

    elif query.data == "whyjoin":
        await query.answer(text="⚠ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ⚠\n\nIғ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴄᴏᴘʏ ʀɪɢʜᴛ ɪꜱ ʟᴏꜱᴛ , ᴡʜᴇɴ ᴀ ɴᴇᴡ ᴄʜᴀɴɴᴇʟ ɪꜱ ꜱᴛᴀʀᴛᴇᴅ, ɪᴛ ᴡɪʟʟ ʙᴇ ɴᴏᴛɪғɪᴇᴅ ᴏɴ ᴛʜɪꜱ ᴄʜᴀɴɴᴇʟ 🙂", show_alert=True)  

    elif query.data == "start":
        buttons = [[                   
                    InlineKeyboardButton("• ɢʀᴏᴜᴘ •", url="https://t.me/+vg2zU33d_1c2YmQ1"),
                    InlineKeyboardButton("• ᴄʜᴀɴɴᴇʟ •", url="https://t.me/UrvashiTheaters_links")
                  ],[
                    InlineKeyboardButton('• ɪꜱꜱᴜᴇꜱ ᴏꜰ ʙᴏᴛ 👉ᴄᴏɴᴛᴀᴄᴛ•', url='https://t.me/PowerOfTG')
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )       
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('Gʟᴏʙᴀʟ Fɪʟᴛᴇʀs', callback_data='global_filters')                    
        ], [
            InlineKeyboardButton('Home ', callback_data='start'),
            InlineKeyboardButton('About', callback_data='about')                          
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    elif query.data == "global_filters":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='help')
        ]]        
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "movieinfo":
        await query.answer("⚠ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ⚠\n\nᴀꜰᴛᴇʀ 20 ᴍɪɴᴜᴛᴇ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ\n\nɪꜰ ʏᴏᴜ ᴅᴏ ɴᴏᴛ ꜱᴇᴇ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴍᴏᴠɪᴇ / sᴇʀɪᴇs ꜰɪʟᴇ, ʟᴏᴏᴋ ᴀᴛ ᴛʜᴇ ɴᴇxᴛ ᴘᴀɢᴇ", show_alert=True)
            
    elif query.data == "movss":
        await query.answer("⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯\nᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ ꜰᴏʀᴍᴀᴛ\n⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯\n\nɢᴏ ᴛᴏ ɢᴏᴏɢʟᴇ ➠ ᴛʏᴘᴇ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ➠ ᴄᴏᴘʏ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ➠ ᴘᴀꜱᴛᴇ ᴛʜɪꜱ ɢʀᴏᴜᴘ\n\nᴇxᴀᴍᴘʟᴇ : ᴋɢꜰ ᴄʜᴀᴘᴛᴇʀ 2 2022\n\n🚯 ᴅᴏɴᴛ ᴜꜱᴇ ➠ ':(!,./)", show_alert=True)

    elif query.data == "moviis":  
        await query.answer("⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯\nꜱᴇʀɪᴇꜱ ʀᴇǫᴜᴇꜱᴛ ꜰᴏʀᴍᴀᴛ\n⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯\n\nɢᴏ ᴛᴏ ɢᴏᴏɢʟᴇ ➠ ᴛʏᴘᴇ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ➠ ᴄᴏᴘʏ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ➠ ᴘᴀꜱᴛᴇ ᴛʜɪꜱ ɢʀᴏᴜᴘ\n\nᴇxᴀᴍᴘʟᴇ : ʟᴏᴋɪ S01E01\n\n🚯 ᴅᴏɴᴛ ᴜꜱᴇ ➠ ':(!,./)", show_alert=True)   

    elif query.data == "myr": 
        await query.answer(f"✯ താഴെയുള്ള ബട്ടണിൽ വേണ്ട ക്വാളിറ്റി യിൽ ക്ലിക്ക് ചെയ്താൽ കിട്ടും⚡\n\n✯ 𝖢𝗅𝗂𝖼𝗄 𝗈𝗇 𝗍𝗁𝖾 𝗙𝗶𝗹𝗲 𝗡𝗮𝗺𝗲 𝖻𝖾𝗅𝗈𝗐 𝖻𝗎𝗍𝗍𝗈𝗇 🌈 𝖠𝗇𝖽 𝖲𝗍𝖺𝗋𝗍 𝖳𝗁𝖾 𝖡𝗈𝗍 🎯",show_alert=True)

    elif query.data == "funda":
        await query.answer("✯ 𝖢𝗁𝖾𝖼𝗄 𝖮𝖳𝖳 𝖱𝖾𝗅𝖾𝖺𝗌𝖾 ᴏʀ 𝖢𝗈𝗋𝗋𝖾𝖼𝗍 𝖳𝗁𝖾 𝗌𝗉𝖾𝗅𝗅𝗂𝗇𝗀\n\n✯ 𝖣𝗈𝗇𝗍 𝖴𝗌𝖾 𝖲𝗒𝗆𝖻𝗈𝗅𝗌 𝖶𝗁𝗂𝗅𝖾 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 (,:'?!* 𝖾𝗍𝖼..)\n\n✯ [𝖬𝗈𝗏𝗂𝖾 𝖭𝖺𝗆𝖾 ,𝖸𝖾𝖺𝗋 ,𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾] 𝖠𝗌𝗄 𝖳𝗁𝗂𝗌 𝖶𝖺𝗒",show_alert=True)        

    elif query.data == "seriess":
        await query.answer("✯ 𝗦𝘁𝗲𝗽 1 :  𝖲𝖾𝗇𝖽 𝗍𝗁𝖾 𝗇𝖺𝗆𝖾 𝗈𝖿 𝗍𝗁𝖾 𝖬𝗈𝗏𝗂𝖾 𝗒𝗈𝗎 𝗐𝖺𝗇𝗍 𝗍𝗈 𝗍𝗁𝗂𝗌 𝗀𝗋𝗈𝗎𝗉\n\n✯ 𝗦𝘁𝗲𝗽 2 : 𝖢𝗅𝗂𝖼𝗄 𝗈𝗇 𝗍𝗁𝖾 𝖡𝗎𝗍𝗍𝗈𝗇 𝗈𝖿 𝗍𝗁𝖾 𝖬𝗈𝗏𝗂𝖾 𝗒𝗈𝗎 𝗐𝖺𝗇𝗍\n\n✯ 𝗦𝘁𝗲𝗽 3 : 𝖳𝗁𝖾𝗇 𝖢𝗅𝗂𝖼𝗄 𝗦𝘁𝗮𝗿𝘁 𝗈𝗇 𝗍𝗁𝖾 𝖡𝗈𝗍 𝖺𝗇𝖽 𝗒𝗈𝗎 𝗐𝗂𝗅𝗅 𝗀𝖾𝗍 𝗍𝗁𝖾 𝖬𝗈𝗏𝗂𝖾",show_alert=True)        
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)        
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='start'),
            InlineKeyboardButton('ʀᴇғʀᴇsʜ', callback_data='rfrsh')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "rfrsh":
        await query.answer("𝙁𝙚𝙩𝙘𝙝𝙞𝙣𝙜 𝙈𝙤𝙣𝙜𝙤𝘿𝙗 𝘿𝙖𝙩𝙖𝘽𝙖𝙨𝙚")
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='stats'),
            InlineKeyboardButton('ʀᴇғʀᴇsʜ', callback_data='rfrsh')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return await query.answer(MSG_ALRT)

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)
        try:
            if settings['auto_delete']:
                settings = await get_settings(grp_id)
        except KeyError:
            await save_group_settings(grp_id, 'auto_delete', True)
            settings = await get_settings(grp_id)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Filter Button',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Single' if settings["button"] else 'Double',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Redirect To', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Bot PM' if settings["botpm"] else 'Channel',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('File Secure',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["file_secure"] else '❌ No',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('IMDB', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["imdb"] else '❌ No',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Spell Check',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["spell_check"] else '❌ No',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Welcome', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["welcome"] else '❌ No',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Auto Delete',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10 Mins' if settings["auto_delete"] else 'OFF',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ]
                
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer(MSG_ALRT)


async def auto_filter(client, msg, spoll=False):
    reqstr1 = msg.from_user.id if msg.from_user else 0
    reqstr = await client.get_users(reqstr1)    
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(client, msg)
                else:
                    await client.send_message(chat_id=NORES_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, search)))
                    return
        else:
            return
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    pre = 'filep' if settings['file_secure'] else 'file'
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"📁{get_size(file.file_size)}​⇛{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
            ]
            for file in files
        ]

    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="ɴᴇxᴛ​ ​⇛", callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="ᴛʜᴇ ᴇɴᴅᠰ", callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b>☞αѕκє∂ ϐγ</b>:- {message.from_user.mention}\n<b>☞τιτℓє</b> :- {search}\n<b>☞ƒιℓєѕ</b> :- {str(total_results)}\n\n<b>★ροωєяє∂ ϐγ</b> :-<b> {message.chat.title}</b>"
    if imdb and imdb.get('poster'):
        try:
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention}, {str(total_results)} ʀᴇsᴜʟᴛs ᴀʀᴇ ғᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {search}. Kɪɴᴅʟʏ ᴜsᴇ 👉 <b>https://t.me/+vg2zU33d_1c2YmQ1</b> ɢʀᴏᴜᴘ. Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...</b>")
            else:
                hehe = await message.reply_text(text=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(180)
                        await hehe.delete()
                        await message.delete()
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(180)
                        await hehe.delete()
                        await message.delete()
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention}, {str(total_results)} ʀᴇsᴜʟᴛs ᴀʀᴇ ғᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {search}. Kɪɴᴅʟʏ ᴜsᴇ 👉 <b>https://t.me/+vg2zU33d_1c2YmQ1</b> ɢʀᴏᴜᴘ. Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...</b>")
            else:
                pic = imdb.get('poster')
                poster = pic.replace('.jpg', "._V1_UX360.jpg")
                hmm = await message.reply_text(text=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(180)
                        await hmm.delete()
                        await message.delete()
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(180)
                        await hmm.delete()
                        await message.delete()
        except Exception as e:
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention}, {str(total_results)} ʀᴇsᴜʟᴛs ᴀʀᴇ ғᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {search}. Kɪɴᴅʟʏ ᴜsᴇ 👉 <b>https://t.me/+vg2zU33d_1c2YmQ1</b> ɢʀᴏᴜᴘ. Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...</b>")
            else:
                logger.exception(e)
                fek = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(180)
                        await fek.delete()
                        await message.delete()
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(180)
                        await fek.delete()
                        await message.delete()
    else:
        if message.chat.id == SUPPORT_CHAT_ID:
            await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention}, {str(total_results)} ʀᴇsᴜʟᴛs ᴀʀᴇ ғᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {search}. Kɪɴᴅʟʏ ᴜsᴇ 👉 <b>https://t.me/+vg2zU33d_1c2YmQ1</b> ɢʀᴏᴜᴘ. Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...</b>")
        else:
            fuk = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
            try:
                if settings['auto_delete']:
                    await asyncio.sleep(180)
                    await fuk.delete()
                    await message.delete()
            except KeyError:
                grpid = await active_connection(str(message.from_user.id))
                await save_group_settings(grpid, 'auto_delete', True)
                settings = await get_settings(message.chat.id)
                if settings['auto_delete']:
                    await asyncio.sleep(180)
                    await fuk.delete()
                    await message.delete()
    
    if spoll:
        await msg.message.delete()


async def advantage_spell_chok(client, msg):
    mv_id = msg.id
    mv_rqst = msg.text
    reqstr1 = msg.from_user.id if msg.from_user else 0
    reqstr = await client.get_users(reqstr1)
    settings = await get_settings(msg.chat.id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    RQST = query.strip()
    query = query.strip() + " movie"
    try:
        movies = await get_poster(mv_rqst, bulk=True)
    except Exception as e:
        logger.exception(e)
        await client.send_message(chat_id=NORES_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
        k = await msg.reply(script.I_CUDNT.format(reqstr.mention))
        await asyncio.sleep(20)
        await k.delete()
        await msg.delete()
        return
    movielist = []
    if not movies:
        reqst_gle = mv_rqst.replace(" ", "+")
        btn_duction = InlineKeyboardButton("📖𝐌𝐮𝐬𝐭 𝐑𝐞𝐚𝐝📖", callback_data="minfo")

        intro_row = [btn_duction]
        btn_eng = InlineKeyboardButton("ᴇɴɢ", callback_data="eng")
        btn_mal = InlineKeyboardButton("ᴍᴀʟ", callback_data="mal")
        btn_hin = InlineKeyboardButton("ʜɪɴ", callback_data="hin")
        btn_tam = InlineKeyboardButton("ᴛᴀᴍ", callback_data="tam")
        btn_tel = InlineKeyboardButton("ᴛᴇʟ", callback_data="tel")

        language_row = [btn_eng, btn_mal, btn_hin, btn_tam, btn_tel]
        btn_google = InlineKeyboardButton("⚠️ Request ⚠️", url="http://t.me/Adarfilter_bot")

        google_row = [btn_google]

        keyboard = InlineKeyboardMarkup(inline_keyboard=[intro_row, language_row, google_row])

        k = await msg.reply_text(text=f"<b>🧞‍♀️I couldn't find anything related to your request \n🧞‍♀️You can find the way to get the movie from the buttons below\n🧞‍♀️Click the below buttons for more Information</b>", reply_markup=keyboard)
        await asyncio.sleep(120)
        await k.delete()
        await msg.delete()
        return
        

    movielist += [movie.get('title') for movie in movies]
    movielist += [f"{movie.get('title')} {movie.get('year')}" for movie in movies]
    SPELL_CHECK[mv_id] = movielist
    btn = [
        [
            InlineKeyboardButton(
                text=movie_name.strip(),
                callback_data=f"spol#{reqstr1}#{k}",
            )
        ]
        for k, movie_name in enumerate(movielist)
    ]
    btn.append([InlineKeyboardButton(text="⚠️ Request Here ⚠️", url="http://t.me/Adarfilter_bot")])
    k = await msg.reply(f"<b>🧞‍♀️താങ്കൾ ഉദ്ദേശിച്ച സിനിമ /സീരീസ് താഴെ കാണുന്ന വല്ലതും ആണ് എങ്കിൽ.അതിൽ ഡേറ്റ് ഇല്ലാത്തതിൽ ക്ലിക്ക്ചെ യ്യുക</b>\n<b>🧞‍♀️ɪ ᴄᴏᴜʟᴅɴ'ᴛ ꜰɪɴᴅ ᴀɴʏᴛʜɪɴɢ ʀᴇʟᴀᴛᴇᴅ ᴛᴏ ᴛʜᴀᴛ ᴅɪᴅ ʏᴏᴜ ᴍᴇᴀɴ ᴀɴʏ ᴏɴᴇ ᴏꜰ ᴛʜᴇꜱᴇ?</b>\n<b>⚠️ᴄʟɪᴄᴋ ᴛʜᴇ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ᴏɴʟʏ ᴅᴏɴᴛ ᴜꜱᴇ ʏᴇᴀʀ ʙᴜᴛᴛᴏɴ</b>",
                      reply_markup=InlineKeyboardMarkup(btn))
    await asyncio.sleep(60)
    await k.delete()
    await msg.delete()

async def manual_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            elsa = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                protect_content=True if settings["file_secure"] else False,
                                reply_to_message_id=reply_id
                            )
                            try:
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_ffilter', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            try:
                                if settings['auto_delete']:
                                    await asyncio.sleep(600)
                                    await elsa.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_delete', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_delete']:
                                    await asyncio.sleep(600)
                                    await elsa.delete()

                        else:
                            button = eval(btn)
                            hmm = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                protect_content=True if settings["file_secure"] else False,
                                reply_to_message_id=reply_id
                            )
                            try:
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_ffilter', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            try:
                                if settings['auto_delete']:
                                    await asyncio.sleep(600)
                                    await hmm.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_delete', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_delete']:
                                    await asyncio.sleep(600)
                                    await hmm.delete()

                    elif btn == "[]":
                        oto = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            protect_content=True if settings["file_secure"] else False,
                            reply_to_message_id=reply_id
                        )
                        try:
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_ffilter', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        try:
                            if settings['auto_delete']:
                                await asyncio.sleep(600)
                                await oto.delete()
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_delete', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_delete']:
                                await asyncio.sleep(600)
                                await oto.delete()

                    else:
                        button = eval(btn)
                        dlt = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        try:
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_ffilter', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        try:
                            if settings['auto_delete']:
                                await asyncio.sleep(600)
                                await dlt.delete()
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_delete', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_delete']:
                                await asyncio.sleep(600)
                                await dlt.delete()

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False

async def global_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_gfilters('gfilters')
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_gfilter('gfilters', keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            joelkb = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id
                            )
                            
                        else:
                            button = eval(btn)
                            hmm = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )

                    elif btn == "[]":
                        oto = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )

                    else:
                        button = eval(btn)
                        dlt = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )                       

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
