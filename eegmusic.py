from spotifyclient import SpotifyClient
import pyfirmata
import json
from threading import Thread
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib as mpl
import datetime
import time
import os
import personaldata as perD

# check arduino connection
try:
    board = pyfirmata.Arduino(perD.port)
    it = pyfirmata.util.Iterator(board)
    it.start()
    analog_input = board.get_pin('a:0:i')
except:
    print('ARDUINO NOT FOUND')
    raise

##############################################################
music_name_for_graph = 'LOADING...'
progress_for_graph = 0
duration_for_graph = 0
analog_count = 1
brain_value = 1


def main():

    spotify_client = SpotifyClient()
    spotify_client.get_encoded_token()

    analog_sum = 0
    current_track_id = None
    while True:
        if not plt.fignum_exists(1): # quit if figure window not exists
            os._exit(1)
        if not spotify_client.token_checker():
            # get currently playing track id and dump to disk when finished
            analog_value = (analog_input.read())
            current_play = spotify_client.get_currently_playing_track()
            global music_name_for_graph
            music_name_for_graph = f"{current_play['track']['track_name']} - {current_play['track']['artists']}"
            global progress_for_graph
            progress_for_graph = current_play['track']['progress_time']
            global duration_for_graph
            duration_for_graph = current_play['track']['duration']
            if current_play['track']['is_playing'] is True:
                if analog_value is not None:
                    analog_sum += analog_value
                    global analog_count
                    analog_count += 1
                global brain_value
                brain_value = (analog_sum / analog_count)
            if current_play['track']['id'] != current_track_id or int(current_play['track']['progress_time'] / 1000) <= 1:
                analog_sum = 0
                brain_value = 0
                analog_count = 0
                current_track_id = current_play['track']['id']

            if (int(current_play['track']['duration'] / 1000)) - 2 == (int(current_play['track']['progress_time'] / 1000)):
                current_play['track']['brain_value'] = "{:.2f}".format(brain_value)

                datas = json.load(open('eegdata.json'))

                id_list = [d['track']['id'] for d in datas]
                if current_play['track']['id'] in id_list:
                    index_id = next(item for item in datas if item['track']['id'] == current_play['track']['id'])
                    old_brain_value = (index_id['track']['brain_value'])
                    new_brain_value = "{:.2f}".format(brain_value)
                    avg_brain_value = (float(old_brain_value) + float(new_brain_value)) / 2
                    index_id['track']['brain_value'] = "{:.2f}".format(avg_brain_value)
                    with open('eegdata.json', 'w') as h:
                        json.dump(datas, h, indent=4)
                else:
                    if isinstance(datas, dict):
                        #if type(datas) is dict:
                        datas = [datas]
                    datas.append(current_play)
                    with open('eegdata.json', 'w') as h:
                        json.dump(datas, h, indent=4)

                # sort and find top5 then add to playlist
                datas = json.load(open('eegdata.json'))
                if type(datas) is dict:
                    datas = [datas]
                datasSorted = sorted(datas, key=lambda k: k['track']['brain_value'], reverse=True)
                sorted_track_ids = [d['track']['id'] for d in datasSorted]
                spotify_client.playlist_engine('N-Predict Playlist',
                                               'Automatically generated - based on realtime EEG values',
                                               sorted_track_ids)
                top_5_tracks = sorted_track_ids[:5]
                recommended_tracks = spotify_client.get_track_recommendations(top_5_tracks)
                spotify_client.playlist_engine('N-Predict Recommendations',
                                               'Automatically generated recommended tracks - based on Top5 of N-Predict playlist',
                                               recommended_tracks)
                analog_sum = 0
                brain_value = 0
                analog_count = 0
            time.sleep(1 - (time.time() % 1))
        else:
            print('token expired')  # get new one
            spotify_client.token_checker()

# Create graph ui
def grapher():

    boudrate = 9600
    interval = (1 / boudrate) * 1000

    # Parameters
    x_len = 5000         # Number of points to display
    y_range = [-0.2, 1.2]  # Range of Y values to display

    # Create figure for plotting
    mpl.use('TkAgg')
    mpl.rcParams['toolbar'] = 'None'
    fig = plt.figure(figsize=(8, 4))
    fig.canvas.set_window_title('MythB')
    # fig.canvas.manager.window.attributes('-topmost', False)
    ax = fig.add_subplot(111)
    xs = list(range(0, x_len))
    ys = [0] * x_len
    ax.set_ylim(y_range)

    # Create a blank line
    line, = ax.plot(xs, ys)
    # Create text.
    value_text = ax.text(0.02, 0.1, '', transform=ax.transAxes,va='bottom', ha='center', rotation='vertical')
    value_avg_text = ax.text(0.02, 0.9, '', transform=ax.transAxes, va='top', ha='center', rotation='vertical')
    progress_text = ax.text(0.01, 0.01, '', transform=ax.transAxes, ha='left')
    music_text = ax.text(0.5, 0.95, '', transform=ax.transAxes, ha='center')
    duration_text = ax.text(0.99, 0.01, '', transform=ax.transAxes, ha='right')

    def animate(i, ys):

        # Read data from analog input
        data = analog_input.read()

        # Add y to personalDatas.py
        ys.append(data)

        # Limit x and y lists to set number of items
        ys = ys[-x_len:]

        global music_name_for_graph
        global progress_for_graph
        global duration_for_graph
        global brain_value

        now_color = 'g' if data > 0.8 else 'y' if 0.8 > data > 0.6 else 'r'
        avg_color = 'g' if brain_value > 0.8 else 'y' if 0.8 > brain_value > 0.6 else 'r'
        # line_color = 'g' if data > 0.8 else 'y' if 0.8 > data > 0.6 else 'r'

        # Update line with new Y values
        # plt.gca().get_lines()[0].set_color(line_color)

        line.set_ydata(ys)
        value_text.set_text('NOW : ' + "{:.2f}".format(data))
        value_text.set_color(now_color)
        value_avg_text.set_text('AVG : ' + "{:.2f}".format(brain_value))
        value_avg_text.set_color(avg_color)
        progress_text.set_text('Progress : ' + (str(datetime.timedelta(seconds=progress_for_graph/1000))[2:-7]))
        music_text.set_text(music_name_for_graph)
        duration_text.set_text('Duration : ' + (str(datetime.timedelta(seconds=duration_for_graph/1000))[2:-7]))

        # (datetime.utcnow().strftime('%M:%S.%f')[:-7])

        return line, value_text, progress_text, music_text, duration_text, value_avg_text,

    # Plot labels
    plt.title('N-Predict EEG Graph', c='tab:blue', y=1.05)
    plt.ylabel('Pleasure (0 - 1)', c='m', size='large')
    # plt.xlabel('Time')

    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(
        fig, animate, fargs=(ys,), interval=interval, blit=True)
    plt.show()


if __name__ == "__main__":
    thread1 = Thread(target=grapher)
    thread2 = Thread(target=main)
    # thread1.deamon = True
    thread2.deamon = True
    thread1.start()
    thread2.start()
