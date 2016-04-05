import utils

torrents_source = utils.scan_folder
torrents_source_args = ('/home/rain87/.local/share/data/qBittorrent/BT_backup',)

keeped_forums = (1, 2, 3)
keeper_user_id = '123445'
keeper_api_key = 'some-weird-api-key'

report_split_by=500

execfile('/home/rain87/rutracker_keeper.py')

