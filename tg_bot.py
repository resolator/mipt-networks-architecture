#!/usr/bin/env python3
# -*- coding: utf-8 -*
"""Telegram bot to work with Raspberry Pi."""
import time
import telegram
import argparse
import subprocess

from pathlib import Path
from telegram.ext import Updater, CommandHandler


def get_args():
    """Arguments parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bot-token', required=True,
                        help='Telegram bot token.')
    parser.add_argument('--ngrok-path', type=Path, required=True,
                        help='Path to ngrok file.')
    parser.add_argument('--ws-path', type=Path, required=True,
                        help='Path to the web stream script.')
    parser.add_argument('--rs-path', type=Path,
                        default=Path('/usr/bin/rpi-surveillance'),
                        help='Path to the rpi-surveillance script.')
    parser.add_argument('--rs-token', required=True,
                        help='Token for a telegram bot for rpi-surveillance.')
    parser.add_argument('--rs-channel-id', required=True,
                        help='Telegram channel ID for rpi-surveillance.'
                             'If you don\'t have it please, send a message to '
                             'your channel and run '
                             '/usr/lib/rpi-surveillance/get_channel_id '
                             'with your token for rpi-surveillance.')
    parser.add_argument('--log-path', type=Path, required=True,
                        help='Path to log file of ngrok.')

    return parser.parse_args()


class Communicator:
    def __init__(self,
                 ngrok_path,
                 ws_path,
                 rs_path,
                 rs_token,
                 rs_channel_id,
                 log_path,
                 user_id=335805223):
        self._user_id = user_id
        self._log_path = log_path
        self._ws_path = ws_path

        self._ngrok_path = ngrok_path
                      
        self._rs_path = rs_path
        self._rs_channel_id = rs_channel_id
        self._rs_token = rs_token

    @staticmethod
    def send_no_access_msg(context, update):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Sorry, you don\'t have access to this bot.'
        )
    
    def app_manager(self,
                    update,
                    context,
                    app_name,
                    p_attr_name,
                    launch_cmd,
                    clean_log=False):
        # check user
        if update.effective_user.id != self._user_id:
            Communicator.send_no_access_msg(context, update)
            return

        # check args
        possible_args = ['start', 'stop', 'status']
        wrong_arg_msg = f'Pass one of the following arguments: {possible_args}'
        try:
            cmd = context.args[0]
        except IndexError:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=wrong_arg_msg
            )
            return

        if cmd not in possible_args:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=wrong_arg_msg
            )
            return
        
        # process cmd
        if cmd == 'start':
            if getattr(self, p_attr_name, None) is None:
                # clean log file
                if clean_log:
                    open(self._log_path, 'w').close()

                # launch app
                p = subprocess.Popen(launch_cmd, stdout=subprocess.DEVNULL)
                time.sleep(4)
                if p.poll() is not None:
                    msg = f'{app_name} launching failed. Most probably you '\
                          f'trying to start "ws" and "rs" at the same time.'
                    p.terminate()
                    p.wait()
                else:
                    setattr(self, p_attr_name, p)
                    msg=f'{app_name} has been launched.'
            else:
                msg=f'{app_name} already launched.'
        elif cmd == 'stop':
            if getattr(self, p_attr_name, None) is None:
                msg=f'{app_name} is not running.'
            else:
                # stop app
                getattr(self, p_attr_name).terminate()
                getattr(self, p_attr_name).wait()
                setattr(self, p_attr_name, None)
                
                msg = f'{app_name} stopped successfully.'
        else:  # status
            if getattr(self, p_attr_name, None) is None:
                msg = f'{app_name} is not running.'
            else:
                msg = f'{app_name} is running.'
        
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=msg)

    def start_cmd(self, update, context):
        if update.effective_user.id != self._user_id:
            Communicator.send_no_access_msg(context, update)
            return

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Welcome, ' + update.effective_user.username
        )

    def get_log_cmd(self, update, context):
        if update.effective_user.id != self._user_id:
            Communicator.send_no_access_msg(context, update)
            return
    
        try:
            n_lines = abs(int(context.args[0]))
        except ValueError:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Can\'t convert the first argument to an integer. '
                     'Type the number of last lines to print here.'
            )
            return
        except IndexError:
            n_lines = 9  # setup default number of lines
        
        with open(self._log_path, 'r') as f:
            logs = f.readlines()
        logs = ''.join(logs[-n_lines:])

        try:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'*Last {n_lines} records of log:*\n{logs}',
                parse_mode=telegram.ParseMode.MARKDOWN
            )
        except telegram.error.BadRequest:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='There are too much logs, select fewer rows to show.'
            )

    def ngrok_cmd(self, update, context):
        self.app_manager(update, context, 'Ngrok', 'ngrok_p',
                         [self._ngrok_path, 'start', '--all', '--log',
                          self._log_path], True)

    def ws_cmd(self, update, context):
        self.app_manager(update, context, 'Web stream', 'ws_p',
                         [self._ws_path, '--rotation', '180', '--fps', '25'])

    def rs_cmd(self, update, context):
        self.app_manager(update, context, 'rpi-surveillance', 'rs_p',
                         [self._rs_path, '--token', self._rs_token,
                          '--channel-id', self._rs_channel_id, '--rotation',
                          '180'])

    def reboot_cmd(self, update, context):
        if update.effective_user.id != self._user_id:
            Communicator.send_no_access_msg(context, update)
            return

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Rebooting...'
        )
        subprocess.run(['sudo', 'reboot'])

    def help_cmd(self, update, context):
        if update.effective_user.id != self._user_id:
            Communicator.send_no_access_msg(context, update)
            return
    
        text = 'Available commands:\n'\
                '/help - show this message\n'\
                '/start - check the access\n'\
                '/get_log [N] - get ngrok logs (last N lines)\n'\
                '/ngrok - ngrok commands (start, stop, status)\n'\
                '/ws - web stream commands (start, stop, status)\n'\
                '/rs - rpi-surveillance commands (start, stop, status)\n'\
                '/reboot - reboot the host\n'
        
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text
        )


def main():
    """Application entry point."""
    args = get_args()

    # connect to telegram bot
    updater = Updater(token=args.bot_token)

    comm = Communicator(args.ngrok_path,
                        args.ws_path,
                        args.rs_path,
                        args.rs_token,
                        args.rs_channel_id,
                        args.log_path)
    handlers = []
    
    handlers.append(CommandHandler('help', comm.help_cmd))
    handlers.append(CommandHandler('start', comm.start_cmd))
    handlers.append(CommandHandler('get_log', comm.get_log_cmd))   
    handlers.append(CommandHandler('ngrok', comm.ngrok_cmd))
    handlers.append(CommandHandler('ws', comm.ws_cmd))
    handlers.append(CommandHandler('rs', comm.rs_cmd))
    handlers.append(CommandHandler('reboot', comm.reboot_cmd))    
    
    [updater.dispatcher.add_handler(x) for x in handlers]

    while True:
        try:
            updater.start_polling(timeout=120)
        except Exception:
            time.sleep(120)
            updater.start_polling(timeout=120)


if __name__ == '__main__':
    main()
