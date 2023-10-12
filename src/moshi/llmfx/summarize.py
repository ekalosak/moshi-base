
        conversation = [Message(**msg) for msg in _conversation.values()]
        conversation.sort(key=lambda msg: msg.created_at)