import sys
    
def progress(count, total, status=''):
    """
    Progress bar for the terminal
    
    Parameters
    ----------
    count : int
        Current progress
    total : int
        Total progress
    status : str, optional
        Status message, by default ''
        
    """
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()