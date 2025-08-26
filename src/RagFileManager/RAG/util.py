from functools import wraps

def safety(func):
    """
    defining a saftey wraper for any function
    """
    @wraps(func)
    def wrapper(*args,**kwargs):
        try:
            res = func(*args,**kwargs)
        except Exception as e:
            print(e)
            return False
        else:
            return True,res
    return wrapper