import re


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
        chunks = []
        for x in range(0, len(text), 4096):
            chunk = text[x:x+4096]
            if x > 0:
                # Find unclosed tags from the previous chunk
                unclosed_tags = re.findall(r'<([a-zA-Z]+)[^>]*>', chunks[-1])
                # Add opening tags to the current chunk
                chunk = ''.join(f'<{tag}>' for tag in reversed(unclosed_tags)) + chunk
            if x + 4096 < len(text):
                # Find and close tags that are left open
                open_tags = re.findall(r'<([a-zA-Z]+)[^>]*>', chunk)
                closed_tags = re.findall(r'</([a-zA-Z]+)>', chunk)
                unclosed_tags = [tag for tag in reversed(open_tags) if tag not in closed_tags]
                # Close unclosed tags
                chunk += ''.join(f'</{tag}>' for tag in unclosed_tags)
            chunks.append(chunk)

        for chunk in chunks:
            last_msg = bot.send_message(chat_id, chunk, *args, **kwargs)
    else:
        return bot.send_message(chat_id, text, *args, **kwargs)

    return last_msg


def send_pieces(bot, chat_id, pieces, topic_name=None):
    pieces = [f'{i+1}. <blockquote>{piece["data"]}</blockquote>' for i, piece in enumerate(pieces)]

    text = '<b>Порции</b>\n'
    
    if topic_name:
        text = f'<b>Тема "{topic_name}"</b>\n'

    for piece in pieces:
        if len(text) + len(piece) + 2 > 4096:
            bot.send_message(chat_id, text)
            text = ''
        text += '\n\n' + piece

    if text:
        bot.send_message(chat_id, text)