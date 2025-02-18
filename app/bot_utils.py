def send_long_message(bot, *args, **kwargs):
    if len(args) >= 1:
        chat_id = args[0]
        args = args[1:]
    else:
        chat_id = kwargs['chat_id']
        kwargs.pop('chat_id')

    if len(args) >= 1:
        text = args[0]
        args = args[1:]
    else:
        text = kwargs['text']
        kwargs.pop('text')

    last_msg = None
    if len(text) > 4096:
        for x in range(0, len(text), 4096):
            last_msg = bot.send_message(chat_id, text[x:x+4096], *args, **kwargs)
    else:
        return bot.send_message(chat_id, text, *args, **kwargs)
    
    return last_msg