#!/usr/bin/env python3
# -*- coding: utf-8 -*
"""Simple generator of a tg_bot.service file."""
import os
import sys
import subprocess
from pathlib import Path


def main():
    """Application entry point."""
    # interact with user
    print('Enter tg_bot token: ', end='')
    tg_bot_token = input()
    print('Enter rpi-surveillance token: ', end='')
    rs_token = input()
    print('Enter rpi-surveillance channel id: ', end='')
    rs_channel_id = input()
    print('Generating...')

    # obtain home path
    home_dir = os.environ['HOME']
    print('Detected home path:', home_dir)

    # obtain repo path
    repo_dir = Path(sys.argv[0]).absolute().parent
    print('Detected repo path:', repo_dir)

    # obtain rpi-surveillance path
    p = subprocess.Popen(['which', 'rpi-surveillance'], stdout=subprocess.PIPE)
    out, _ = p.communicate()
    rs_path = out.decode('utf-8')[:-1]
    assert rs_path != '', 'rpi-surveillance not installed.'
    print('Detected rpi-surveillance path:', rs_path)

    # generate service file
    data = ('[Unit]\n'
            'Description=Telegram bot to manage this host.\n'
            'After=network.target\n\n'
            '[Service]\n'
            'Type=simple\n'
            'Restart=always\n'
            f'ExecStart=python3 {repo_dir}/tg_bot.py --bot-token {tg_bot_token}'
            f' --ngrok-path {home_dir}/bin/ngrok/ngrok --ws-path {repo_dir}/web'
            f'_stream.py --rs-path {rs_path} --rs-token {rs_token} --rs-channel'
            f'-id {rs_channel_id} --log-path {home_dir}/bin/ngrok/log.txt\n\n'
            '[Install]\n'
            'WantedBy=multi-user.target\n')
    
    tg_service_path = repo_dir.joinpath('tg_bot.service')
    with open(tg_service_path, 'w') as f:
        print(data, file=f)
    
    print('File successfully created at path:', tg_service_path)


if __name__ == "__main__":
    main()
