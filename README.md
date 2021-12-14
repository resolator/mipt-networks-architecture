# mipt-networks-architecture
Repo with homework for MIPT "Architecture of computer networks" course.

## App description

The app allows you to use your Raspberry Pi as a surveillance system with the 
following features:
- Web streaming from the camera.
- Motion detection with notifications to the telegram channel.
- Ngrok tunnel manager to get access to your Raspberry from the outside.

## App architecture

This application consist of the following components:
- A telegram bot to control the host Raspberry Pi [Alexander Rezanov].
- A web stream server with stream from the camera [Nikita Chestnov].
- A [surveillance system](https://github.com/resolator/rpi-surveillance) with telegram notifications [Vladyslav Dusiak].

## Installation

1. Install the surveillance system (with a telegram part) from [this](https://github.com/resolator/rpi-surveillance) repo.
2. Download ngrok from their [webiste](https://ngrok.com) and get a token for your ngrok instance.
3. Create a `~/bin/ngrok` directory and place downloaded ngrok there.
4. Move the `ngrok auth file` to `.ngrok2` directory. Insert your ngrok auth key to this file.
5. Move `tg_bot.service` to `/etc/systemd/system/`.
6. Execute `sudo systemctl enable tg_bot` and `sudo systemctl start tg_bot`.
7. Done. Now you can use the app.

## Usage
Here the list of available bot commands (this list can be obtained by sending `/help` command to the bot):
```
/help - show this message
/start - check the access
/get_log [N] - get ngrok logs (last N lines)
/ngrok - ngrok commands (start, stop, status)
/ws - web stream commands (start, stop, status)
/rs - rpi-surveillance commands (start, stop, status)
/reboot - reboot the host
```
Unfortunately you can't start the web steream and the surveillance system at the same time, because both of them captures the camera on your Raspberry but the camera can be captured by only one app. 

After you started ngrok URLs can be obtained from the ngrok's logs by the `/get_log` command. This log will be cleaned at every `/ngrok start` command.
