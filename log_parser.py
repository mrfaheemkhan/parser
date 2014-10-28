'''
Created on 26-Oct-2014

@author: admin-mbp03
'''
from _collections import defaultdict
import re
import sys


URL_INFO = [{'method': 'GET',
            'url': '/api/users/{user_id}/count_pending_messages'
            },
            
            {'method': 'GET',
            'url': '/api/users/{user_id}/get_messages'
            },
            
            {'method': 'GET',
            'url': '/api/users/{user_id}/get_friends_progress'
            },
            
            {'method': 'GET',
            'url': '/api/users/{user_id}/get_friends_score'
            },
            
            {'method': 'GET',
            'url': '/api/users/{user_id}'
            },
            
            {'method': 'POST',
            'url': '/api/users/{user_id}'
            }]


def _update_dict_for_urls():
    
    '''
    Update the URL_INFO dict with additional keys and default values
    to store and calculate stats
    '''
    for url_info in URL_INFO:
        
        
        url = url_info['url']
        regex_pattern = url.replace('{user_id}', '[0-9]*')
        regex = re.compile(regex_pattern)
        # add the regex in dict for later use
        url_info['regex'] = regex
        url_info['dynos'] = defaultdict(lambda: 0)
        url_info['mode'] = defaultdict(lambda: 0)
        
        for stat_keys in ['min_resp_time', 'max_resp_time', 'total_calls', 'median', 'resp_sum']:
            url_info[stat_keys] = 0
            
        url_info['resp_time'] = []


def get_stats_for_file(file_path):
    _update_dict_for_urls()
    log_file = open(file_path)   
    
    for line in log_file:
        for url_info in URL_INFO:
            if url_info['regex'].search(line) is not None:
                split_log = line.split(' ')
                
                if split_log[3].split('=')[1] != url_info['method']:
                    continue
                
                #update dyno count
                dyno_name = split_log[7].split('=')[1]
                url_info['dynos'][dyno_name] += 1
                
                # resp_time
                # split_log[8] is connect time   connect_time=19ms
                # split_log[9] is service time   service_time=20ms
                resp_time = int(split_log[8].split('=')[1].split('ms')[0]) + int(split_log[9].split('=')[1].split('ms')[0])
                
                url_info['resp_time'].append(resp_time)
                url_info['resp_sum'] += resp_time
                url_info['mode'][resp_time] += 1

                if url_info['max_resp_time'] < resp_time:
                    url_info['max_resp_time'] = resp_time
                
                elif url_info['min_resp_time'] > resp_time:
                    url_info['min_resp_time'] = resp_time

                url_info['total_calls'] += 1
                break
                
def display_url_stats():
    
    print '\n'
    for url_stats in URL_INFO:
        
        print 'URL:', url_stats['method'] + ' ' + url_stats['url']
        print 'Total Calls:', url_stats['total_calls']
        
        
        # calculate mean
        if url_stats['total_calls'] > 0:
            mean = int(url_stats['resp_sum'] / url_stats['total_calls'])
        else:
            mean = 0
             
        print 'Mean:', mean
        
        
        # calculate median
        url_stats['resp_time'].sort()
        
        if len(url_stats['resp_time']) > 0:
            # we take the lower index in case of even
            median_index = int(len(url_stats['resp_time']) / 2)
            median = url_stats['resp_time'][median_index]
        else:
            median = 0
            
        print 'Median:', median
        
        # calculate mode
        # max responding dyno
        mode = None
        max_count = 0
        for mode_time, count in url_stats['mode'].items():
            if mode is None:
                mode = mode_time
                max_count = count
            elif count > max_count:
                mode = mode_time
                max_count = count
        print 'Mode:',  mode
        
        
        # max responding dyno
        max_dyno = None
        max_calls = 0
        for dyno_name, calls in url_stats['dynos'].items():
            if max_dyno is None:
                max_dyno = dyno_name
                max_calls = calls
            elif calls > max_calls:
                max_dyno = dyno_name
                max_calls = calls
                  
        print 'Max Responding dyno: ', max_dyno
        print '\n'
    
    
if __name__=='__main__':
    if len(sys.argv) < 2:
        print 'usage: python '+sys.argv[0]+' /path/to/log/file'
        sys.exit()
    
    file_path = sys.argv[1]
    get_stats_for_file(file_path)
    display_url_stats()
