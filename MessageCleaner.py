import os
import logging
import logging.config
from pyrubi import Client

MAX_MESSAGES = 1000

class MessageManager:
    def __init__(self, client):
        self.client = client
        self.logger = self.setup_logger()

    @staticmethod
    def setup_logger():
        logging_config = {
            'version': 1,
            'formatters': {
                'default': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                },
            },
            'root': {
                'level': 'INFO',
                'handlers': ['console'],
            },
        }
        logging.config.dictConfig(logging_config)
        return logging.getLogger(__name__)

    def get_all_messages(self, object_guid, max_message_id=None):
        all_messages = []
        count = 0
        while True:
            response = self.client.get_messages(object_guid, max_message_id)
            for message in response['messages']:
                yield message
                count += 1
                if count >= MAX_MESSAGES:
                    break
            if not response['has_continue'] or count >= MAX_MESSAGES:
                break
            max_message_id = response['new_max_id']

    def delete_messages(self, object_guid, messages):
        count_no_id = 0
        count_failed = 0
        count_deleted = 0
        for msg in messages:
            try:
                message_id = msg['message_id']
                try:
                    self.client.delete_messages(object_guid, [message_id])
                    count_deleted += 1
                    self.logger.info(f"Deleted message count: {count_deleted} - Message deleted")
                except Exception as e:
                    self.logger.error(f"Failed to delete message: {e}")
                    count_failed += 1
            except KeyError:
                count_no_id += 1
        self.logger.info(f"Number of messages without an ID: {count_no_id}")
        self.logger.info(f"Number of messages failed to delete: {count_failed}")

    def get_channel_info(self, object_guid):
        info = self.client.get_chat_info(object_guid)
        all_messages = list(self.get_all_messages(object_guid))
        if len(all_messages) == 0:
            self.logger.error("There are no messages in the channel or group.")
            return False
        if 'channel' in info:
            channel = info['channel']
            for key in ['channel_title', 'username', 'count_members', 'channel_type']:
                if key in channel:
                    self.logger.info(f"{key}: {channel[key]}")
            self.logger.info(f"All Messages: {'+1000' if len(all_messages) == 1000 else len(all_messages)}")
        elif 'group' in info:
            group = info['group']
            for key in ['group_title', 'count_members', 'chat_history_for_new_members']:
                if key in group:
                    self.logger.info(f"{key}: {group[key]}")
            self.logger.info(f"All Messages: {'+1000' if len(all_messages) == 1000 else len(all_messages)}")
        return True


def main():
    session = 'mySelf'
    #اینجا تو بخش object_guid گویید گپ یا چنل مورد نظر رو بزنید
    object_guid = 'guid'
    #اینجا تو بخش limit تعداد پیام هایی که میخواید پاک شه رو بزنید، اگه میخواید کل پیام ها(۱۰۰۰ پیام) پاک شه، کلمه all رو داخلش بزارید
    limit = '3'

    client = Client(session=session)
    message_manager = MessageManager(client)
    if not message_manager.get_channel_info(object_guid):
        return
    all_messages = list(message_manager.get_all_messages(object_guid))
    if limit.lower() == 'all':
        message_manager.delete_messages(object_guid, all_messages)
    else:
        limit = int(limit)
        if limit > len(all_messages):
            message_manager.logger.error("The number of messages you want to delete is greater than the total number of messages in the channel or group.")
        else:
            message_manager.delete_messages(object_guid, all_messages[:limit])


if __name__ == "__main__":
    main()
